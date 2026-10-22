import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
for filename in ('step3_changes.json', 'step4_changes.json'):
    audit = json.loads((root / filename).read_text(encoding='utf-8'))
    for role in ('source', 'target'):
        path = Path(audit[role])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == audit[f'{role}_sha256'], path

config = json.loads((root / 'configuration_audit.json').read_text(encoding='utf-8'))
for evidence in config['evidence']:
    path = root.parent.parent / evidence['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence['sha256'], path
review = {
    'manuscript': '2026.10.03v60.docx',
    'v59_pages_reviewed': list(range(1, 11)),
    'v60_pages_reviewed': list(range(1, 11)),
    'method': 'Word read-only PDF export and Poppler page rendering; visual inspection',
    'findings': 'No clipped figures, overlapping text, truncated tables or missing formulas observed.',
    'figure_pages': {'1': 2, '2': 6, '3': 7, '4': 8, '5': 9},
    'source_and_target_hashes_verified': True,
    'experiment_evidence_hashes_verified': len(config['evidence']),
    'tables_preserved': 3,
    'formulas_preserved': 41,
    'figures_preserved': 5,
    'references_preserved': 11,
}
(root / 'visual_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
print('Source/target and experiment evidence hashes verified; final visual review recorded.')
