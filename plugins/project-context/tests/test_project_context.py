import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
PAYLOAD = Path(os.environ.get("PROJECT_CONTEXT_PAYLOAD") or Path(__file__).resolve().parents[1] / "project-context")
sys.path.insert(0, str(PAYLOAD / "runtime"))
from engine import ContextError, Engine, MAX_FILE, directory_fd, safe_bytes
from server import call


def pin_in_process(cache, workspace_id, path):
    Engine(cache).control(workspace_id, "pin", path)


class ProjectContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="project-context-test-")
        self.base = Path(self.temporary.name)
        self.cache = self.base / "state"
        self.runtime = Engine(self.cache)
        self.demo = self.runtime.demo()
        self.identifier = self.demo["workspace_id"]
        self.root = Path(self.demo["root"])

    def tearDown(self):
        self.temporary.cleanup()

    def paths(self, result):
        return [item["rel"] for group in ("primary", "supporting", "related") for item in result["pack"][group]]

    def test_demo_is_new_and_synthetic(self):
        second = self.runtime.demo()
        self.assertNotEqual(second["root"], self.demo["root"])
        self.assertIn("虚构", (self.root / "README.md").read_text())
        self.assertEqual(self.demo["scan"]["indexed_count"], 6)

    def test_chinese_task_rank_and_grounding(self):
        result = self.runtime.find(self.identifier, "登录设计 tokenlogin 离线缓存")
        primary = result["pack"]["primary"][0]
        self.assertEqual(primary["rel"], "docs/login-design.md")
        self.assertIn("七天", primary["passages"][0]["snippet"])
        self.assertEqual(primary["sha256"], hashlib.sha256((self.root / primary["rel"]).read_bytes()).hexdigest())
        self.assertTrue(any(relation["other"] == "README.md" and relation["line"] == 4 for relation in primary["relations"]))
        self.assertIn("主要资料", result["markdown"])

    def test_no_hit_does_not_fill_groups(self):
        result = self.runtime.find(self.identifier, "zqxvnonexistent999")
        self.assertEqual(self.paths(result), [])
        self.assertEqual(result["pack"]["totals"]["matched"], 0)

    def test_passage_line_span_matches_source(self):
        result = self.runtime.find(self.identifier, "登录设计 tokenlogin")
        for group in ("primary", "supporting", "related"):
            for item in result["pack"][group]:
                body = (self.root / item["rel"]).read_text()
                for passage in item["passages"]:
                    self.assertEqual(body[passage["startOffset"]:passage["endOffset"]].count("\n") + 1, passage["endLine"] - passage["startLine"] + 1)
                    self.assertTrue(any(term in body.lower() for term in passage["terms"]))

    def test_scan_does_not_mark_read(self):
        self.runtime.find(self.identifier, "登录设计")
        self.assertEqual(self.runtime.status(self.identifier)["reads"], [])

    def test_read_tracks_only_returned_range(self):
        result = self.runtime.read(self.identifier, "docs/login-design.md", 3, 2)
        self.assertTrue(result["content"].startswith("3: "))
        self.assertEqual(result["end_line"], 4)
        record = self.runtime.status(self.identifier)["reads"][0]
        self.assertEqual(record["start_line"], 3)
        self.assertIn("未变化", record["status"])

    def test_content_change_even_if_mtime_same(self):
        document = self.root / "docs/login-design.md"
        self.runtime.read(self.identifier, "docs/login-design.md")
        previous = document.stat()
        document.write_text(document.read_text().replace("七天", "五天"))
        os.utime(document, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        self.assertIn("已变化", self.runtime.status(self.identifier)["reads"][0]["status"])
        self.runtime.read(self.identifier, "docs/login-design.md")
        self.assertIn("未变化", self.runtime.status(self.identifier)["reads"][0]["status"])

    def test_expected_hash_rejects_and_preserves_record(self):
        self.runtime.read(self.identifier, "docs/login-design.md")
        before = self.runtime.status(self.identifier)["reads"]
        with self.assertRaisesRegex(ContextError, "预期指纹"):
            self.runtime.read(self.identifier, "docs/login-design.md", expected_sha256="0" * 64)
        self.assertEqual(before, self.runtime.status(self.identifier)["reads"])

    def test_pins_separate_from_relevance_and_persist(self):
        self.runtime.control(self.identifier, "pin", "docs/garden.md")
        result = Engine(self.cache).find(self.identifier, "登录设计 tokenlogin")
        self.assertEqual(result["pinned"][0]["rel"], "docs/garden.md")
        self.assertNotIn("docs/garden.md", self.paths(result))

    def test_exclude_before_rank_count_relations_and_pin(self):
        self.runtime.control(self.identifier, "pin", "docs/login-old.md")
        self.runtime.control(self.identifier, "exclude", "docs/login-old.md")
        result = self.runtime.find(self.identifier, "登录设计 tokenlogin")
        self.assertNotIn("docs/login-old.md", self.paths(result))
        self.assertTrue(all(relation["other"] != "docs/login-old.md" for group in ("primary", "supporting", "related") for item in result["pack"][group] for relation in item.get("relations", [])))
        self.assertEqual(result["scan"]["indexed_count"], 5)
        self.assertEqual(result["pinned"], [])
        with self.assertRaisesRegex(ContextError, "不在本轮"):
            self.runtime.read(self.identifier, "docs/login-old.md")
        self.runtime.control(self.identifier, "restore", "docs/login-old.md")
        self.assertEqual(self.runtime.find(self.identifier, "登录设计")["scan"]["indexed_count"], 6)

    def test_unpin_and_idempotent_pin(self):
        for unused in range(2):
            self.runtime.control(self.identifier, "pin", "README.md")
        self.assertEqual(self.runtime.status(self.identifier)["pins"], ["README.md"])
        self.runtime.control(self.identifier, "unpin", "README.md")
        self.assertEqual(self.runtime.status(self.identifier)["pins"], [])

    def test_traversal_and_absolute_paths_rejected(self):
        for path in ("../outside.md", "/etc/passwd", "docs/../README.md", "docs\\login-design.md", "README.md\x00", "docs//file.md"):
            with self.subTest(path=path), self.assertRaises(ContextError):
                self.runtime.read(self.identifier, path)

    def test_hidden_secret_generated_and_binary_are_unavailable(self):
        for name in (".env", "secrets.json", "credentials.json", "bundle.min.js", "package-lock.json", "id_rsa"):
            (self.root / name).write_text("zqxvprivateonly999")
        (self.root / "binary.txt").write_bytes(b"zqxvprivateonly999\x00")
        (self.root / "image.png").write_text("zqxvprivateonly999")
        result = self.runtime.find(self.identifier, "zqxvprivateonly999")
        self.assertEqual(self.paths(result), [])
        self.assertEqual(result["scan"]["indexed_count"], 6)
        for action in ("pin", "restore"):
            with self.assertRaisesRegex(ContextError, "保护规则"):
                self.runtime.control(self.identifier, action, "secrets.json")

    def test_root_and_nested_gitignore(self):
        (self.root / ".gitignore").write_text("*.tmp.md\n!keep.tmp.md\nprivate/\n")
        (self.root / "hidden.tmp.md").write_text("uniquebait555")
        (self.root / "keep.tmp.md").write_text("keepbait777")
        (self.root / "private").mkdir()
        (self.root / "private/private.md").write_text("uniquebait555")
        (self.root / "docs/.gitignore").write_text("/blocked.md\n")
        (self.root / "docs/blocked.md").write_text("uniquebait555")
        self.assertEqual(self.paths(self.runtime.find(self.identifier, "uniquebait555")), [])
        self.assertIn("keep.tmp.md", self.paths(self.runtime.find(self.identifier, "keepbait777")))
        with self.assertRaises(ContextError):
            self.runtime.read(self.identifier, "docs/blocked.md")

    def test_unsupported_ignore_fails_closed(self):
        (self.root / ".gitignore").write_text("[ab]*\n")
        with self.assertRaisesRegex(ContextError, "不支持"):
            self.runtime.find(self.identifier, "登录设计")

    def test_symbolic_file_and_directory_and_hardlink_blocked(self):
        outside = self.base / "outside.md"
        outside.write_text("symlinkbait999")
        (self.root / "linked.md").symlink_to(outside)
        (self.root / "external").symlink_to(self.base, target_is_directory=True)
        os.link(outside, self.root / "hard.md")
        self.assertEqual(self.paths(self.runtime.find(self.identifier, "symlinkbait999")), [])
        for path in ("linked.md", "external/outside.md", "hard.md"):
            with self.assertRaises(ContextError):
                self.runtime.read(self.identifier, path)

    def test_descriptor_read_rejects_symlink_parent(self):
        target = self.base / "target"
        target.mkdir()
        (target / "bait.md").write_text("private")
        (self.root / "alias").symlink_to(target, target_is_directory=True)
        with directory_fd(self.root) as root_fd:
            with self.assertRaises(OSError):
                safe_bytes(root_fd, ["alias", "bait.md"])

    def test_replaced_root_rejected(self):
        moved = self.root.with_name(self.root.name + "-moved")
        self.root.rename(moved)
        self.root.mkdir()
        with self.assertRaisesRegex(ContextError, "已被替换"):
            self.runtime.status(self.identifier)

    def test_file_limit_and_invalid_utf8_reported(self):
        (self.root / "large.md").write_bytes(b"a" * (MAX_FILE + 1))
        (self.root / "invalid.md").write_bytes(b"\xff\xfe")
        result = self.runtime.find(self.identifier, "登录设计")
        self.assertEqual(result["scan"]["indexed_count"], 6)
        self.assertTrue(result["scan"]["omissions"])

    def test_budget_reported(self):
        with patch("engine.MAX_FILES", 2):
            result = self.runtime.find(self.identifier, "登录设计")
        self.assertEqual(result["scan"]["indexed_count"], 2)
        self.assertFalse(result["scan"]["complete"])

    def test_missing_file_status_is_not_read_unchanged(self):
        self.runtime.read(self.identifier, "docs/garden.md")
        (self.root / "docs/garden.md").unlink()
        self.assertIn("不可用", self.runtime.status(self.identifier)["reads"][0]["status"])

    def test_restart_has_same_workspace_and_records(self):
        self.runtime.read(self.identifier, "README.md")
        status = Engine(self.cache).status(self.identifier)
        self.assertEqual(status["reads"][0]["path"], "README.md")
        self.assertEqual(Engine(self.cache).open(str(self.root))["workspace_id"], self.identifier)

    def test_concurrent_controls_do_not_lose_updates(self):
        processes = [multiprocessing.Process(target=pin_in_process, args=(self.cache, self.identifier, path)) for path in ("README.md", "docs/garden.md", "docs/login-design.md")]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(len(self.runtime.status(self.identifier)["pins"]), 3)

    def test_cache_corruption_preserved(self):
        state_file = self.cache / "state.json"
        state_file.write_text("{corrupted")
        with self.assertRaisesRegex(ContextError, "损坏"):
            self.runtime.status()
        self.assertEqual(state_file.read_text(), "{corrupted")

    def test_state_only_metadata_and_permissions(self):
        self.runtime.read(self.identifier, "docs/login-design.md")
        content = (self.cache / "state.json").read_text()
        self.assertNotIn("离线缓存保存七天", content)
        self.assertEqual(self.cache.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.cache / "state.json").stat().st_mode & 0o777, 0o600)

    def test_invalid_arguments_and_no_project_write(self):
        before = {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        for arguments in ({"workspace_id": self.identifier, "path": "README.md", "max_lines": True}, {"workspace_id": self.identifier, "path": "README.md", "max_lines": 121}, {"workspace_id": self.identifier, "path": "README.md", "extra": 1}):
            with self.assertRaises(ContextError):
                call(self.runtime, "context_read", arguments)
        with self.assertRaises(ContextError):
            self.runtime.find(self.identifier, " ")
        with self.assertRaises(ContextError):
            self.runtime.status("invented-id")
        self.runtime.find(self.identifier, "登录设计")
        self.runtime.read(self.identifier, "README.md")
        self.runtime.control(self.identifier, "pin", "README.md")
        self.assertEqual(before, {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_reject_global_and_plugin_roots(self):
        for root in ("/", str(Path.home()), str(PAYLOAD), "relative/path"):
            with self.assertRaises(ContextError):
                self.runtime.open(root)

    def test_ranking_failure_not_success(self):
        with patch("engine.subprocess.run", side_effect=subprocess.TimeoutExpired("node", 15)):
            with self.assertRaisesRegex(ContextError, "执行失败"):
                self.runtime.find(self.identifier, "登录设计")

    def test_missing_runtime_is_reported_without_install(self):
        with patch("engine.os.path.isfile", return_value=False), patch("engine.shutil.which", return_value=None):
            with self.assertRaisesRegex(ContextError, "未找到 Node"):
                Engine(self.base / "missing-node")

    def test_old_runtime_is_rejected(self):
        with patch("engine.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout="v18.0.0\n")):
            with self.assertRaisesRegex(ContextError, "版本过低"):
                Engine(self.base / "old-node")

    def test_pin_limit_and_read_line_errors(self):
        for path in ("README.md", "docs/login-design.md", "docs/login-old.md", "docs/garden.md", "src/login.py"):
            self.runtime.control(self.identifier, "pin", path)
        with self.assertRaisesRegex(ContextError, "最多固定"):
            self.runtime.control(self.identifier, "pin", "tests/test_login.py")
        with self.assertRaisesRegex(ContextError, "文件末尾"):
            self.runtime.read(self.identifier, "README.md", 999)
        self.assertEqual(self.runtime.status(self.identifier)["reads"], [])

    def test_state_symlink_not_followed(self):
        state_file = self.cache / "state.json"
        original = state_file.read_bytes()
        outside = self.base / "outside-state.json"
        outside.write_bytes(original)
        state_file.unlink()
        state_file.symlink_to(outside)
        with self.assertRaises(OSError):
            self.runtime.status()
        self.assertEqual(outside.read_bytes(), original)

    def test_demo_under_hidden_cache_root(self):
        hidden_cache = self.base / ".cache/project-context"
        demo = Engine(hidden_cache).demo()
        self.assertEqual(demo["scan"]["indexed_count"], 6)

    def test_directory_ignore_and_restore_do_not_override_protection(self):
        ignored = self.root / "node_modules"
        ignored.mkdir()
        (ignored / "library.js").write_text("privatepackage123")
        self.assertEqual(self.paths(self.runtime.find(self.identifier, "privatepackage123")), [])
        with self.assertRaisesRegex(ContextError, "保护规则"):
            self.runtime.control(self.identifier, "restore", "node_modules/library.js")

    def test_oversize_protocol_request_then_ping(self):
        ping = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"})
        result = subprocess.run([sys.executable, str(PAYLOAD / "runtime/server.py")], input="a" * 262145 + "\n" + ping + "\n", text=True, capture_output=True, check=True)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32600)
        self.assertEqual(responses[1]["result"], {})

    def test_protocol_errors_do_not_kill_server(self):
        messages = ["notjson", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}), json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})]
        result = subprocess.run([sys.executable, str(PAYLOAD / "runtime/server.py")], input="\n".join(messages) + "\n", text=True, capture_output=True, check=True)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[1]["result"]["serverInfo"]["version"], "1.0.0")
        self.assertEqual(len(responses[2]["result"]["tools"]), 6)
        self.assertEqual(result.stderr, "")

    def test_bundled_license_and_original_core_hashes(self):
        expected = {"relevance.js": "9dae39cd6d6d5336b887beb9a8c45b027c80969970350e9ebae93aad6259285f", "context.js": "f1b39bc872bb0bbff59544edc645eba39cd5c889ea9364984a23c355df1bf0a8", "classification.js": "bca1a991a1a3804ec4534488028474c72bf8163d1c0f132c1bf456fb09e1b559", "relations.js": "6b56ad603a0e230224e97d87c3c95ef4eeb7eb745caf3f53b8d24e247db26a9b", "links.js": "405d5b54d3d83b34c65361d8678b636f109f45db134ab7b58b7a9668393aa0bb", "passage.js": "fadd9e875f16d77ab3213d76a44e3d8692a7a2306f400e1dcc10ea622ed6ec4c"}
        for name, fingerprint in expected.items():
            self.assertEqual(hashlib.sha256((PAYLOAD / "vendor/dsh-knit" / name).read_bytes()).hexdigest(), fingerprint)
        license_text = (PAYLOAD / "licenses/dsh-knit/LICENSE").read_bytes()
        self.assertEqual(hashlib.sha256(license_text).hexdigest(), "8f0d3535cb8e31e61cf6ebf0d9d4f0aa9509659c3ff43d8d77e1f6c5f6972cbb")


if __name__ == "__main__":
    unittest.main(verbosity=2)
