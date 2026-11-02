"""Independent, workspace-bounded PDF review engine. JSON stdin/stdout CLI.

No MCP App, web server, shell, network access, or upstream viewer code is used.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid
from contextlib import contextmanager

VERSION = "1.1.0"
LIMIT_BYTES = 50 * 1024 * 1024
REQUIRED = {"pypdf": "pypdf", "reportlab": "reportlab", "PIL": "Pillow", "pypdfium2": "pypdfium2"}
ACTIONS = ["status", "help", "list_pdfs", "open", "preview", "search", "plan", "apply", "save_as"]
TYPES = {"highlight", "underline", "strikethrough", "note", "freetext", "rectangle", "circle", "stamp", "image"}


class ReviewError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def fail(code, message):
    raise ReviewError(code, message)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dependencies():
    result = {}
    for module, distribution in REQUIRED.items():
        try:
            result[distribution] = importlib.metadata.version(distribution) if importlib.util.find_spec(module) else None
        except (ImportError, ValueError, importlib.metadata.PackageNotFoundError):
            result[distribution] = None
    return result


def libs():
    missing = [name for name, version in dependencies().items() if version is None]
    if missing:
        fail("DEPENDENCIES_MISSING", "当前 Python 缺少依赖：" + "、".join(missing) + "。请按 README 安装 requirements.txt，或设置 WORKSWARM_PDF_PYTHON。")
    global PdfReader, PdfWriter, G, pdfium, Image, canvas, ImageReader, pdfmetrics
    from pypdf import PdfReader, PdfWriter
    from pypdf import generic as G
    import pypdfium2 as pdfium
    from PIL import Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def number(value, label, low=0, high=100000):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        fail("BAD_INPUT", f"{label} 必须在 {low} 到 {high} 之间。")
    return float(value)


def integer(value, label, low=0, high=100000):
    n = number(value, label, low, high)
    if int(n) != n:
        fail("BAD_INPUT", f"{label} 必须是整数。")
    return int(n)


def text(value, label, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        fail("BAD_INPUT", f"{label} 必须是非空文本，最多 {maximum} 字符。")
    return value


def font_for(value):
    return "STSong-Light" if any(ord(c) > 255 for c in value) else "Helvetica"


def json_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="write-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, allow_nan=False, indent=2)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_pdf(path):
    if path.stat().st_size > LIMIT_BYTES:
        fail("FILE_TOO_LARGE", "PDF 超过 50 MiB 上限。")
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            fail("ENCRYPTED_PDF", "当前版本不处理加密 PDF；请提供经授权解密的副本。")
        if not 0 < len(reader.pages) <= 1000:
            fail("PAGE_LIMIT", "PDF 必须包含 1 到 1000 页。")
        return reader
    except ReviewError:
        raise
    except Exception:
        fail("INVALID_PDF", "无法读取 PDF，请检查文件是否完整。")


def field_name(widget):
    parts, seen = [], set()
    while widget is not None:
        widget = widget.get_object()
        if id(widget) in seen:
            fail("FORM_STRUCTURE", "表单字段父子结构存在循环。")
        seen.add(id(widget))
        if widget.get("/T"):
            parts.append(str(widget["/T"]))
        widget = widget.get("/Parent")
    return ".".join(reversed(parts))


def inherited(widget, key, default=None):
    seen = set()
    while widget is not None:
        widget = widget.get_object()
        if id(widget) in seen:
            fail("FORM_STRUCTURE", "表单字段结构存在循环。")
        seen.add(id(widget))
        if key in widget:
            return widget[key]
        widget = widget.get("/Parent")
    return default


def widgets(reader):
    for page_no, page in enumerate(reader.pages, 1):
        for ref in page.get("/Annots", []):
            item = ref.get_object()
            if item.get("/Subtype") == "/Widget":
                yield page_no, item


def prepare_fields(writer):
    """Recover only unambiguous, genuinely orphaned, parentless widgets."""
    canonical = {}
    visited = set()

    def walk(ref):
        obj = ref.get_object()
        if id(obj) in visited:
            fail("FORM_STRUCTURE", "表单字段树存在循环或重复引用。")
        visited.add(id(obj))
        if obj.get("/T"):
            name = field_name(obj)
            if name in canonical and canonical[name] is not obj:
                fail("FORM_STRUCTURE", f"字段 {name} 在字段树中重复。")
            canonical[name] = obj
        for child in obj.get("/Kids", []):
            walk(child)

    form = writer.root_object.get("/AcroForm")
    if form is not None:
        for ref in form.get_object().get("/Fields", []):
            walk(ref)
    seen = {}
    orphans = []
    for _, widget in widgets(writer):
        name = field_name(widget)
        if not name:
            continue
        owner = widget
        while "/T" not in owner and owner.get("/Parent") is not None:
            owner = owner["/Parent"].get_object()
        identity = id(owner)
        if name in seen and seen[name] != identity:
            fail("FORM_STRUCTURE", f"字段 {name} 有多个无关联的同名对象，不能安全填写。")
        seen[name] = identity
        if name in canonical:
            # get_fields() wraps dictionaries and loses object identity. Compare
            # the raw field-tree owner with the widget's actual named ancestor.
            if canonical[name] is not owner:
                fail("FORM_STRUCTURE", f"字段 {name} 的字段树与页面控件不一致。")
        else:
            if widget.get("/Parent") is not None or "/FT" not in widget:
                fail("FORM_STRUCTURE", f"字段 {name} 缺少可安全恢复的字段树。")
            orphans.append(widget)
    if orphans:
        root = writer.root_object
        if "/AcroForm" not in root:
            root[G.NameObject("/AcroForm")] = writer._add_object(G.DictionaryObject())
        form = root["/AcroForm"].get_object()
        if "/Fields" not in form:
            form[G.NameObject("/Fields")] = G.ArrayObject()
        for widget in orphans:
            form["/Fields"].append(widget.indirect_reference)
    return bool(orphans)


def field_catalog(reader):
    fields = reader.get_fields() or {}
    result = []
    for name, field in fields.items():
        kind = str(field.get("/FT", ""))
        if not kind:
            continue
        entry = {"name": name, "type": kind, "value": str(field.get("/V", "")), "widgets": []}
        if field.get("/Opt"):
            entry["options"] = [str(v[0] if isinstance(v, list) else v) for v in field["/Opt"]]
        for page_no, widget in widgets(reader):
            if field_name(widget) == name:
                box = reader.pages[page_no - 1].cropbox
                rect = [float(v) for v in widget.get("/Rect", [0, 0, 0, 0])]
                entry["widgets"].append({"page": page_no, "rect": [rect[0] - float(box.left), float(box.top) - rect[3], rect[2] - rect[0], rect[3] - rect[1]]})
                if kind == "/Btn":
                    ap = widget.get("/AP", {}).get("/N", {})
                    if hasattr(ap, "keys"):
                        entry["options"] = sorted(set(entry.get("options", [])) | set(map(str, ap.keys())))
        result.append(entry)
    return result


def validate_values(reader, updates):
    if not isinstance(updates, dict) or not updates or len(updates) > 40:
        fail("BAD_INPUT", "fields 必须是非空字段名到值的对象，每批最多 40 项。")
    catalog = {f["name"]: f for f in field_catalog(reader)}
    raw_fields = reader.get_fields() or {}
    result = {}
    for name, value in updates.items():
        if name not in catalog:
            fail("FIELD_NOT_FOUND", f"不存在可填写字段：{name}")
        field, raw = catalog[name], raw_fields[name]
        if int(raw.get("/Ff", 0)) & 1:
            fail("READ_ONLY_FIELD", f"字段 {name} 为只读。")
        kind = field["type"]
        if kind == "/Sig":
            fail("SIGNATURE_FIELD", "不填写密码学签名域；请按用户确认的位置放置签名图片。")
        if kind == "/Btn":
            options = field.get("options", [])
            if isinstance(value, bool):
                on = [o for o in options if o != "/Off"]
                if value and len(on) != 1:
                    fail("FIELD_VALUE", f"字段 {name} 有多个选项，请指定：{options}")
                value = on[0] if value else "/Off"
            if not isinstance(value, str) or value not in options:
                fail("FIELD_VALUE", f"字段 {name} 的值须从 {options} 中选择。")
        elif kind in {"/Tx", "/Ch"}:
            if not isinstance(value, str) or len(value) > 2000 or "\x00" in value:
                fail("FIELD_VALUE", f"字段 {name} 的值必须是最多 2000 字符的文本。")
            if kind == "/Ch" and value not in field.get("options", []):
                fail("FIELD_VALUE", f"字段 {name} 的值不在可选列表中。")
            if raw.get("/MaxLen") and len(value) > int(raw["/MaxLen"]):
                fail("FIELD_VALUE", f"字段 {name} 超过允许长度。")
        else:
            fail("FIELD_TYPE", f"暂不支持字段 {name} 的类型 {kind}。")
        result[name] = value
    return result


def set_text_appearances(writer, updates):
    """Generate real widget appearances, including Chinese, without flattening."""
    for _, widget in widgets(writer):
        name = field_name(widget)
        if name not in updates or inherited(widget, "/FT") not in {"/Tx", "/Ch"}:
            continue
        value = updates[name]
        rect = list(map(float, widget["/Rect"]))
        w, h = rect[2] - rect[0], rect[3] - rect[1]
        if w <= 4 or h <= 4:
            fail("FIELD_APPEARANCE", f"字段 {name} 的显示区域过小。")
        font = font_for(value)
        lines = value.replace("\r\n", "\n").split("\n")
        if len(lines) > 1 and not int(inherited(widget, "/Ff", 0)) & 4096:
            fail("FIELD_VALUE", f"字段 {name} 不支持多行文本。")
        size = min(12, (h - 4) / (max(1, len(lines)) * 1.25))
        while size >= 6 and any(pdfmetrics.stringWidth(line, font, size) > w - 6 for line in lines):
            size -= 0.5
        if size < 6:
            fail("FIELD_APPEARANCE", f"字段 {name} 的文字无法完整放入区域，请缩短值。")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(w, h))
        c.setFont(font, size)
        c.setFillColorRGB(0.07, 0.12, 0.18)
        for index, line in enumerate(lines):
            c.drawString(3, max(2, h - size - 2) - index * size * 1.25, line)
        c.save()
        page = PdfReader(io.BytesIO(buffer.getvalue())).pages[0]
        stream = G.DecodedStreamObject()
        stream.set_data(page.get_contents().get_data())
        stream.update({G.NameObject("/Type"): G.NameObject("/XObject"), G.NameObject("/Subtype"): G.NameObject("/Form"), G.NameObject("/BBox"): G.ArrayObject([G.FloatObject(v) for v in [0, 0, w, h]]), G.NameObject("/Resources"): page["/Resources"].clone(writer)})
        widget[G.NameObject("/AP")] = G.DictionaryObject({G.NameObject("/N"): writer._add_object(stream)})


def verify_pdf(path, expected_fields=None):
    reader = read_pdf(path)
    fields = reader.get_fields() or {}
    for name, expected in (expected_fields or {}).items():
        if name not in fields or str(fields[name].get("/V", "")) != expected:
            fail("VERIFY_FAILED", f"保存后字段 {name} 的实际值不一致。")
        for _, widget in widgets(reader):
            if field_name(widget) != name:
                continue
            if str(inherited(widget, "/V", "")) != expected:
                fail("VERIFY_FAILED", f"字段 {name} 的页面控件与字段树值不一致。")
            appearance = widget.get("/AP", {}).get("/N")
            if appearance is None:
                fail("VERIFY_FAILED", f"字段 {name} 缺少显示外观。")
            if inherited(widget, "/FT") in {"/Tx", "/Ch"} and not appearance.get_object().get_data():
                fail("VERIFY_FAILED", f"字段 {name} 的显示外观为空。")
    return reader


class Engine:
    def __init__(self, workspace_dir):
        raw = Path(text(workspace_dir, "workspace_dir", 4096)).expanduser()
        if not raw.is_absolute() or not raw.is_dir():
            fail("WORKSPACE_REQUIRED", "workspace_dir 必须是已存在工作目录的绝对路径。")
        self.root = raw.resolve()
        self.store = self.root / ".pdf-review"
        self.internal()

    def internal(self, *parts):
        path = self.store.joinpath(*parts)
        if not path.resolve().is_relative_to(self.root):
            fail("PATH_OUTSIDE_WORKSPACE", "内部审阅目录不能通过符号链接或联接指向工作目录之外。")
        cursor = path
        while cursor != self.root:
            if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
                fail("UNSAFE_STATE_PATH", "内部审阅路径不能使用符号链接或联接。")
            cursor = cursor.parent
        return path

    def file(self, value, suffixes=None, existing=True):
        value = text(value, "path", 4096)
        path = Path(value).expanduser()
        path = (path if path.is_absolute() else self.root / path).resolve()
        if not path.is_relative_to(self.root) or path.is_relative_to(self.store):
            fail("PATH_OUTSIDE_WORKSPACE", "文件必须位于已明确指定的工作目录内，且不能位于内部审阅目录。")
        if suffixes and path.suffix.lower() not in suffixes:
            fail("FILE_TYPE", "文件类型不受支持。")
        if existing and (not path.is_file() or path.stat().st_size > LIMIT_BYTES):
            fail("FILE_UNAVAILABLE", "文件不存在、不是普通文件或超过 50 MiB。")
        return path

    def review_id(self, payload):
        value = payload.get("review_id", "")
        if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{32}", value):
            fail("REVIEW_REQUIRED", "请使用 open 返回的 review_id。")
        return value

    def load(self, payload):
        rid = self.review_id(payload)
        path = self.internal(rid, "state.json")
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            fail("REVIEW_NOT_FOUND", "审阅记录不存在或已损坏。")
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("review_id") != rid:
            fail("REVIEW_NOT_FOUND", "审阅标识不一致。")
        return state

    def current(self, state):
        rev = integer(state["revision"], "revision")
        return self.internal(state["review_id"], "revisions", f"{rev:06d}.pdf")

    def revision(self, state, payload):
        if payload.get("expected_revision") != state["revision"] or isinstance(payload.get("expected_revision"), bool):
            fail("STALE_REVISION", f"审阅版本已变化；当前 revision={state['revision']}，请重新获取预览和计划。")

    @contextmanager
    def locked(self, rid):
        lock = self.internal(rid, ".lock")
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            fail("REVIEW_BUSY", "该审阅正在执行其他操作；请等待后重新读取状态，不要重复应用。")
        try:
            os.close(fd)
            yield
        finally:
            lock.unlink(missing_ok=True)

    def list_pdfs(self, payload):
        found, visited = [], 0
        for directory, dirs, files in os.walk(self.root, followlinks=False):
            safe = []
            for d in dirs:
                child = Path(directory) / d
                if d.startswith(".") or d in {"node_modules", "venv", "__pycache__"}:
                    continue
                if child.is_symlink() or (hasattr(child, "is_junction") and child.is_junction()) or not child.resolve().is_relative_to(self.root):
                    continue
                safe.append(d)
            dirs[:] = sorted(safe)
            visited += 1
            if visited > 2000:
                break
            for name in sorted(files):
                if not name.lower().endswith(".pdf"):
                    continue
                try:
                    p = self.file(str(Path(directory) / name), {".pdf"})
                except ReviewError:
                    continue
                found.append({"path": str(p), "bytes": p.stat().st_size})
                if len(found) >= 500:
                    return {"files": found, "truncated": True, "workspace_dir": str(self.root)}
        return {"files": found, "truncated": visited > 2000, "workspace_dir": str(self.root)}

    def pages(self, reader):
        result = []
        for i, p in enumerate(reader.pages):
            w, h = float(p.cropbox.width), float(p.cropbox.height)
            if p.rotation % 180:
                w, h = h, w
            result.append({"page": i + 1, "width": w, "height": h})
        return result

    def open(self, payload):
        source = self.file(payload.get("path"), {".pdf"})
        reader = read_pdf(source)
        signed = any(f.get("/FT") == "/Sig" and f.get("/V") for f in (reader.get_fields() or {}).values()) or bool(reader.trailer["/Root"].get("/Perms"))
        rid = uuid.uuid4().hex
        folder = self.internal(rid)
        folder.mkdir(parents=True)
        baseline = self.internal(rid, "base.pdf")
        recovered = False
        if signed:
            # Rewriting even without edits invalidates existing signatures.
            shutil.copyfile(source, baseline)
        else:
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            recovered = prepare_fields(writer)
            for page in writer.pages:
                if page.rotation:
                    page.transfer_rotation_to_content()
            writer.write(baseline)
        normalized = verify_pdf(baseline)
        revdir = self.internal(rid, "revisions")
        revdir.mkdir()
        shutil.copyfile(baseline, revdir / "000000.pdf")
        state = {"review_id": rid, "revision": 0, "source": str(source), "source_sha256": digest(source), "base_sha256": digest(baseline), "pages": self.pages(normalized), "annotations": [], "fields": {}, "signed": bool(signed)}
        json_write(self.internal(rid, "state.json"), state)
        previews = self.render(self.current(state), [1], self.internal(rid, "previews", "r0"), 1.25)
        return {**self.summary(state), "form_fields": field_catalog(normalized), "recovered_orphan_fields": recovered, "previews": previews, "message": "已创建原稿快照；请通过宿主文件查看工具核对页面预览。"}

    def summary(self, state):
        return {k: state[k] for k in ["review_id", "revision", "source", "pages", "annotations", "fields", "signed"]}

    def render(self, path, pages, folder, scale):
        scale = number(scale, "scale", 0.5, 3)
        if not isinstance(pages, list) or not 1 <= len(pages) <= 4:
            fail("PAGE_LIMIT", "每次预览请选择 1 到 4 页。")
        folder.mkdir(parents=True, exist_ok=True)
        outputs = []
        with pdfium.PdfDocument(path) as document:
            document.init_forms()
            for requested in pages:
                n = integer(requested, "page", 1, len(document))
                page = document[n - 1]
                w, h = page.get_size()
                if w * h * scale * scale > 24_000_000:
                    fail("RENDER_LIMIT", "页面预览超过像素上限，请降低 scale。")
                bitmap = page.render(scale=scale, draw_annots=True)
                image = bitmap.to_pil()
                output = folder / f"page-{n}-{scale:g}.png"
                image.save(output)
                outputs.append({"page": n, "path": str(output), "width": image.width, "height": image.height})
                image.close()
                bitmap.close()
                page.close()
        return outputs

    def preview(self, payload):
        state = self.load(payload)
        return {**self.summary(state), "previews": self.render(self.current(state), payload.get("pages", [1]), self.internal(state["review_id"], "previews", f"r{state['revision']}"), payload.get("scale", 1.25))}

    def locate(self, path, query, requested=None):
        query = text(query, "query", 300)
        matches = []
        reader = read_pdf(path)
        with pdfium.PdfDocument(path) as doc:
            selected = [integer(requested, "page", 1, len(doc))] if requested is not None else list(range(1, len(doc) + 1))
            for n in selected:
                page = doc[n - 1]
                tp = page.get_textpage()
                searcher = tp.search(query, match_case=False)
                while len(matches) < 40:
                    hit = searcher.get_next()
                    if hit is None:
                        break
                    start, count = hit
                    boxes = [tp.get_charbox(i) for i in range(start, start + count)]
                    boxes = [b for b in boxes if b[2] > b[0] and b[3] > b[1]]
                    groups = []
                    for b in boxes:
                        if groups and abs((groups[-1][1] + groups[-1][3]) / 2 - (b[1] + b[3]) / 2) < max(2, (b[3] - b[1]) / 2):
                            old = groups[-1]
                            groups[-1] = [min(old[0], b[0]), min(old[1], b[1]), max(old[2], b[2]), max(old[3], b[3])]
                        else:
                            groups.append(list(b))
                    crop = reader.pages[n - 1].cropbox
                    rects = [[b[0] - float(crop.left), float(crop.top) - b[3], b[2] - b[0], b[3] - b[1]] for b in groups]
                    if rects:
                        matches.append({"page": n, "text": query, "rects": rects})
                searcher.close()
                tp.close()
                page.close()
                if len(matches) >= 40:
                    break
        return matches

    def search(self, payload):
        state = self.load(payload)
        return {"review_id": state["review_id"], "revision": state["revision"], "matches": self.locate(self.current(state), payload.get("query"), payload.get("page")), "message": "返回页面位置用于审阅；扫描页可能没有可搜索文字。"}

    def annotation(self, raw, state):
        if not isinstance(raw, dict):
            fail("BAD_INPUT", "annotation 必须是对象。")
        a = copy.deepcopy(raw)
        a["id"] = a.get("id") or uuid.uuid4().hex
        if not isinstance(a["id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", a["id"]):
            fail("BAD_INPUT", "批注 id 仅可含字母、数字、下划线和连字符，最多 64 字符。")
        if a.get("type") not in TYPES:
            fail("ANNOTATION_TYPE", "不支持的批注类型。")
        a["page"] = integer(a.get("page"), "page", 1, len(state["pages"]))
        page = state["pages"][a["page"] - 1]
        color = a.get("color", [1, 0.85, 0.1])
        if not isinstance(color, list) or len(color) != 3:
            fail("BAD_INPUT", "color 必须是三个 0 到 1 的 RGB 数值。")
        a["color"] = [number(v, "color", 0, 1) for v in color]
        if a["type"] in {"highlight", "underline", "strikethrough"}:
            if not isinstance(a.get("rects"), list) or not 1 <= len(a["rects"]) <= 80:
                fail("BAD_INPUT", "文字标注需要 1 到 80 个 rects，格式为 [x,y,width,height]。")
            rects = a["rects"]
        else:
            if a["type"] in {"note", "freetext", "stamp"}:
                a["content"] = text(a.get("content", a.get("label")), "content", 2000)
            a["width"] = a.get("width", 22 if a["type"] == "note" else 150)
            a["height"] = a.get("height", 22 if a["type"] == "note" else 42)
            if a["type"] == "image":
                image_path = self.file(a.get("image_path"), {".png", ".jpg", ".jpeg"})
                with Image.open(image_path) as im:
                    if im.width * im.height > 24_000_000:
                        fail("IMAGE_LIMIT", "图片超过像素上限。")
                    im.verify()
                with Image.open(image_path) as im:
                    if "height" not in raw:
                        a["height"] = float(a["width"]) * im.height / im.width
                a["image_path"] = str(image_path)
                a["image_sha256"] = digest(image_path)
            rects = [[a.get("x"), a.get("y"), a["width"], a["height"]]]
        for r in rects:
            if not isinstance(r, list) or len(r) != 4:
                fail("BAD_INPUT", "矩形须为 [x,y,width,height]。")
            x, y, w, h = [number(v, "rect") for v in r]
            if w <= 0 or h <= 0 or x + w > page["width"] + 0.01 or y + h > page["height"] + 0.01:
                fail("BOUNDS", "批注超出页面范围。坐标原点为可见页面左上角，单位为 PDF 点。")
        a["font_size"] = number(a.get("font_size", 14), "font_size", 6, 72)
        return a

    def plan(self, payload):
        rid = self.review_id(payload)
        with self.locked(rid):
            state = self.load(payload)
            self.revision(state, payload)
            if state["signed"]:
                fail("SIGNED_PDF", "该文档已有数字签名或认证，仅允许查看；请使用未签署的测试副本。")
            commands = payload.get("commands")
            if not isinstance(commands, list) or not 1 <= len(commands) <= 5:
                fail("BATCH_LIMIT", "每个计划需要 1 到 5 条命令。")
            candidate, changes, affected = copy.deepcopy(state), [], set()
            for cmd in commands:
                if not isinstance(cmd, dict):
                    fail("BAD_INPUT", "commands 的每一项必须是对象。")
                action = cmd.get("action")
                if action in {"add_annotations", "update_annotations"}:
                    items = cmd.get("annotations")
                    if not isinstance(items, list) or not 1 <= len(items) <= 5:
                        fail("BATCH_LIMIT", "每条命令包含 1 到 5 个批注。")
                    for raw in items:
                        current = next((a for a in candidate["annotations"] if a["id"] == raw.get("id")), None) if isinstance(raw, dict) else None
                        if action == "update_annotations":
                            if current is None:
                                fail("ANNOTATION_NOT_FOUND", "只能修改本次审阅创建的已知批注 ID。")
                            affected.add(current["page"])
                            a = self.annotation({**current, **raw}, candidate)
                            candidate["annotations"].remove(current)
                        else:
                            a = self.annotation(raw, candidate)
                            if any(old["id"] == a["id"] for old in candidate["annotations"]):
                                fail("DUPLICATE_ID", "批注 ID 重复。")
                        candidate["annotations"].append(a)
                        affected.add(a["page"])
                        changes.append({"action": action, "id": a["id"], "page": a["page"], "type": a["type"]})
                elif action == "remove_annotations":
                    ids = cmd.get("ids")
                    if not isinstance(ids, list) or not ids or len(ids) > 20:
                        fail("BAD_INPUT", "ids 必须包含 1 到 20 个批注 ID。")
                    for aid in ids:
                        a = next((a for a in candidate["annotations"] if a["id"] == aid), None)
                        if a is None:
                            fail("ANNOTATION_NOT_FOUND", "只能删除本次审阅创建的已知批注 ID。")
                        candidate["annotations"].remove(a)
                        affected.add(a["page"])
                        changes.append({"action": action, "id": aid, "page": a["page"]})
                elif action == "highlight_text":
                    hits = self.locate(self.current(state), cmd.get("text"), cmd.get("page"))
                    if not hits:
                        fail("TEXT_NOT_FOUND", "未找到可定位文字；扫描 PDF 请先预览并使用用户确认的矩形坐标。")
                    occurrence = cmd.get("occurrence", 1)
                    selected = hits if occurrence == "all" else [hits[integer(occurrence, "occurrence", 1, len(hits)) - 1]]
                    if len(selected) > 5:
                        fail("BATCH_LIMIT", "单次最多高亮 5 个匹配，请指定页或 occurrence。")
                    for hit in selected:
                        a = self.annotation({"type": "highlight", "page": hit["page"], "rects": hit["rects"], "content": cmd["text"], "color": cmd.get("color", [1, 0.85, 0.1])}, candidate)
                        candidate["annotations"].append(a)
                        affected.add(a["page"])
                        changes.append({"action": action, "id": a["id"], "page": a["page"], "text": cmd["text"]})
                elif action == "fill_form":
                    values = validate_values(read_pdf(self.current(state)), cmd.get("fields"))
                    candidate["fields"].update(values)
                    for f in field_catalog(read_pdf(self.current(state))):
                        if f["name"] in values:
                            affected.update(w["page"] for w in f["widgets"])
                    changes.append({"action": action, "fields": values})
                else:
                    fail("UNSUPPORTED_ACTION", "计划仅支持 highlight_text、add_annotations、update_annotations、remove_annotations、fill_form。")
            if len(candidate["annotations"]) > 200:
                fail("ANNOTATION_LIMIT", "每次审阅最多保留 200 个新增批注。")
            if len(affected) > 4:
                fail("BATCH_LIMIT", "每个计划最多影响 4 页，便于逐页核对。")
            pid = uuid.uuid4().hex
            folder = self.internal(rid, "plans", pid)
            folder.mkdir(parents=True)
            candidate_pdf = folder / "candidate.pdf"
            self.build(candidate, candidate_pdf)
            previews = self.render(candidate_pdf, sorted(affected) or [1], folder, 1.25)
            record = {"plan_id": pid, "base_revision": state["revision"], "candidate": candidate, "pdf_sha256": digest(candidate_pdf), "changes": changes, "previews": previews}
            json_write(folder / "plan.json", record)
            return {"review_id": rid, "revision": state["revision"], "plan_id": pid, "changes": changes, "previews": previews, "applied": False, "message": "这是待确认预览，当前审阅版本未改变。请展示预览及变更，收到用户确认后再调用 apply。"}

    def build(self, state, output):
        base = self.internal(state["review_id"], "base.pdf")
        if digest(base) != state["base_sha256"]:
            fail("SNAPSHOT_CHANGED", "原稿快照已变化，请重新 open。")
        writer = PdfWriter()
        writer.clone_document_from_reader(read_pdf(base))
        if state["fields"]:
            validate_values(writer, state["fields"])
            writer.update_page_form_field_values(None, state["fields"], auto_regenerate=False)
            set_text_appearances(writer, state["fields"])
        for index, page in enumerate(writer.pages):
            annotations = [a for a in state["annotations"] if a["page"] == index + 1]
            overlays = [a for a in annotations if a["type"] in {"stamp", "image", "freetext"}]
            crop = page.cropbox
            if overlays:
                buf = io.BytesIO()
                c = canvas.Canvas(buf, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
                c.translate(-float(page.mediabox.left), -float(page.mediabox.bottom))
                for a in overlays:
                    x, y, w, h = float(crop.left) + a["x"], float(crop.top) - a["y"] - a["height"], a["width"], a["height"]
                    if a["type"] == "image":
                        image_path = self.file(a["image_path"], {".png", ".jpg", ".jpeg"})
                        if digest(image_path) != a["image_sha256"]:
                            fail("IMAGE_CHANGED", "签名图片已变化，请重新计划放置图片。")
                        c.drawImage(ImageReader(str(image_path)), x, y, width=w, height=h, preserveAspectRatio=True, anchor="c", mask="auto")
                    else:
                        value = a["content"]
                        size, font = a["font_size"], font_for(value)
                        if "\n" in value or pdfmetrics.stringWidth(value, font, size) > w - 8 or size * 1.3 > h:
                            fail("TEXT_BOUNDS", "印章或自由文字无法完整放入区域，请增大区域或缩小 font_size。")
                        c.setStrokeColorRGB(*a["color"])
                        c.setFillColorRGB(0.55, 0.05, 0.1)
                        if a["type"] == "stamp":
                            c.setLineWidth(1.5)
                            c.rect(x, y, w, h)
                        c.setFont(font, size)
                        c.drawString(x + 4, y + (h - size) / 2 + 2, value)
                c.save()
                page.merge_page(PdfReader(io.BytesIO(buf.getvalue())).pages[0])
            for a in annotations:
                if a in overlays:
                    continue
                rects = a.get("rects", [[a.get("x"), a.get("y"), a.get("width"), a.get("height")]])
                converted = [[float(crop.left) + r[0], float(crop.top) - r[1] - r[3], float(crop.left) + r[0] + r[2], float(crop.top) - r[1]] for r in rects]
                subtype = {"highlight": "Highlight", "underline": "Underline", "strikethrough": "StrikeOut", "note": "Text", "rectangle": "Square", "circle": "Circle"}[a["type"]]
                bounds = [min(r[0] for r in converted), min(r[1] for r in converted), max(r[2] for r in converted), max(r[3] for r in converted)]
                obj = G.DictionaryObject({G.NameObject("/Type"): G.NameObject("/Annot"), G.NameObject("/Subtype"): G.NameObject("/" + subtype), G.NameObject("/Rect"): G.ArrayObject([G.FloatObject(v) for v in bounds]), G.NameObject("/NM"): G.TextStringObject(a["id"]), G.NameObject("/Contents"): G.TextStringObject(a.get("content", "")), G.NameObject("/C"): G.ArrayObject([G.FloatObject(v) for v in a["color"]]), G.NameObject("/F"): G.NumberObject(4)})
                if a["type"] in {"highlight", "underline", "strikethrough"}:
                    quads = [v for x0, y0, x1, y1 in converted for v in [x0, y1, x1, y1, x0, y0, x1, y0]]
                    obj[G.NameObject("/QuadPoints")] = G.ArrayObject([G.FloatObject(v) for v in quads])
                    obj[G.NameObject("/CA")] = G.FloatObject(0.4 if a["type"] == "highlight" else 1)
                if a["type"] == "note":
                    obj[G.NameObject("/Name")] = G.NameObject("/Comment")
                writer.add_annotation(index, obj)
        writer.write(output)
        verify_pdf(output, state["fields"])

    def apply(self, payload):
        rid = self.review_id(payload)
        with self.locked(rid):
            state = self.load(payload)
            self.revision(state, payload)
            if payload.get("confirmed") is not True:
                fail("CONFIRMATION_REQUIRED", "收到用户对该计划的明确确认后，才可传 confirmed=true 应用。")
            pid = payload.get("plan_id", "")
            if not isinstance(pid, str) or not re.fullmatch("[0-9a-f]{32}", pid):
                fail("PLAN_REQUIRED", "请使用 plan 返回的 plan_id。")
            folder = self.internal(rid, "plans", pid)
            record = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
            if record["base_revision"] != state["revision"] or record["candidate"]["review_id"] != rid:
                fail("STALE_PLAN", "计划已过期，请重新生成并确认。")
            candidate_pdf = folder / "candidate.pdf"
            if digest(candidate_pdf) != record["pdf_sha256"]:
                fail("PLAN_CHANGED", "候选 PDF 已变化，请重新生成计划。")
            next_state = record["candidate"]
            next_state["revision"] = state["revision"] + 1
            destination = self.current(next_state)
            with open(candidate_pdf, "rb") as source, open(destination, "xb") as target:
                shutil.copyfileobj(source, target)
            verify_pdf(destination, next_state["fields"])
            json_write(self.internal(rid, "state.json"), next_state)
            return {**self.summary(next_state), "applied": True, "changes": record["changes"], "previews": record["previews"], "message": "已应用确认的计划，原文件未修改。"}

    def save_as(self, payload):
        rid = self.review_id(payload)
        with self.locked(rid):
            state = self.load(payload)
            self.revision(state, payload)
            output = self.file(payload.get("path"), {".pdf"}, existing=False)
            if output == Path(state["source"]).resolve() or output.exists():
                fail("OUTPUT_EXISTS", "禁止覆盖原文件或已有文件，请指定新的 PDF 文件名。")
            output.parent.mkdir(parents=True, exist_ok=True)
            created = False
            try:
                with open(self.current(state), "rb") as source, open(output, "xb") as target:
                    created = True
                    shutil.copyfileobj(source, target)
                reader = verify_pdf(output, state["fields"])
            except Exception:
                if created:
                    output.unlink(missing_ok=True)
                raise
            return {"review_id": rid, "revision": state["revision"], "path": str(output), "sha256": digest(output), "pages": len(reader.pages), "verified": True, "message": "已另存副本并重新打开校验；请使用外部阅读器核对交付文件。"}


HELP = {
    "message": "PDF阅览与批注助手使用本机 PDF 库与页面 PNG 预览，不依赖 MCP App。先 status，再 list_pdfs/open；修改先 plan，展示预览并等待用户确认，再 apply，最后 save_as。",
    "actions": ACTIONS,
    "examples": {
        "open": {"path": "sample.pdf"},
        "preview": {"review_id": "open 返回值", "pages": [1], "scale": 1.25},
        "search": {"review_id": "open 返回值", "query": "付款期限"},
        "plan": {"review_id": "open 返回值", "expected_revision": 0, "commands": [{"action": "highlight_text", "page": 1, "text": "付款期限"}]},
        "apply": {"review_id": "open 返回值", "expected_revision": 0, "plan_id": "plan 返回值", "confirmed": True},
        "save_as": {"review_id": "open 返回值", "expected_revision": 1, "path": "sample-annotated.pdf"},
    },
    "coordinates": "可见页面左上角为原点，单位 PDF 点。矩形为 [x,y,width,height]。",
    "annotation_types": sorted(TYPES),
    "limitations": "仅处理指定工作目录内的文件；不做 OCR、文档摘要、实时拖拽 UI 或密码学数字签名；不覆盖原稿或已有文件。",
}


def run(inputs):
    try:
        if not isinstance(inputs, dict):
            fail("BAD_INPUT", "输入必须是 JSON 对象。")
        action = inputs.get("action")
        if action not in ACTIONS:
            fail("UNSUPPORTED_ACTION", "不支持该操作，请先调用 help。")
        if action == "help":
            return {"ok": True, "version": VERSION, **HELP}
        if action == "status":
            versions = dependencies()
            return {"ok": True, "version": VERSION, "ready": all(versions.values()), "python": sys.executable, "dependencies": versions, "message": "依赖已就绪。" if all(versions.values()) else "请安装随包 requirements.txt，或设置 WORKSWARM_PDF_PYTHON；本工具不自动安装软件。"}
        payload = inputs.get("payload", {})
        if not isinstance(payload, dict):
            fail("BAD_INPUT", "payload 必须是对象。")
        libs()
        engine = Engine(inputs.get("workspace_dir"))
        result = getattr(engine, action)(payload)
        return {"ok": True, "version": VERSION, **result}
    except ReviewError as exc:
        return {"ok": False, "error": {"code": exc.code, "message": exc.message}}
    except FileNotFoundError:
        return {"ok": False, "error": {"code": "NOT_FOUND", "message": "所需文件或计划不存在，请重新读取当前审阅状态。"}}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {"ok": False, "error": {"code": "INVALID_DATA", "message": "参数或审阅记录格式不正确，请先 help 或重新 open。"}}
    except Exception as exc:
        return {"ok": False, "error": {"code": "PDF_OPERATION_FAILED", "message": "PDF 操作未完成，请检查文件、依赖和工作目录权限。", "exception_type": type(exc).__name__}}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    raw = sys.stdin.buffer.read(256001)
    if len(raw) > 256000:
        result = {"ok": False, "error": {"code": "INPUT_LIMIT", "message": "输入超过 256 KB。"}}
    else:
        try:
            result = run(json.loads(raw.decode("utf-8")))
        except (ValueError, UnicodeError):
            result = {"ok": False, "error": {"code": "INVALID_JSON", "message": "请通过标准输入传入 UTF-8 JSON。"}}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
