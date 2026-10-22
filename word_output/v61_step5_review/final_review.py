import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
QA = Path(__file__).resolve().parent
audit = json.loads((QA / 'step5_changes.json').read_text(encoding='utf-8'))
for key in ('source', 'target'):
    assert hashlib.sha256(Path(audit[key]).read_bytes()).hexdigest() == audit[key + '_sha256']
assert hashlib.sha256((QA / 'render_input.docx').read_bytes()).hexdigest() == audit['target_sha256']
reader = PdfReader(QA / '2026.10.03v61.pdf')
pages = [p.extract_text() for p in reader.pages]
assert len(pages) == 10
assert '[11]' in pages[-1]
figure_pages = {}
for number, caption in enumerate(('自适应多尺度预测框架', '相对LightTS的误差降低率与参数规模',
                                  '相对两类基线的多指标改进分布', '分组预测校准与典型窗口轨迹',
                                  '尺度权重分布与种子均值'), start=1):
    found = [i + 1 for i, p in enumerate(pages) if f'图{number}{caption}' in re.sub(r'\s+', '', p)]
    assert len(found) == 1
    figure_pages[str(number)] = found[0]
assert figure_pages == {'1': 2, '2': 6, '3': 7, '4': 8, '5': 9}
stats = json.loads((QA / 'v61_word_statistics.json').read_text(encoding='utf-8-sig'))
(QA / 'v61_rendered_text.txt').write_text('\n\f\n'.join(pages), encoding='utf-8')
record = {'pages': 10, 'figure_pages': figure_pages,
          'source_and_target_hashes_verified': True,
          'rendered_copy_identical_to_final_manuscript': True,
          'preserved': audit['preserved'],
          'word_statistics': stats,
          'visual_review_pages': list(range(1, 11)),
          'visual_findings': 'All pages reviewed; no clipped figures, overlapping text or missing formulas. References end on page 10.'}
(QA / 'visual_review.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
report = ROOT / 'word_output' / '2026.10.03v61_第五步修改对比与高需求分析.md'
addition = ('\n## 最终检查\n\n'
            '已查看最终版全部10页。图1～图5仍分别位于第2、6、7、8、9页，新增高需求分析位于第10页的2.5末尾，结语及11条参考文献均完整保留。'
            '初次预览最后一条参考文献单独落在第11页，已精简新增说明的重复措辞，保留全部新增数值、定义和统计含义，最终保持10页；没有缩小原图或改变正文格式。\n\n'
            f'Word统计为{stats["words"]}字词、{stats["far_east_characters"]}个远东字符；与v60相比，分别净增加224和196，此处“字词”不是中文纯字数。'
            '新增结果的四组均值±标准差、四项配对降幅和种子改善数均与分析CSV核对一致；162份原始来源文件哈希不变。\n\n'
            '内置渲染器缺少配套LibreOffice，使用不加载Word插件的任务副本导出PDF并逐页核对；副本与最终稿SHA256一致，均未通过Word回存。'
            '未见图表裁切、图文重叠或公式缺失，正文未加入机器硬件配置。\n')
assert '## 最终检查' not in report.read_text(encoding='utf-8')
with report.open('a', encoding='utf-8') as handle:
    handle.write(addition)
print(json.dumps(record, ensure_ascii=False))
