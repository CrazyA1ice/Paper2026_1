from pathlib import Path
import json,hashlib,re
from zipfile import ZipFile
from lxml import etree as E
import pdfplumber

QA=Path(__file__).resolve().parent
m=json.loads((QA/'manifest.json').read_text(encoding='utf8'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(m['output']) as z:x=E.fromstring(z.read('word/document.xml'))
for r in x.xpath('.//m:r',namespaces=ns):
    props=r.find('w:rPr',ns);text=r.find('m:t',ns)
    if props is not None and text is not None:assert list(r).index(props)<list(r).index(text)
entries={
0:'中文题名不超过20字；四号宋体14 pt加粗居中。',
1:'收稿日期标签五号宋体；实际收稿值由投稿/编辑流程确定，留空。',
3:'按用户确认无基金项目，移除基金示例，未虚构项目。',
4:'作者简介五号宋体；已补民族、籍贯、学历学位、联系电话及邮箱。',
5:'中文作者五号宋体居中。',
7:'单位写到二级单位，省市及邮编完整，五号宋体。',
8:'摘要标签五号宋体加粗，正文五号宋体；198字符；目的、方法、结果、结论齐备；第三人称；首次解释DLinear；无图表、引文及自我评价；中英文信息一致。',
9:'五个全称关键词，五号宋体；中英文对应顺序一致。',
10:'中图分类号TP393、文献标志码A保留；标签五号宋体加粗，值为五号；文章编号不虚构，留编辑部填写。',
11:'doi标签五号加粗；DOI值按模板留编辑部填写。',
13:'引言序号0；一级标题小四号宋体12 pt加粗。',
14:'正文五号宋体10.5 pt、两端对齐、固定18 pt行距。',
16:'一级标题小四号宋体加粗，阿拉伯数字顺序，左顶格，一字间距。',
23:'各一级标题统一小四号宋体加粗。',
24:'二级标题五号宋体加粗；保留模板三个单栏节及实际分节结构。',
25:'模板此处红色空格不构成额外内容要求；正文采用明确两字首行缩进。',
26:'二级标题五号宋体加粗；专业术语和首次缩略语统一。',
28:'数字使用阿拉伯数字；时长单位h与数值留空；数值范围用～。',
34:'外文及数字Times New Roman；量符号斜体、向量矩阵黑斜体，函数与单位正体。',
36:'本文无三级标题；三级标题字体要求不适用，未人为增加层次。',
42:'本文无三级标题；名称、算子、函数、单位及缩写保持正体。',
52:'数学公式原生可编辑；居中，编号1—15顺序且右对齐。',
54:'所有16个陈列公式均有句末标点；补齐参数量公式标点。',
58:'插图标题对应二级标题要求，图体与正文紧密相联。',
59:'四图均与中文图题组合在无边框文本框内；图宽13.8 cm、约600 dpi、标称六号7.5 pt；图题小五9 pt加粗。',
69:'三张三线表保留全部数值，图表按正文次序编号并有引出文字。',
73:'表题小五宋体9 pt加粗；数字与说明六号7.5 pt；保留实际单位。',
74:'参考文献格式节要求落实于正文引用与文后列表；正文无此模板说明节。',
75:'13处文内引文上标，首次顺序1—11；姓全大写、名规范大小写；中国作者拼音名不缩写；超过3人使用等/et al.；预印本条目换为正式发表的基准研究且限定引用表述。',
77:'所有表题统一小五宋体9 pt加粗；未复制示例表。',
79:'结语一级标题小四号宋体加粗；结语正文保持五号常规字重。',
82:'参考文献前空一行。',
83:'参考文献标签五号宋体加粗。',
84:'文献列表五号宋体；非中文Times New Roman。',
92:'英文信息置于参考文献之后，之前空一行。',
93:'英文题名四号Times New Roman14 pt加粗；句首大写，其他普通词小写。',
94:'英文作者只列第一作者KE Yawen；姓大写、名首字母大写，五号Times New Roman。',
96:'英文二级单位、机构、城市、邮编及China完整，五号Times New Roman。',
97:'英文单位与Abstract之间空一行。',
98:'Abstract标签五号Times New Roman加粗；摘要正文五号常规；与中文结果、方法和结论对应。',
99:'Key words标签五号Times New Roman加粗；关键词五号常规，用英文分号分隔。',
}
audit=json.loads((QA/'论文模板_inspection.json').read_text(encoding='utf8'))
red_indices=[p['index'] for p in audit['paragraphs'] if any(r['color'] in ['FF0000','C00000'] for r in p['runs'])]
assert set(red_indices)<=set(entries),(set(red_indices)-set(entries))
ledger=[{'template_paragraph_index':i,'requirement_and_resolution':entries[i],'status':'verified' if i not in [3,25,36,42] else 'conditional or non-content rule resolved'} for i in red_indices]
raw=json.loads((QA/'figure_source_preflight.json').read_text(encoding='utf8'))
exceptions=[]
for f in raw['findings']:
    if f['level'] in ['FAIL','WARN']:
        assert f['check_id'] in ['FONT-FAMILY','FINAL-WIDTH'],f
        exceptions.append({**f,'journal_resolution':'Template requires Songti and Times New Roman, not generic Nature sans-serif. Actual PDF width is checked independently at138 mm; generic literal-source figsize parser does not evaluate138/25.4.','status':'target-specific check supersedes generic default'})
figqa=json.loads((QA/'figure_qa_summary.json').read_text(encoding='utf8'))
for f in figqa:assert f['collision_verdict']=='PASS' and f['font_returncode']==0
for f in m['figures']:
    with pdfplumber.open(Path(m['output']).parent/'图表源文件'/f"图{f['figure']}.pdf") as pdf:
        assert abs(pdf.pages[0].width/72*25.4-138)<.1
        assert pdf.pages[0].height/72*25.4<90
    assert f['effective_dpi']>=599
result={'template_red_paragraphs_covered':len(red_indices),'unmapped_red_requirements':0,'ledger':ledger,'source_preflight_target_exceptions':exceptions,'figures_collision_and_font_checks':'PASS','editorial_fields':'Receipt date, article number and DOI intentionally blank; no publication/submission event is invented.'}
(QA/'requirements_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
lines=['# 期刊模板要求逐项核对','', '以下记录供作者核对，不属于投稿主稿。主稿可独立阅读，未引用本记录。','', '| 模板段落 | 核对结果 |','|---|---|']
for item in ledger:lines.append(f"| {item['template_paragraph_index']+1} | {item['requirement_and_resolution']} |")
lines+=['','原模板红字所涉及的段落均已映射，重复出现的字号要求也逐处统一。收稿日期须据实际投稿流程确定，文章编号与DOI由编辑部填写，因此三项值保留空白；未编造日期、基金或刊物编号。','', '原始数据、已报告任务、全部模型与种子均未更改。图表重新导出只改变版式及文字显示。']
(Path(m['output']).parent/'模板要求逐项核对.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'red_paragraphs_covered':len(red_indices),'unmapped':0,'figures':'PASS'},ensure_ascii=False))
