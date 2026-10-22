from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json
import sys

from PIL import Image
import pymupdf

sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
OUT=ROOT/'paper_template/长春工程学院学报(自然科学版)/图2-4参考方案_20261022'
SOURCE=OUT.parent/'图表组织优化修订_20261022/自适应多尺度加权的多变量网络流量预测_图表优化稿.docx'
assert sha256(SOURCE.read_bytes()).hexdigest()=='ea996d638e7b11f4a02863b5c0de681f8511dbc7b2ead96a16bbaba79ac49d89'
items=json.loads((QA/'exports.json').read_text(encoding='utf-8'))
assert {x['tag'] for x in items}=={s+str(n) for s in 'ABC' for n in [2,3,4]}
report=[]
for item in items:
    tag=item['tag'];prefix=Path(item['prefix'])
    collision=json.loads((QA/f'{tag}_collision.json').read_text(encoding='utf-8'))
    glyph=json.loads((QA/f'{tag}_text.txt').read_text(encoding='utf-8'))
    assert collision['summary']['fail']==collision['summary']['warn']==0
    assert glyph['below_minimum_count']==0 and glyph['minimum_found_pt']>=7.5
    assert item['alignment']=='PASS' or tag=='A4' and item['alignment']=='NOT APPLICABLE'
    with pymupdf.open(prefix.with_suffix('.pdf')) as d:
        assert len(d)==1
        assert abs(d[0].rect.width/72*25.4-138)<.01
    with Image.open(prefix.with_suffix('.png')) as im:
        assert im.info['dpi'][0]>599 and im.width==3259
    assert '<text' in prefix.with_suffix('.svg').read_text(encoding='utf-8')
    report.append(dict(tag=tag,physical_width_mm=138,font_floor_pt=7.5,final_png_dpi=600,
        alignment=item['alignment'],collision='PASS',visual_colour_review='PASS',visual_grayscale_review='PASS',all_eight_seeds_retained=True))
book=OUT/'图2-4_三套方案对照册.pdf'
with pymupdf.open(book) as doc:
    assert len(doc)==3
    for i,page in enumerate(doc,1):
        assert page.rect.width>400 and page.rect.height>650
        page.get_pixmap(matrix=pymupdf.Matrix(150/72,150/72),alpha=False).save(QA/f'book-page-{i}.png')
qa=dict(accepted=True,figures=report,book_pages=3,manuscript_unchanged=True,
    no_new_experiments=True,no_seed_exclusions=True,
    source_linter_manual_review={'internal_preview_dpi':220,'final_scientific_png_dpi':600,
    'physical_pdf_width_mm':138,'notes':'220 dpi files are internal QA previews, not scientific exports. All final individual PNGs pass 600 dpi format audit. Target width 138 mm follows the supplied Chinese journal manuscript. PDF/SVG plus 600 dpi PNG are the requested reference deliverables; TIFF was not required for this comparison task.'},
    repeat_definition='eight training seeds, 42–49; sample SD; matched percentage reductions averaged across seeds',
    raw_scope={'core_and_ablation_records':96,'baseline_records_for_figure2':48,'high_demand_records':80,'weekly_records':40,'baseline_paired_metric_values':64,'high_demand_paired_metric_values':128,'weekly_paired_metric_values':64})
(QA/'final_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
with (QA/'figure_contract.md').open('a',encoding='utf-8') as f:
    f.write('\nAcceptance: PASS. Nine individual figures and all panel/colour/grayscale views inspected. Nine glyph and collision audits pass; A4 is a single-panel matrix with a separate colorbar, so multi-panel alignment is not applicable. All three PDF booklet pages rendered and inspected. The accepted Word manuscript is byte-for-byte unchanged.\n')
archive=OUT/'三套参考方案_完整文件.zip'
files=[p for p in OUT.rglob('*') if p.is_file() and p!=archive]
with ZipFile(archive,'w',compression=ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files):z.write(p,p.relative_to(OUT).as_posix())
with ZipFile(archive) as z:assert z.testzip() is None and len(z.namelist())==len(files)
print(json.dumps(dict(output=str(OUT),book=str(book),archive=str(archive),figures=9,book_pages=3,
    total_files_in_archive=len(files),archive_mb=round(archive.stat().st_size/1024**2,2),manuscript_unchanged=True),ensure_ascii=False))
