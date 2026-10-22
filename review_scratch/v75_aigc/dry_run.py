from pathlib import Path
import importlib.util,sys,types,re,json
sys.stdout.reconfigure(encoding='utf-8')
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
from replacements import EDITS
spec=importlib.util.spec_from_file_location('old_terms',QA.parent/'v74_aigc/replacements.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
mod=types.ModuleType('replacements');mod.EDITS=EDITS;mod.TERMS=old.TERMS
sys.modules['replacements']=mod
source=(QA/'revise.py').read_text(encoding='utf-8').split('changes=[]')[0]
scope={'__file__':str(QA/'revise.py')}
exec(source,scope)
fails=[]
for i,edits in EDITS.items():
    text=''.join(t['text'] for t in scope['tokens'](scope['ps'][i]))
    new=text
    try:
        for a,b in edits:
            assert new.count(a)==1,(a,new.count(a));new=new.replace(a,b,1)
        assert re.findall(r'\d+(?:\.\d+)?',text)==re.findall(r'\d+(?:\.\d+)?',new),'numbers'
        for term in old.TERMS:
            if term.casefold() in text.casefold(): assert term.casefold() in new.casefold(),('term',term)
        scope['apply_new'](scope['ps'][i],new)
    except Exception as error: fails.append({'index':i,'error':str(error)})
print(json.dumps({'validated':len(EDITS)-len(fails),'failures':fails},ensure_ascii=False))
