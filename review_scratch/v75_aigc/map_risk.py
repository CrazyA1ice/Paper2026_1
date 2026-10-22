from pathlib import Path
import json,re,sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
norm=lambda t:re.sub(r'\s','',t)
records={}
for v in [74,68]:
    pages=json.loads((QA/f'report_v{v}_pages.json').read_text(encoding='utf-8'))
    para=json.loads((QA/f'v{v}_paragraphs.json').read_text(encoding='utf-8'))
    chars=[];colors=[];numbers=[]
    for p in pages[1:]:
        for s in p['spans']:
            t=norm(s['text']);chars.extend(t);colors.extend([s['color']]*len(t));numbers.extend([p['page']]*len(t))
    text=''.join(chars)
    mapped=[]
    for p in para:
        t=norm(p['text'])
        if len(t)<30 or p['images'] or re.match(r'^(?:\d[.\d]*|图\d|表\d|\[\d+\])',t): continue
        anchor=t[:24]
        start=text.find(anchor)
        if start<0:
            anchor=t[:15];start=text.find(anchor)
        if start<0:
            mapped.append({'index':p['index'],'matched':False,'text':p['protected_text']});continue
        end=start+len(t)
        # Exact matches give reliable paragraph boundaries; formula-containing
        # paragraphs can only provide an approximate color count.
        exact=text[start:end]==t
        if not exact:
            tail=t[-20:];stop=text.find(tail,start)
            if stop>=0 and stop<start+len(t)+250: end=stop+len(tail)
        cc=Counter(colors[start:end])
        mapped.append({'index':p['index'],'matched':True,'exact':exact,'pages':sorted(set(numbers[start:end])),
                       'red':cc[15022389],'orange':cc[16361509],'normal':cc[2171169],
                       'colors':dict(cc),'text':p['protected_text']})
    records[v]=mapped
    print(f'V{v}')
    for p in mapped:
        print(f"P{p['index']:03} page={p.get('pages')} red={p.get('red')} orange={p.get('orange')} normal={p.get('normal')} exact={p.get('exact')} {p['text'][:65]}")
(QA/'risk_mapping.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
