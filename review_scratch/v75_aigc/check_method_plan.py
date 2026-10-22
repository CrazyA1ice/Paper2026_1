import json
import re
from pathlib import Path

root = Path(__file__).parent
source = {str(p['index']): p['protected_text'] for p in json.loads((root / 'v74_paragraphs.json').read_text(encoding='utf-8'))}
plan = json.loads((root / 'method_edits.json').read_text(encoding='utf-8'))
checked = []
for index, item in plan.items():
    before = source[index]
    after = before
    for entry in item['entries']:
        assert after.count(entry['old']) == 1, (index, entry['old'], after.count(entry['old']))
        after = after.replace(entry['old'], entry['new'], 1)
    assert re.findall(r'\d+(?:\.\d+)?', before) == re.findall(r'\d+(?:\.\d+)?', after), ('numbers', index)
    assert re.findall(r'⟦M\d+⟧', before) == re.findall(r'⟦M\d+⟧', after), ('math', index)
    assert re.findall(r'\[\d+\]', before) == re.findall(r'\[\d+\]', after), ('citation', index)
    checked.append({'index': int(index), 'before_len': len(before), 'after_len': len(after), 'length_change': round(len(after) / len(before) - 1, 4), 'after': after})
(root / 'method_plan_check.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([ {k: v for k,v in x.items() if k != 'after'} for x in checked], ensure_ascii=False, indent=2))
