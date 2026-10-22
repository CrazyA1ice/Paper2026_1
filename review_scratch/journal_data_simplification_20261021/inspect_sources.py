from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
import pdfplumber
from zipfile import ZipFile

sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
QA=Path(__file__).resolve().parent
old=ROOT/'review_scratch/changchun_revision'
manifest=json.loads((old/'sample_manifest.json').read_text(encoding='utf8'))
poppler=next(Path(r'C:\Users\Quant\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler').rglob('pdftoppm.exe'))
records=[]
for item,pages in zip(manifest,[[5,6],[5,6],[3,4]]):
    path=Path(item['file'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    with pdfplumber.open(path) as pdf:
        assert len(pdf.pages)==item['pages']
        texts=[p.extract_text() or '' for p in pdf.pages]
        (QA/f'sample_{item["id"]}_full.txt').write_text('\n\n'.join(f'PDF PAGE {i+1}\n{t}' for i,t in enumerate(texts)),encoding='utf8')
    for n in pages:
        target=QA/f'sample_{item["id"]}_page_{n}'
        subprocess.run([str(poppler),'-f',str(n),'-l',str(n),'-r','140','-singlefile','-png',str(path),str(target)],check=True,capture_output=True)
    records.append({**item,'reviewed_experimental_pdf_pages':pages})

data=[]
for ds in ['abilene','geant']:
    path=ROOT/f'abilene_forecasting/data/processed/{ds}_1hour.npz'
    with np.load(path) as raw:
        splits={k:raw[k] for k in ['train','val','test']}
        assert all(np.isfinite(v).all() for v in splits.values())
        assert np.max(np.abs(splits['train'].mean(axis=0)))<1e-5
        assert np.max(np.abs(splits['train'].std(axis=0)-1))<1e-4
        assert len(set(raw['active_indices'].tolist()))==splits['train'].shape[1]
        data.append({'dataset':ds,'shape':{k:list(v.shape) for k,v in splits.items()},'train_max_abs_normalized_mean':float(np.max(np.abs(splits['train'].mean(axis=0)))),'train_max_abs_normalized_sd_error':float(np.max(np.abs(splits['train'].std(axis=0)-1))),'all_finite':True,'original_shape':raw['original_shape'].tolist(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
out={'samples':records,'processed_data':data,'scope':'reporting and evidence allocation; no retraining, re-scoring, observations excluded, or preprocessing changes'}
(QA/'source_inspection.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'samples_verified':len(records),'experimental_pages_rendered':6,'normalized_datasets_verified':2},ensure_ascii=False))
