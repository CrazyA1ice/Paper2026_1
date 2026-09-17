from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_图1折线修订版.docx"
OUTPUT = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_SciPilot图表整合最新版.docx"
FIG_DIR = ROOT / "abilene_forecasting" / "paper_figures"

REPLACEMENTS = {
    29: FIG_DIR / "paper_comic_set" / "P1_方法图解草稿.png",
    89: FIG_DIR / "scipilot_figure_set" / "S1_小样本透明化消融.png",
    96: FIG_DIR / "scipilot_figure_set" / "S2_配对权重消融.png",
    99: FIG_DIR / "scipilot_figure_set" / "S4a_路由权重诊断.png",
    106: FIG_DIR / "scipilot_figure_set" / "S3_频域敏感性原始轨迹.png",
    111: FIG_DIR / "scipilot_figure_set" / "S4b_代表性预测诊断.png",
}

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def clone_info(info: ZipInfo) -> ZipInfo:
    copied = ZipInfo(info.filename, info.date_time)
    copied.compress_type = ZIP_DEFLATED
    copied.comment = info.comment
    copied.extra = info.extra
    copied.create_system = info.create_system
    copied.external_attr = info.external_attr
    copied.internal_attr = info.internal_attr
    copied.flag_bits = info.flag_bits
    return copied


def main() -> None:
    for path in REPLACEMENTS.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    with ZipFile(SOURCE, "r") as source_zip:
        document = etree.fromstring(source_zip.read("word/document.xml"))
        relationships = etree.fromstring(source_zip.read("word/_rels/document.xml.rels"))
        relationship_targets = {
            rel.get("Id"): rel.get("Target")
            for rel in relationships.xpath("/pr:Relationships/pr:Relationship", namespaces=NS)
        }
        paragraphs = document.xpath("/w:document/w:body/w:p", namespaces=NS)
        media_bytes: dict[str, bytes] = {}

        for paragraph_index, figure_path in REPLACEMENTS.items():
            paragraph = paragraphs[paragraph_index]
            blips = paragraph.xpath(".//a:blip", namespaces=NS)
            if len(blips) != 1:
                raise RuntimeError(f"Paragraph {paragraph_index} contains {len(blips)} images")
            relationship_id = blips[0].get(f"{{{NS['r']}}}embed")
            target = relationship_targets[relationship_id]
            media_name = "word/" + target
            media_bytes[media_name] = figure_path.read_bytes()

            with Image.open(figure_path) as image:
                pixel_width, pixel_height = image.size
            extents = paragraph.xpath(".//wp:extent", namespaces=NS)
            if len(extents) != 1:
                raise RuntimeError(f"Paragraph {paragraph_index} has no unique wp:extent")
            width_emu = int(extents[0].get("cx"))
            height_emu = round(width_emu * pixel_height / pixel_width)
            extents[0].set("cy", str(height_emu))
            for shape_extent in paragraph.xpath(".//a:xfrm/a:ext", namespaces=NS):
                shape_extent.set("cx", str(width_emu))
                shape_extent.set("cy", str(height_emu))

        updated_document = etree.tostring(
            document, xml_declaration=True, encoding="UTF-8", standalone=True
        )

        with ZipFile(OUTPUT, "w") as output_zip:
            for info in source_zip.infolist():
                if info.filename == "word/document.xml":
                    payload = updated_document
                elif info.filename in media_bytes:
                    payload = media_bytes[info.filename]
                else:
                    payload = source_zip.read(info.filename)
                output_zip.writestr(clone_info(info), payload)

    print(OUTPUT)


if __name__ == "__main__":
    main()
