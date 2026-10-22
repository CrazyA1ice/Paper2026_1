from pathlib import Path
import json
root=Path(r'C:\Users\Quant\Desktop\Paper2026_1');old=root/'review_scratch/v74_manual_audit_20261008';out=root/'review_scratch/v75_presubmission_20261008'
source=(old/'audit_numbers.py').read_text(encoding='utf-8-sig');prefix=source.split("ns={'w':")[0];prefix=prefix.replace("out=root/'review_scratch/v74_manual_audit_20261008'","out=root/'review_scratch/v75_presubmission_20261008'").replace("new=json.loads((out/'v74.json').read_text(encoding='utf-8')); old=json.loads((out/'v73.json').read_text(encoding='utf-8'))",'')
exec(compile(prefix,'fresh_numeric_check','exec'))
result={'run_count':len(rows),'raw_metric_validation_errors':checks,'summary':summary,'paired':paired,'datasets':datasets};(out/'fresh_numerical_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'runs':len(rows),'errors':checks,'core_mse':[p for p in paired if p['seeds']==8 and p['metric']=='mse' and p['baseline'] in ['dlinear_scale_global','dlinear_scale_constant_router']]},indent=2))

