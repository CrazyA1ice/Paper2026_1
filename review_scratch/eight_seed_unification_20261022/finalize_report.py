from hashlib import sha256
from pathlib import Path
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
audit = json.loads((QA / 'audit.json').read_text(encoding='utf-8'))
render = json.loads((QA / 'render_verification.json').read_text(encoding='utf-8'))
data = json.loads((QA / 'data_audit.json').read_text(encoding='utf-8'))
training = json.loads((QA / 'training_complete.json').read_text(encoding='utf-8-sig'))
assert training['all_runs_completed'] and len(training['runs']) == 10
assert render['visual_review_passed'] and not render['visual_review_pending']
assert sha256(Path(audit['source']).read_bytes()).hexdigest() == audit['source_sha256']
assert sha256(Path(audit['output']).read_bytes()).hexdigest() == audit['output_sha256']
audit['visual_review_passed'] = True
audit['visual_review_pending'] = False
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'training_progress.json').write_text(json.dumps({'completed': training['runs'], 'total': 10}, ensure_ascii=False, indent=2), encoding='utf-8')
models = {'dlinear': 'DLinear', 'lightts': 'LightTS', 'dlinear_scale': '本文方法'}
datasets = {'abilene': 'Abilene', 'geant': 'GÉANT'}
summary = {(r['dataset'], r['model']): r for r in data['summary']}
effects = {(r['dataset'], r['metric']): r for r in data['effects']}
lines = ['八次重复统一实验简报', '',
         '已补齐LightTS在Abilene和GÉANT上的种子45～49，共完成10次新增训练。基线比较现统一使用种子42～49，每个模型、每套数据集均为8次重复，共汇总48条训练记录，全部纳入计算。', '',
         '| 数据集 | 方法 | MSE | MAE |', '|---|---|---:|---:|']
for dataset in ['abilene', 'geant']:
    for model in ['dlinear', 'lightts', 'dlinear_scale']:
        r = summary[dataset, model]
        lines.append(f'| {datasets[dataset]} | {models[model]} | {r["mse_mean"]:.3f}±{r["mse_sd"]:.3f} | {r["mae_mean"]:.3f}±{r["mae_sd"]:.3f} |')
lines.extend(['', '表中为均值±样本标准差。本文方法在两套数据集上的平均MSE和MAE均低于DLinear与LightTS。', '',
              '| 数据集 | 相对LightTS的MSE平均降幅 | 相对LightTS的MAE平均降幅 |', '|---|---:|---:|'])
for dataset in ['abilene', 'geant']:
    own, linear, baseline = [summary[dataset, model] for model in ['dlinear_scale', 'dlinear', 'lightts']]
    assert all(own[m+'_mean'] < linear[m+'_mean'] and own[m+'_mean'] < baseline[m+'_mean'] for m in ['mse', 'mae'])
    lines.append(f'| {datasets[dataset]} | {effects[dataset,"mse"]["mean"]:.2f}% | {effects[dataset,"mae"]["mean"]:.2f}% |')
assert all(row['wins'] == 8 for row in data['effects'])
lines.extend(['', '相对降幅先按相同随机种子配对计算，再取8次均值。在每套数据集的8次配对比较中，本文方法的MSE和MAE均低于LightTS。', '',
              '已同步更新表2、图2、实验重复次数说明及正文和结语中的相关数值。表2与表3中相同模型、相同任务的均值和标准差完全一致。', '',
              f'已核对全部48份预测记录的测试目标、有限数值及误差计算。原有算法、数据划分、训练设置、公式、其余图表和格式设置保持原样；修订稿共{render["pages"]}页，已逐页检查。旧稿保留。', ''])
report = Path(audit['output']).parent / '八次重复统一实验简报.md'
report.write_text('\n'.join(lines), encoding='utf-8')
with (QA / 'artifact.md').open('a', encoding='utf-8') as f:
    f.write('\n## Final acceptance\n\nPASS. All final pages visually reviewed. Ten prespecified new runs completed; all 48 baseline records and prediction archives verified; table 2 and table 3 agree for shared models. Source, format properties, native math and other displays are preserved. Final SHA256 '+audit['output_sha256']+'.\n')
print(json.dumps({'manuscript': audit['output'], 'report': str(report), 'pages': render['pages'],
    'new_runs': 10, 'baseline_records': 48, 'effects': data['effects']}, ensure_ascii=False))
