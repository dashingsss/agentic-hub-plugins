"""Copy unmodified installed-distribution license texts as reference evidence.

No library implementation/binary/font is copied. Dependency installation remains
separate. Run only in the recorded build environment before rebuilding a version.
"""
import hashlib
from importlib import metadata
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "pdf-viewer"
for package, directory in [("pypdf", "pypdf"), ("reportlab", "reportlab"), ("Pillow", "pillow"), ("pypdfium2", "pypdfium2")]:
    distribution = metadata.distribution(package)
    licenses = Path(distribution._path) / "licenses"
    target = PAYLOAD / "licenses" / directory
    shutil.copytree(licenses, target, dirs_exist_ok=True)
provenance_path = ROOT / "provenance.json"
provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
provenance["license_reference_files"] = [
    {"path": p.relative_to(PAYLOAD).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in sorted((PAYLOAD / "licenses").rglob("*")) if p.is_file()
]
provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Verified reference license files:", len(provenance["license_reference_files"]))
