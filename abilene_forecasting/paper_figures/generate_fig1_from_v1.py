from __future__ import annotations

import base64
import io
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = Path(__file__).resolve().parent
EXPORT_DIR = FIG_DIR / "exports"
SOURCE_DOCX = REPO_ROOT / "word_output" / "2026.09.19v1.docx"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _paragraph_text(paragraph) -> str:
    return "".join(
        e.text or "" for e in paragraph.iter() if e.tag.endswith("}t")
    )


def _extract_v1_figure1() -> Image.Image:
    with ZipFile(SOURCE_DOCX) as z:
        document = ET.fromstring(z.read("word/document.xml"))
        relationships = ET.fromstring(z.read("word/_rels/document.xml.rels"))
        body = document.find("w:body", NS)
        paragraphs = body.findall("w:p", NS)

        caption_index = next(
            i
            for i, paragraph in enumerate(paragraphs)
            if _paragraph_text(paragraph).strip() == "图1 自适应多尺度预测框架"
        )

        figure_paragraph = None
        for i in range(caption_index - 1, max(-1, caption_index - 5), -1):
            if any(e.tag.endswith("}blip") for e in paragraphs[i].iter()):
                figure_paragraph = paragraphs[i]
                break
        if figure_paragraph is None:
            raise RuntimeError("Could not locate Figure 1 in 2026.09.19v1.docx")

        blip = next(
            e for e in figure_paragraph.iter() if e.tag.endswith("}blip")
        )
        relationship_id = blip.get("{" + NS["r"] + "}embed")
        relationship = next(
            e for e in relationships if e.get("Id") == relationship_id
        )
        target = relationship.get("Target")
        raw = z.read("word/" + target)

    return Image.open(io.BytesIO(raw)).convert("RGB")


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError(
        "Noto CJK font not found. Install fonts-noto-cjk before generating Figure 1."
    )


def _center_text(draw: ImageDraw.ImageDraw, box, text: str, font) -> None:
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (x0 + x1 - width) // 2
    y = (y0 + y1 - height) // 2 - 2
    draw.text((x, y), text, font=font, fill="black")


def build_v1_based_figure() -> Image.Image:
    """
    Modify the Figure 1 embedded in 2026.09.19v1.docx rather than redesigning it.

    Preserved from v1:
      - overall canvas, title, input/preprocessing blocks;
      - three scale lanes;
      - DLinear expert and scale-prediction blocks;
      - weighted-fusion/output blocks;
      - router placement, experimental-validation panel and legend.

    Changed for the second-stage manuscript:
      - remove the three frequency-gating blocks;
      - connect each scale directly to its DLinear expert;
      - update router capitalization;
      - replace obsolete validation labels with the current experiment design.
    """
    image = _extract_v1_figure1()
    if image.size != (1404, 787):
        raise RuntimeError(
            f"Unexpected v1 Figure 1 size {image.size}; expected (1404, 787)."
        )

    draw = ImageDraw.Draw(image)

    # Remove the original three frequency-gating blocks and their short arrows.
    draw.rectangle([497, 103, 703, 441], fill="white")

    # Preserve the v1 lane positions and directly connect scale construction
    # to the corresponding DLinear expert.
    for y in (157, 274, 391):
        draw.line([(496, y), (700, y)], fill="black", width=2)
        draw.polygon([(704, y), (692, y - 7), (692, y + 7)], fill="black")

    # Keep the original router box and location, only standardize Softmax spelling.
    router_box = (588, 465, 817, 554)
    draw.rounded_rectangle(
        router_box, radius=12, fill="white", outline="black", width=4
    )
    router_font = _font(26)
    router_lines = ["样本级路由器", "Softmax权重"]
    line_boxes = [draw.textbbox((0, 0), t, font=router_font) for t in router_lines]
    heights = [b[3] - b[1] for b in line_boxes]
    y = (router_box[1] + router_box[3] - (sum(heights) + 4)) // 2 - 2
    for text, bbox, height in zip(router_lines, line_boxes, heights):
        width = bbox[2] - bbox[0]
        x = (router_box[0] + router_box[2] - width) // 2
        draw.text((x, y), text, font=router_font, fill="black")
        y += height + 4

    # Preserve the original four validation slots but update them to the
    # current two-dataset / external-baseline / eight-seed evidence structure.
    validation_font = _font(24)
    validation_boxes = [
        ((294, 646, 487, 739), "外部基线对比"),
        ((501, 646, 691, 739), "固定/自适应"),
        ((710, 646, 908, 739), "8种子稳定性"),
        ((926, 646, 1120, 739), "路由与预测"),
    ]
    for box, label in validation_boxes:
        draw.rounded_rectangle(
            box, radius=12, fill="white", outline="#333333", width=2
        )
        _center_text(draw, box, label, validation_font)

    return image


def generate() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    image = build_v1_based_figure()

    png_path = EXPORT_DIR / "fig1_method_schematic.png"
    tiff_path = EXPORT_DIR / "fig1_method_schematic.tiff"
    pdf_path = EXPORT_DIR / "fig1_method_schematic.pdf"
    svg_path = EXPORT_DIR / "fig1_method_schematic.svg"

    image.save(png_path, dpi=(600, 600))
    image.save(tiff_path, dpi=(600, 600), compression="tiff_lzw")
    image.save(pdf_path, "PDF", resolution=600.0)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", dpi=(600, 600))
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    width, height = image.size
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<image width="{width}" height="{height}" '
        f'xlink:href="data:image/png;base64,{encoded}"/>'
        f'</svg>'
    )
    svg_path.write_text(svg, encoding="utf-8")

    print(png_path)


if __name__ == "__main__":
    generate()
