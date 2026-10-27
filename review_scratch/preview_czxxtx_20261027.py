"""Secondary offline preview. It does not certify native Word pagination."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'paper_template'/'长江信息通信'
WORK=BASE/'格式核对工作_20261027'
script=(BASE/'结构分析工作'/'render_review_html.py').read_text(encoding='utf-8')
script=script.replace("ROOT=Path(__file__).resolve().parent",f"ROOT=Path({str(BASE/'结构分析工作')!r})")
script=script.replace("PATH=ROOT.parent/'自适应多尺度加权的多变量网络流量预测_czxxtx20261026_结构精简稿.docx'",f"PATH=Path({str(BASE/'自适应多尺度加权的多变量网络流量预测_czxxtx20261027_格式核对修订稿.docx')!r})")
script=script.replace("OUT=ROOT/'修订稿版式核对'",f"OUT=Path({str(WORK/'secondary_preview')!r})")
script=script.replace("if props.find(qn('w:b')) is not None: text='<b>'+text+'</b>'", "if props.find(qn('w:b')) is not None and props.find(qn('w:b')).get(qn('w:val')) not in ['0','false']: text='<b>'+text+'</b>'\n        if props.find(qn('w:i')) is not None and props.find(qn('w:i')).get(qn('w:val')) not in ['0','false']: text='<i>'+text+'</i>'")
script=script.replace("if v is not None and v.get(qn('w:val'))=='superscript': text='<sup>'+text+'</sup>'", "if v is not None and v.get(qn('w:val'))=='superscript': text='<sup>'+text+'</sup>'\n        if v is not None and v.get(qn('w:val'))=='subscript': text='<sub>'+text+'</sub>'")
script=script.replace('margin:16.5mm 13.15mm 13.74mm 19.05mm','margin:15.01mm 20.00mm 15.01mm 20.00mm')
script=script.replace('line-height:18pt','line-height:1.5')
script=script.replace('font-family:"SimHei","Times New Roman",serif','font-family:"Times New Roman","SimSun",serif')
script=script.replace('h1{font-size:12pt}','h1{font-size:14pt}')
script=script.replace('font-size:9pt;line-height:14pt;margin:0 0 4pt','font-size:10.5pt;line-height:1.5;margin:0 0 3pt')
script=script.replace('.figure img{width:100%;height:auto;max-width:100%;}', '.figure img{width:138mm;height:auto;max-width:100%;}')
script=script.replace('.JournalReference{font-size:9pt;line-height:14pt;text-indent:-14pt;margin-left:14pt;}', '.JournalReference{font-size:10.5pt;line-height:1.5;text-indent:-18pt;margin-left:18pt;break-inside:avoid;}')
script=script.replace('font-family:"SimHei",serif;font-weight:bold;break-after:avoid;margin-top:5pt;', 'font-family:"Times New Roman","SimSun",serif;font-weight:bold;font-size:14pt;break-after:avoid;margin-top:5pt;')
script=script.replace('sup{font-size:7pt;line-height:0;}', 'sup,sub{font-size:7pt;line-height:0;}')
exec(compile(script,str(__file__),'exec'))
js=(BASE/'结构分析工作'/'print_review.cjs').read_text(encoding='utf-8')
js=js.replace("const dir=path.join(__dirname,'修订稿版式核对');",f"const dir={str(WORK/'secondary_preview')!r};")
(WORK/'print_secondary_preview.cjs').write_text(js,encoding='utf-8')
