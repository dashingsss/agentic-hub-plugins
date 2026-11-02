"""Render reopened saved PDFs for manual visual QA; not shipped in payload."""
import argparse
import json
from pathlib import Path
import shutil
import pypdfium2 as pdfium

parser = argparse.ArgumentParser()
parser.add_argument("workspace", type=Path)
args = parser.parse_args()
target = args.workspace / "visual-qa"
target.mkdir(exist_ok=True)
for name in ["sample-annotated", "test-form-completed", "shapes-and-stamp"]:
    with pdfium.PdfDocument(args.workspace / (name + ".pdf")) as doc:
        doc.init_forms()
        page = doc[0]
        bitmap = page.render(scale=1.25, draw_annots=True)
        image = bitmap.to_pil()
        image.save(target / (name + ".png"))
        image.close()
        bitmap.close()
        page.close()
for state_path in (args.workspace / ".pdf-review").glob("*/state.json"):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    source = Path(state["source"]).stem
    if source in {"rotated", "cropped"}:
        png = next(state_path.parent.glob("plans/*/page-1-1.25.png"))
        shutil.copyfile(png, target / (source + ".png"))
print(target)
