from pathlib import Path
import json,importlib.util
from root_edits import EDITS as ROOT_EDITS
QA=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('previous_replacements',QA.parent/'v74_aigc/replacements.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
TERMS=previous.TERMS
EDITS=dict(ROOT_EDITS)
method=json.loads((QA/'method_edits.json').read_text(encoding='utf-8'))
for index,record in method.items():
    assert int(index) not in EDITS
    EDITS[int(index)]=[(x['old'],x['new']) for x in record['entries']]
EDITS=dict(sorted(EDITS.items()))
