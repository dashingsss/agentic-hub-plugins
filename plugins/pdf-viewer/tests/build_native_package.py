"""Build the flat WorkSwarm native test package and verify it.

The native test package is the artifact a user imports into the WorkSwarm UI, so
manifest.json must sit at the archive root. This is deliberately different from the
marketplace wrapper produced by tools/asset_release.py pack.

Usage:
    python tests/build_native_package.py
"""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import shutil
import stat
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / "pdf-viewer"
OUT_DIR = ROOT / "test-packages"
ASSET = json.loads((ROOT / "asset.json").read_text(encoding="utf-8"))
SLUG, VERSION = ASSET["name"], ASSET["version"]
OUT = OUT_DIR / f"{SLUG}-{VERSION}-native.zip"

# Files that must not leak into a user-facing archive.
FORBIDDEN_PARTS = {"__pycache__", "node_modules", "tests", ".git", "venv"}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    members: dict[str, bytes] = {}
    for path in sorted(PAYLOAD.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(PAYLOAD)
        if any(part in FORBIDDEN_PARTS or part.startswith(".") for part in rel.parts):
            raise SystemExit(f"refusing to package development file: {rel}")
        members[rel.as_posix()] = path.read_bytes()

    required = {"manifest.json", "README.md", "THIRD_PARTY_NOTICES.md"}
    missing = required - members.keys()
    if missing:
        raise SystemExit(f"payload missing required root files: {sorted(missing)}")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, members[name])
    body = buffer.getvalue()
    if OUT.exists():
        if OUT.read_bytes() != body:
            raise SystemExit(f"refusing to overwrite a different existing version: {OUT}; increment the version first")
    else:
        with OUT.open("xb") as output:
            output.write(body)
    return OUT


def verify(archive_path: pathlib.Path) -> dict:
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if "manifest.json" not in names:
            raise SystemExit("manifest.json is not at the archive root")
        if any(n.endswith("plugin.yaml") for n in names):
            raise SystemExit("marketplace plugin.yaml must not be in the native package")

        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        if manifest.get("id") != SLUG or manifest.get("version") != VERSION:
            raise SystemExit(f"manifest identity/version mismatch: {manifest.get('id')} {manifest.get('version')}")

        provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))
        licence_report = []
        evidence = list(provenance.get("license_reference_files", []))
        for source in provenance["sources"]:
            evidence.extend(source.get("license_evidence", []))
        for item in evidence:
            body = archive.read(item["path"])
            digest = hashlib.sha256(body).hexdigest()
            if digest != item["sha256"]:
                raise SystemExit(f"licence hash mismatch inside ZIP: {item['path']}")
            licence_report.append({"path": item["path"], "sha256": digest, "ok": True})

        declared = []
        for entry in manifest.get("skills", []):
            declared.append(f"{entry['dir']}/SKILL.md")
        for entry in manifest.get("mcps", []):
            declared.append(entry["file"])
        for entry in manifest.get("tools", []):
            declared.append(entry["file"])
        declared.extend(["runtime/pdf_review.py", "requirements.txt"])
        if manifest.get("mcps") or len(manifest.get("tools", [])) != 1:
            raise SystemExit("1.1.0 requires one native tool and no MCP service")
        missing = [d for d in declared if d not in names]
        if missing:
            raise SystemExit(f"declared files absent from ZIP: {missing}")

    return {
        "members": sorted(names),
        "licenses": licence_report,
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "bytes": archive_path.stat().st_size,
    }


def retest_extracted(archive_path: pathlib.Path) -> int:
    """Run the functional tests against the extracted payload only."""
    workdir = pathlib.Path(tempfile.mkdtemp(prefix="pdf-viewer-native-extract-"))
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(workdir)
    env_note = f"extracted payload: {workdir}"
    print(env_note)
    import os
    import subprocess

    env = dict(os.environ, PDF_VIEWER_PAYLOAD=str(workdir))
    try:
        proc = subprocess.run([sys.executable, str(ROOT / "tests" / "test_functional.py")], env=env)
        if proc.returncode:
            return proc.returncode
        if os.environ.get("PDF_REVIEW_HOST_SDK"):
            env["PYTHONPATH"] = os.environ["PDF_REVIEW_HOST_SDK"]
            host = subprocess.run([sys.executable, str(ROOT / "tests" / "host_checks.py"), "--payload", str(workdir), "--report", str(OUT_DIR / f"host-{VERSION}.json")], env=env)
            return host.returncode
        return 0
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    path = build()
    report = verify(path)
    (OUT_DIR / f"verification-{VERSION}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    code = retest_extracted(path)
    print("extracted-payload functional tests:", "PASS" if code == 0 else "FAIL")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
