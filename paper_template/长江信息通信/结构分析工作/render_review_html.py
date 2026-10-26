"""Offline visual review fallback. HTML pagination is not a Word export."""
from pathlib import Path
from zipfile import ZipFile
import base64
import html
import re
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table

ROOT=Path(__file__).resolve().parent
PATH=ROOT.parent/'自适应多尺度加权的多变量网络流量预测_czxxtx20261026_结构精简稿.docx'
OUT=ROOT/'修订稿版式核对'
OUT.mkdir(exist_ok=True)
doc=Document(PATH)
transform=etree.XSLT(etree.parse(r'C:\Program Files\Microsoft Office\Root\Office16\OMML2MML.XSL'))

def mathml(e):
    result=transform(e)
    root=result.getroot()
    if root is None:
        raise RuntimeError('MathML conversion returned no root')
    # Unprefixed MathML is required when embedding in an HTML document.
    for item in root.iter():
        if isinstance(item.tag,str):
            item.tag=etree.QName(item).localname
    etree.cleanup_namespaces(root)
    root.set('xmlns','http://www.w3.org/1998/Math/MathML')
    root.set('display','inline')
    return etree.tostring(root,encoding='unicode')

def run_html(r):
    chunks=[]
    for e in r:
        if e.tag==qn('w:t'):
            chunks.append(html.escape(e.text or ''))
        elif e.tag==qn('w:tab'):
            chunks.append(' ')
        elif e.tag in [qn('w:br'),qn('w:cr')]:
            chunks.append('<br>')
    text=''.join(chunks)
    props=r.find(qn('w:rPr'))
    if props is not None:
        if props.find(qn('w:b')) is not None: text='<b>'+text+'</b>'
        v=props.find(qn('w:vertAlign'))
        if v is not None and v.get(qn('w:val'))=='superscript': text='<sup>'+text+'</sup>'
    return text

def paragraph(e):
    p=Paragraph(e,doc._body)
    style=p.style.name
    if e.xpath('.//w:drawing'):
        blip=e.xpath('.//a:blip')[0]
        rid=blip.get(qn('r:embed'))
        part=doc.part.related_parts[rid]
        uri='data:'+part.content_type+';base64,'+base64.b64encode(part.blob).decode()
        return '<div class="figure"><img src="'+uri+'"></div>'
    parts=[]
    for c in e:
        if c.tag==qn('w:r'): parts.append(run_html(c))
        elif c.tag==qn('m:oMath'): parts.append(mathml(c))
        elif c.tag==qn('m:oMathPara'):
            parts.extend(mathml(m) for m in c if m.tag==qn('m:oMath'))
        elif c.tag==qn('w:hyperlink'):
            parts.extend(run_html(r) for r in c if r.tag==qn('w:r'))
    inside=''.join(parts)
    if style=='JournalEquation':
        number=re.search(r'（\d+）',p.text)
        math=''.join(mathml(m) for m in e.xpath('./m:oMath | ./m:oMathPara/m:oMath'))
        return '<div class="equation"><div>'+math+'</div><span>'+(number.group() if number else '')+'</span></div>'
    klass=re.sub(r'[^A-Za-z0-9]','',style)
    tag='p'
    if style=='JournalHeading1': tag='h1'
    if style=='JournalHeading2': tag='h2'
    return '<'+tag+' class="'+klass+'">'+inside+'</'+tag+'>'

blocks=[]
for e in doc._element.body:
    if e.tag==qn('w:p'):
        blocks.append(paragraph(e))
    elif e.tag==qn('w:tbl'):
        t=Table(e,doc._body)
        rows=[]
        for idx,row in enumerate(t.rows):
            tag='th' if idx==0 else 'td'
            rows.append('<tr>'+''.join('<'+tag+'>'+html.escape(c.text).replace('\n','<br>')+'</'+tag+'>' for c in row.cells)+'</tr>')
        blocks.append('<table><thead>'+rows[0]+'</thead><tbody>'+''.join(rows[1:])+'</tbody></table>')

css='''
@page { size:210mm 297mm; margin:16.5mm 13.15mm 13.74mm 19.05mm; }
*{box-sizing:border-box} body{margin:0;color:#000;font-family:"Times New Roman","SimSun",serif;font-size:10.5pt;line-height:18pt;}
p{margin:0;text-align:justify;orphans:2;widows:2;overflow-wrap:anywhere;}
.JournalBody{text-indent:21pt;}
.Title{font-family:"SimHei","Times New Roman",serif;font-size:14pt;font-weight:bold;line-height:18pt;text-align:center;margin:0 0 8pt;break-after:avoid;text-indent:0;}
.JournalAuthor,.JournalAffiliation{text-align:center;break-after:avoid;text-indent:0;}
.JournalAbstract{margin-bottom:3pt;text-indent:0;font-size:10.5pt;}
.JournalMetadata{font-size:9pt;text-indent:0;}
h1,h2{font-family:"SimHei","Times New Roman",serif;color:#000;margin:5pt 0;break-after:avoid;line-height:18pt;}
h1{font-size:12pt} h2{font-size:10.5pt;margin:3pt 0;}
.figure{text-align:center;break-inside:avoid;break-after:avoid;margin:3pt 0 0;line-height:0;}
.figure img{width:100%;height:auto;max-width:100%;}
.JournalCaption{text-indent:0;text-align:center;font-size:9pt;line-height:14pt;margin:0 0 4pt;break-inside:avoid;}
table{width:100%;border-collapse:collapse;margin:0 0 5pt;font-size:9pt;line-height:14pt;break-inside:avoid;border-top:1pt solid #000;border-bottom:1pt solid #000;}
thead{border-bottom:.5pt solid #000;display:table-header-group}td,th{padding:3pt 2pt;text-align:center;font-weight:normal;}td:first-child{text-align:left;}
.equation{display:grid;grid-template-columns:1fr 35pt;align-items:center;break-inside:avoid;text-indent:0;margin:3pt 0;min-height:18pt;font-size:10pt;line-height:1.3;}
.equation>div{text-align:center}.equation>span{text-align:right;}math{font-family:"Cambria Math",serif;}
.JournalReferenceHeading{font-family:"SimHei",serif;font-weight:bold;break-after:avoid;margin-top:5pt;}
.JournalReference{font-size:9pt;line-height:14pt;text-indent:-14pt;margin-left:14pt;}
sup{font-size:7pt;line-height:0;}
'''
html_text='<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><title>修订稿版式核对</title><style>'+css+'</style></head><body>'+''.join(blocks)+'</body></html>'
(OUT/'review.html').write_text(html_text,encoding='utf-8')
print(OUT/'review.html')
