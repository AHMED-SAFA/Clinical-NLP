import json
import pymupdf as fitz  # PyMuPDF
import pdfplumber
from .config import PROTOCOLS, PROTOCOL_DIR, EXTRACT_DIR, expand


def _md(rows):
    rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in rows if r]
    if not rows:
        return ""
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def extract_protocol(key: str, dpi: int = 120) -> dict:
    meta = PROTOCOLS[key]
    pdf = PROTOCOL_DIR / meta["file"]
    png_dir = EXTRACT_DIR / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    doc, pages = fitz.open(pdf), {}
    with pdfplumber.open(pdf) as pl:
        for p in expand(meta["pages"]):
            page = doc[p - 1]  # PDF cover = page 1
            text = page.get_text("text", sort=True)
            try:
                tables = [
                    t for t in (_md(x) for x in pl.pages[p - 1].extract_tables()) if t
                ]
            except Exception:
                tables = []
            page.get_pixmap(dpi=dpi).save(png_dir / f"{key}_p{p:03d}.png")
            pages[str(p)] = dict(
                page=p,
                text=text,
                tables_md=tables,
                n_chars=len(text),
                n_images=len(page.get_images()),
                inspect_png=len(text) < 400,
            )  # likely flowchart/image page
    out = dict(protocol=key, title=meta["title"], version=meta["version"], pages=pages)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    (EXTRACT_DIR / f"{key}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), "utf-8"
    )
    return out
