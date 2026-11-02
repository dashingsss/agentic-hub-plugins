"""Exercise real PDFs, rendered previews, and the actual OpenJiuwen Tool class.

PDF_VIEWER_PAYLOAD selects an extracted ZIP. PDF_REVIEW_TEST_ARTIFACTS retains
the test workspace for visual inspection. No MCP/file-registration test shim.
"""
from __future__ import annotations
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = Path(os.environ.get("PDF_VIEWER_PAYLOAD", ROOT / "pdf-viewer"))
spec = importlib.util.spec_from_file_location("native_pdf_review", PAYLOAD / "runtime/pdf_review.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
from PIL import Image, ImageChops, ImageDraw
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, TextStringObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def make_fixtures(folder):
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(folder / "sample.pdf"), pagesize=(612, 792))
    for title, sentence in [("PDF 功能测试", "付款期限为收到发票后 30 天。"), ("第二页", "本页用于测试搜索、翻页和缩放。")]:
        c.setFont("STSong-Light", 24)
        c.drawString(72, 722, title)
        c.setFont("STSong-Light", 14)
        c.drawString(72, 680, sentence)
        c.setFont("Helvetica", 14)
        c.drawString(72, 650, "Payment is due within 30 days.")
        c.showPage()
    c.save()
    c = canvas.Canvas(str(folder / "test-form.pdf"), pagesize=(612, 792))
    c.setFont("STSong-Light", 23)
    c.drawString(72, 727, "表单与签名测试")
    c.setFont("STSong-Light", 14)
    for label, y in [("姓名", 660), ("邮箱", 600), ("确认", 540), ("签名图片", 220)]:
        c.drawString(72, y, label)
    for name, y in [("name", 650), ("email", 590)]:
        c.acroForm.textfield(name=name, x=120, y=y, width=350, height=26, forceBorder=True)
    c.acroForm.checkbox(name="approved", x=120, y=532, size=18, checked=False, forceBorder=True)
    c.setDash(3, 3)
    c.rect(120, 120, 350, 80)
    c.save()
    image = Image.new("RGBA", (400, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.line([(10, 70), (80, 20), (120, 70), (180, 15), (250, 70), (380, 30)], fill=(18, 45, 110), width=5)
    draw.text((145, 75), "TEST SIGNATURE", fill=(18, 45, 110))
    image.save(folder / "test-signature.png")
    for name in ["rotated", "cropped", "orphan", "ambiguous", "signed", "encrypted"]:
        w = PdfWriter()
        w.clone_document_from_reader(PdfReader(folder / ("test-form.pdf" if name in {"orphan", "ambiguous", "signed"} else "sample.pdf")))
        if name == "rotated":
            w.pages[0].rotate(90)
        elif name == "cropped":
            w.pages[0].cropbox.lower_left, w.pages[0].cropbox.upper_right = (30, 40), (580, 760)
        elif name == "orphan":
            w.root_object["/AcroForm"][NameObject("/Fields")] = ArrayObject()
        elif name == "ambiguous":
            original = w.root_object["/AcroForm"]["/Fields"][0].get_object()
            duplicate = DictionaryObject({k: v for k, v in original.items() if k not in {"/P", "/AP"}})
            w.root_object["/AcroForm"]["/Fields"][0] = w._add_object(duplicate)
        elif name == "signed":
            sig = DictionaryObject({NameObject("/FT"): NameObject("/Sig"), NameObject("/T"): TextStringObject("signed"), NameObject("/V"): w._add_object(DictionaryObject({NameObject("/Type"): NameObject("/Sig")}))})
            w.root_object["/AcroForm"]["/Fields"].append(w._add_object(sig))
        elif name == "encrypted":
            # ReportLab's binary /ID may be decoded as text when cloned. Let
            # pypdf generate its own identifiers for the encrypted fixture.
            w._ID = None
            w.encrypt("test-password")
        w.write(folder / (name + ".pdf"))
    (folder / "broken.pdf").write_bytes(b"This is not a PDF.")


class FunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="pdf-native-", dir=ROOT / "tests")
        cls.workspace = Path(cls.temp.name) / "中文工作目录"
        cls.workspace.mkdir()
        make_fixtures(cls.workspace)

    @classmethod
    def tearDownClass(cls):
        artifacts = os.environ.get("PDF_REVIEW_TEST_ARTIFACTS")
        if artifacts:
            dest = Path(artifacts)
            if dest.exists():
                dest = dest / ("run-" + Path(cls.temp.name).name)
            shutil.copytree(cls.workspace, dest)
            print("ARTIFACTS", dest)
        cls.temp.cleanup()

    def call(self, action, **payload):
        return engine.run({"workspace_dir": str(self.workspace), "action": action, "payload": payload})

    def success(self, result):
        self.assertTrue(result.get("ok"), result)
        return result

    def opened(self, name="sample.pdf"):
        return self.success(self.call("open", path=name))

    def plan(self, state, commands):
        return self.success(self.call("plan", review_id=state["review_id"], expected_revision=state["revision"], commands=commands))

    def apply(self, plan):
        return self.success(self.call("apply", review_id=plan["review_id"], expected_revision=plan["revision"], plan_id=plan["plan_id"], confirmed=True))

    def test_discover_open_search_zoom(self):
        listed = self.success(self.call("list_pdfs"))
        self.assertIn(str(self.workspace / "sample.pdf"), [f["path"] for f in listed["files"]])
        state = self.opened()
        self.assertEqual(len(state["pages"]), 2)
        hit = self.success(self.call("search", review_id=state["review_id"], query="付款期限为收到发票后 30 天。"))
        self.assertEqual(hit["matches"][0]["page"], 1)
        preview = self.success(self.call("preview", review_id=state["review_id"], pages=[2], scale=1.5))
        self.assertEqual(preview["previews"][0]["width"], 918)

    def test_annotations_edit_delete_save_and_original_preserved(self):
        original = engine.digest(self.workspace / "sample.pdf")
        state = self.opened()
        plan = self.plan(state, [{"action": "highlight_text", "page": 1, "text": "付款期限为收到发票后 30 天。"}, {"action": "add_annotations", "annotations": [{"id": "note-test", "type": "note", "page": 1, "x": 470, "y": 150, "content": "测试批注：请复核"}, {"id": "stamp-test", "type": "stamp", "page": 1, "x": 370, "y": 180, "width": 150, "height": 40, "content": "DRAFT"}]}])
        self.assertFalse(plan["applied"])
        self.assertEqual(self.success(self.call("preview", review_id=state["review_id"]))["revision"], 0)
        with Image.open(state["previews"][0]["path"]) as before, Image.open(plan["previews"][0]["path"]) as after:
            self.assertIsNotNone(ImageChops.difference(before.convert("RGB"), after.convert("RGB")).getbbox())
        changed = self.apply(plan)
        changed = self.apply(self.plan(changed, [{"action": "update_annotations", "annotations": [{"id": "note-test", "content": "测试批注：已复核"}]}, {"action": "remove_annotations", "ids": ["stamp-test"]}]))
        saved = self.success(self.call("save_as", review_id=changed["review_id"], expected_revision=2, path="sample-annotated.pdf"))
        reader = PdfReader(saved["path"])
        annotations = [a.get_object() for a in reader.pages[0]["/Annots"]]
        self.assertIn("/Highlight", [a["/Subtype"] for a in annotations])
        self.assertEqual(next(a for a in annotations if a.get("/NM") == "note-test")["/Contents"], "测试批注：已复核")
        self.assertNotIn("DRAFT", reader.pages[0].extract_text())
        self.assertEqual(engine.digest(self.workspace / "sample.pdf"), original)

    def test_chinese_form_checkbox_signature_reopen(self):
        original = engine.digest(self.workspace / "test-form.pdf")
        state = self.opened("test-form.pdf")
        self.assertEqual({f["name"] for f in state["form_fields"]}, {"name", "email", "approved"})
        plan = self.plan(state, [{"action": "fill_form", "fields": {"name": "测试用户", "email": "pdf-test@example.com", "approved": True}}, {"action": "add_annotations", "annotations": [{"id": "signature", "type": "image", "page": 1, "image_path": "test-signature.png", "x": 150, "y": 615, "width": 200}]}])
        changed = self.apply(plan)
        saved = self.success(self.call("save_as", review_id=changed["review_id"], expected_revision=1, path="test-form-completed.pdf"))
        reader = PdfReader(saved["path"])
        self.assertEqual(reader.get_fields()["name"]["/V"], "测试用户")
        self.assertEqual(reader.get_fields()["email"]["/V"], "pdf-test@example.com")
        self.assertEqual(reader.get_fields()["approved"]["/V"], "/Yes")
        for _, widget in engine.widgets(reader):
            self.assertEqual(str(engine.inherited(widget, "/V", "")), str(reader.get_fields()[engine.field_name(widget)].get("/V", "")))
            self.assertIsNotNone(widget.get("/AP", {}).get("/N"))
        self.assertTrue(any(o.get_object().get("/Subtype") == "/Image" for o in reader.pages[0]["/Resources"]["/XObject"].values()))
        self.assertEqual(engine.digest(self.workspace / "test-form.pdf"), original)

    def test_confirmation_and_stale_revision(self):
        state = self.opened()
        plan = self.plan(state, [{"action": "highlight_text", "text": "Payment is due"}])
        self.assertEqual(self.call("apply", review_id=state["review_id"], expected_revision=0, plan_id=plan["plan_id"])["error"]["code"], "CONFIRMATION_REQUIRED")
        self.apply(plan)
        self.assertEqual(self.call("apply", review_id=state["review_id"], expected_revision=0, plan_id=plan["plan_id"], confirmed=True)["error"]["code"], "STALE_REVISION")

    def test_access_bounds_and_no_overwrite(self):
        outside = self.workspace.parent / "outside.pdf"
        shutil.copyfile(self.workspace / "sample.pdf", outside)
        self.assertEqual(self.call("open", path="../outside.pdf")["error"]["code"], "PATH_OUTSIDE_WORKSPACE")
        state = self.opened()
        for path, code in [("sample.pdf", "OUTPUT_EXISTS"), ("test-form.pdf", "OUTPUT_EXISTS"), (".pdf-review/export.pdf", "PATH_OUTSIDE_WORKSPACE"), ("../outside-output.pdf", "PATH_OUTSIDE_WORKSPACE")]:
            self.assertEqual(self.call("save_as", review_id=state["review_id"], expected_revision=0, path=path)["error"]["code"], code)

    def test_invalid_inputs(self):
        state = self.opened()
        for command, code in [({"action": "fill_form", "fields": {"missing": "x"}}, "FIELD_NOT_FOUND"), ({"action": "highlight_text", "text": "not present anywhere"}, "TEXT_NOT_FOUND"), ({"action": "add_annotations", "annotations": [{"type": "note", "page": 1, "x": 999, "y": 10, "content": "越界"}]}, "BOUNDS"), ({"action": "navigate"}, "UNSUPPORTED_ACTION")]:
            result = self.call("plan", review_id=state["review_id"], expected_revision=0, commands=[command])
            self.assertEqual(result["error"]["code"], code, result)
        for name, code in [("broken.pdf", "INVALID_PDF"), ("encrypted.pdf", "ENCRYPTED_PDF")]:
            self.assertEqual(self.call("open", path=name)["error"]["code"], code)

    def test_rotated_and_cropped_pages(self):
        for name in ["rotated.pdf", "cropped.pdf"]:
            state = self.opened(name)
            self.assertTrue(self.success(self.call("search", review_id=state["review_id"], query="Payment is due", page=1))["matches"])
            self.assertTrue(self.plan(state, [{"action": "highlight_text", "text": "Payment is due", "page": 1}])["previews"])

    def test_orphan_and_ambiguous_forms(self):
        state = self.opened("orphan.pdf")
        self.assertTrue(state["recovered_orphan_fields"])
        self.apply(self.plan(state, [{"action": "fill_form", "fields": {"name": "Recovered"}}]))
        bad = self.call("open", path="ambiguous.pdf")
        self.assertFalse(bad["ok"], "Unrelated field/widget objects must not be silently accepted")
        self.assertEqual(bad["error"]["code"], "FORM_STRUCTURE")

    def test_signed_pdf_read_only_and_changed_plan(self):
        state = self.opened("signed.pdf")
        self.assertTrue(state["signed"])
        self.assertEqual(engine.digest(engine.Engine(str(self.workspace)).current(state)), engine.digest(self.workspace / "signed.pdf"))
        self.assertEqual(self.call("plan", review_id=state["review_id"], expected_revision=0, commands=[{"action": "fill_form", "fields": {"name": "x"}}])["error"]["code"], "SIGNED_PDF")
        state = self.opened()
        plan = self.plan(state, [{"action": "highlight_text", "text": "Payment is due"}])
        with (self.workspace / ".pdf-review" / state["review_id"] / "plans" / plan["plan_id"] / "candidate.pdf").open("ab") as f:
            f.write(b"\nchanged")
        self.assertEqual(self.call("apply", review_id=state["review_id"], expected_revision=0, plan_id=plan["plan_id"], confirmed=True)["error"]["code"], "PLAN_CHANGED")

    def test_duplicate_ids_locking_and_image_mutation(self):
        state = self.opened()
        note = {"id": "same", "type": "note", "page": 1, "x": 450, "y": 180, "content": "复核"}
        bad = self.call("plan", review_id=state["review_id"], expected_revision=0, commands=[{"action": "add_annotations", "annotations": [note, note]}])
        self.assertEqual(bad["error"]["code"], "DUPLICATE_ID")
        lock = self.workspace / ".pdf-review" / state["review_id"] / ".lock"
        lock.touch()
        try:
            self.assertEqual(self.call("save_as", review_id=state["review_id"], expected_revision=0, path="locked-output.pdf")["error"]["code"], "REVIEW_BUSY")
        finally:
            lock.unlink()
        shutil.copyfile(self.workspace / "test-signature.png", self.workspace / "mutable-signature.png")
        changed = self.apply(self.plan(state, [{"action": "add_annotations", "annotations": [{"id": "mutable", "type": "image", "page": 1, "image_path": "mutable-signature.png", "x": 100, "y": 400, "width": 200}]}]))
        Image.new("RGB", (100, 30), "black").save(self.workspace / "mutable-signature.png")
        bad = self.call("plan", review_id=changed["review_id"], expected_revision=1, commands=[{"action": "add_annotations", "annotations": [note]}])
        self.assertEqual(bad["error"]["code"], "IMAGE_CHANGED")

    def test_empty_workspace(self):
        with tempfile.TemporaryDirectory(dir=self.workspace) as empty:
            result = self.success(engine.run({"workspace_dir": empty, "action": "list_pdfs"}))
            self.assertEqual(result["files"], [])

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_workspace_junction_boundary(self):
        target = self.workspace.parent / "outside-junction-target"
        target.mkdir(exist_ok=True)
        shutil.copyfile(self.workspace / "sample.pdf", target / "outside.pdf")
        link = self.workspace / "junction-outside"
        env = dict(os.environ, PDF_TEST_LINK=str(link), PDF_TEST_TARGET=str(target))
        proc = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "New-Item -ItemType Junction -Path $env:PDF_TEST_LINK -Target $env:PDF_TEST_TARGET -ErrorAction Stop | Out-Null"], env=env, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        try:
            self.assertEqual(self.call("open", path="junction-outside/outside.pdf")["error"]["code"], "PATH_OUTSIDE_WORKSPACE")
            listing = self.success(self.call("list_pdfs"))
            self.assertFalse(any("outside-junction-target" in item["path"] for item in listing["files"]))
        finally:
            link.rmdir()  # Removes only the junction itself, never its target.

    def test_shapes_and_chinese_stamp(self):
        state = self.opened()
        items = [
            {"type": "rectangle", "page": 1, "x": 60, "y": 160, "width": 310, "height": 45, "color": [0.1, 0.3, 0.8]},
            {"type": "circle", "page": 1, "x": 400, "y": 300, "width": 60, "height": 60, "color": [0.8, 0.1, 0.1]},
            {"type": "stamp", "page": 1, "x": 350, "y": 220, "width": 180, "height": 40, "content": "已复核·仅供测试"},
            {"type": "freetext", "page": 1, "x": 70, "y": 300, "width": 250, "height": 35, "content": "中文说明：测试副本"},
            {"type": "underline", "page": 1, "rects": [[70, 250, 190, 18]], "color": [0.2, 0.3, 0.9]},
        ]
        changed = self.apply(self.plan(state, [{"action": "add_annotations", "annotations": items}]))
        result = self.success(self.call("save_as", review_id=changed["review_id"], expected_revision=1, path="shapes-and-stamp.pdf"))
        reader = PdfReader(result["path"])
        self.assertEqual({a.get_object()["/Subtype"] for a in reader.pages[0]["/Annots"]}, {"/Square", "/Circle", "/Underline"})
        self.assertIn("已复核", reader.pages[0].extract_text())

    def test_native_host_tool_and_missing_runtime(self):
        manifest = json.loads((PAYLOAD / "manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest.get("mcps"))
        decl = manifest["tools"][0]
        spec = importlib.util.spec_from_file_location("pdf_native_adapter", PAYLOAD / decl["file"])
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        tool = getattr(adapter, decl["class"])()
        self.assertEqual(tool.card.name, "pdf_review")
        args = {"workspace_dir": str(self.workspace), "action": "open", "payload": {"path": "sample.pdf"}}
        self.assertEqual(len(self.success(asyncio.run(tool.invoke(args)))["pages"]), 2)
        probe = subprocess.run([sys.executable, "-S", str(PAYLOAD / "runtime/pdf_review.py")], input=b'{"action":"status"}', capture_output=True)
        self.assertFalse(json.loads(probe.stdout)["ready"])
        old = os.environ.get("WORKSWARM_PDF_PYTHON")
        os.environ["WORKSWARM_PDF_PYTHON"] = str(self.workspace / "missing-python")
        try:
            self.assertFalse(asyncio.run(tool.invoke(args))["ok"])
        finally:
            if old is None:
                os.environ.pop("WORKSWARM_PDF_PYTHON", None)
            else:
                os.environ["WORKSWARM_PDF_PYTHON"] = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
