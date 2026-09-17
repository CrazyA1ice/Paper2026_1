from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(r"C:\Users\Quant\Desktop\Paper2026_1")
SOURCE = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_图1重绘版.docx"
OUTPUT = ROOT / "word_output" / "基于自适应多尺度加权的多变量网络流量预测方法_图1折线修订版.docx"
FIGURE = ROOT / "abilene_forecasting" / "paper_figures" / "exports" / "fig1_method_schematic.png"
TARGET = "word/media/image1.png"


def main() -> None:
    figure_bytes = FIGURE.read_bytes()
    with ZipFile(SOURCE, "r") as source_zip, ZipFile(OUTPUT, "w", ZIP_DEFLATED) as output_zip:
        names = source_zip.namelist()
        if TARGET not in names:
            raise RuntimeError(f"Missing expected Figure 1 asset: {TARGET}")
        for item in source_zip.infolist():
            payload = figure_bytes if item.filename == TARGET else source_zip.read(item.filename)
            output_zip.writestr(item, payload)
    print(OUTPUT)


if __name__ == "__main__":
    main()
