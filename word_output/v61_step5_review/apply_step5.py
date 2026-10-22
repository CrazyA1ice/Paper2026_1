"""Add the training-defined high-demand forecast analysis to the application discussion."""

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'word_output'
QA = Path(__file__).resolve().parent
ANALYSIS = ROOT / 'abilene_forecasting' / 'results' / 'high_demand_analysis'
spec = importlib.util.spec_from_file_location('previous_edit', OUTPUT / 'v60_steps3_4_review' / 'apply_steps3_4.py')
edit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edit)
edit.QA = QA


def read_csv(name):
    with (ANALYSIS / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    source, target = OUTPUT / '2026.10.03v60.docx', OUTPUT / '2026.10.03v61.docx'
    original, root, members, infos, source_hash = edit.read_source(source, target, 5)
    body = root.find('w:body', edit.NS)
    old = edit.find(body, '图4中各模型在高真实值区间均有低估，')
    method = ('以训练集各OD的第90百分位为高需求阈值，仅评价真实值超过相应阈值的测试预测点。'
              '使用种子42～49和24步预测，在标准化空间统计MAE和平均低估幅度。后者在全部高需求预测点上平均真实值减预测值的正值部分。'
              'Abilene、GÉANT的高需求预测点占比分别为13.61%和13.00%。')
    results = ('按8个种子的均值±标准差汇总，本文方法在Abilene上的高需求MAE和平均低估幅度分别为0.147±0.013、0.137±0.017，'
               '相对全局可学习权重的逐种子平均降幅为17.22%、20.49%，8个种子均改善。'
               'GÉANT两项指标为0.632±0.060、0.577±0.080，平均降幅为3.59%、6.30%，均有6/8个种子改善。')
    interpretation = ('图4的校准分析与上述量化结果共同表明，本文方法的高需求平均绝对误差和低估幅度较低，'
                      'Abilene改善较稳定；GÉANT两项配对改进率的95%置信区间均跨零。'
                      '该结果可为需求上升时段的观察和容量复核提供参考。')
    # Check every rounded value inserted into the manuscript against saved analysis.
    summary, paired = read_csv('summary.csv'), read_csv('paired_reductions.csv')
    for dataset, expected in [('abilene', ('0.147', '0.013', '0.137', '0.017')),
                              ('geant', ('0.632', '0.060', '0.577', '0.080'))]:
        row = next(r for r in summary if r['dataset'] == dataset and r['model'] == 'dlinear_scale')
        actual = tuple(f'{float(row[k]):.3f}' for k in ('mae_mean', 'mae_sd', 'mean_shortfall_mean', 'mean_shortfall_sd'))
        assert actual == expected
    for dataset, values, wins in [('abilene', ('17.22', '20.49'), 8), ('geant', ('3.59', '6.30'), 6)]:
        for metric, expected in zip(('mae', 'mean_shortfall'), values):
            row = next(r for r in paired if r['dataset'] == dataset and r['baseline'] == 'dlinear_scale_global' and r['metric'] == metric)
            assert f'{float(row["mean_reduction_pct"]):.2f}' == expected
            assert int(row['seed_wins']) == wins
    changes = []
    before = edit.text(old)
    edit.replace(old, method, changes, '用预先确定的训练分位阈值补充高需求评价口径。')
    result_node = edit.paragraph(old, results)
    interpretation_node = edit.paragraph(old, interpretation)
    for node in (old, result_node, interpretation_node):
        edit.set_property(node, 'keepNext', val=0)
        edit.set_property(node, 'keepLines', val=0)
        edit.set_property(node, 'widowControl', val=1)
    old.addnext(result_node)
    result_node.addnext(interpretation_node)
    changes.extend([{'before': '原文未报告按训练阈值划分的高需求误差。', 'after': results, 'reason': '加入现有80份预测记录的两项高需求评价结果。'},
                    {'before': before, 'after': interpretation, 'reason': '将图4观察与量化结果衔接，保留数据集差异及应用用途。'}])
    # Every other paragraph must remain identical; tables/formulas/media are checked by the shared verifier.
    before_nodes = original.xpath('//w:body/w:p', namespaces=edit.NS)
    after_nodes = root.xpath('//w:body/w:p', namespaces=edit.NS)
    protected_before = [edit.etree.tostring(p, method='c14n') for p in before_nodes if not edit.text(p).startswith('图4中各模型在高真实值区间均有低估，')]
    changed_nodes = {old, result_node, interpretation_node}
    protected_after = [edit.etree.tostring(p, method='c14n') for p in after_nodes if p not in changed_nodes]
    assert protected_before == protected_after
    edit.save_verify(source, target, 5, original, root, members, infos, source_hash, changes)
    build_report(before, [method, results, interpretation], summary, paired)


def build_report(before, paragraphs, summary, paired):
    audit = json.loads((ANALYSIS / 'analysis_audit.json').read_text(encoding='utf-8'))
    labels = {'dlinear': 'DLinear', 'dlinear_scale_static': '固定等权多尺度',
              'dlinear_scale_global': '全局可学习权重', 'dlinear_scale_constant_router': '恒定输入路由',
              'dlinear_scale': '本文方法', 'mae': 'MAE', 'mean_shortfall': '平均低估幅度'}
    lines = [
        '# v61第五步修改与高需求分析报告', '',
        '日期：2026-10-03。原稿：v60；新稿：v61。', '',
        '## 第五步做了什么', '',
        '按原计划选择一项应用相关分析。本次使用已有H=24预测文件评估高需求时段，没有重新训练，也没有使用H=12或H=48结果。', '',
        '主要结果：本文方法在两个数据集的高需求MAE与平均低估幅度均值均低于四类对照；Abilene的改善较稳定，GÉANT的种子间波动较大。分析补充需求高值区间的预测表现，未测量容量配置、拥塞、能耗或在线部署收益。', '',
        '## 分析设计与数据核对', '',
        '- 高需求定义：各OD在训练集的第90百分位作为固定阈值；真实测试值严格大于本OD阈值的预测点进入评价。阈值在读取模型误差之前确定，不按测试结果调整。',
        '- 使用两个数据集、五种模型、种子42～49的80份预测文件；均为L=96、H=24。逐点核对真实值与预处理测试集重建的滑动窗口完全一致，并复算总体MSE与原运行记录一致。',
        '- 主要指标：标准化空间中的MAE、平均低估幅度。后一指标在全部高需求预测点上平均正值部分max(真实值−预测值,0)，高估点贡献0；不是仅对低估点求平均。',
        '- 补充指标：低估点比例、带符号平均偏差；完整保存，不用于替代主要指标。',
        '- 先在每个种子内计算指标，再汇总8个种子的均值±标准差；改进率先按相同种子配对再平均。区间是自由度7的描述性t区间，未作多重比较校正，不声称所有比较均显著。',
        '- 滑动窗口会在不同预测步重复同一目标小时；点数表示评价覆盖量，不是独立样本数。置信区间只按8个共同种子计算；不把滚动预测点当作独立重复。',
        '- 阈值以逐OD分位数定义高值，可比较同一OD相对历史的需求水平；这些指标不是原始带宽误差，也不代表绝对流量最大的OD或链路负荷。', '',
        '| 数据集 | 测试窗口 | 有效OD | 高需求预测点 | 全部预测点 | 占比 | 不重复的高需求时间×OD点 |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for r in audit['datasets']:
        lines.append(f'| {r["dataset"]} | {r["windows"]} | {r["channels"]} | {r["high_forecast_targets"]} | {r["forecast_targets"]} | {100*r["high_fraction"]:.2f}% | {r["unique_high_time_od_targets"]} |')
    lines += ['', '训练阈值下测试集高需求比例约13%，不必恰为10%；测试分布与训练分布不同，且评价采用24步滑动预测目标。各模型使用完全相同的高需求掩码。', '',
              '## 全部模型结果', '', '| 数据集 | 模型 | 高需求MAE | 平均低估幅度 | 低估点比例 | 带符号平均偏差 |',
              '|---|---|---:|---:|---:|---:|']
    for r in summary:
        formatted = []
        for metric in ('mae', 'mean_shortfall', 'underprediction_fraction', 'signed_bias'):
            multiplier = 100 if metric == 'underprediction_fraction' else 1
            suffix = '%' if multiplier == 100 else ''
            formatted.append(f'{float(r[metric+"_mean"])*multiplier:.3f}±{float(r[metric+"_sd"])*multiplier:.3f}{suffix}')
        lines.append(f'| {r["dataset"]} | {labels[r["model"]]} | ' + ' | '.join(formatted) + ' |')
    lines += ['', 'MAE、低估幅度、偏差均在标准化空间；±为8个种子之间的标准差。各模型仍有较高比例的高需求点低估，因此“低估幅度减小”不能改写成“准确捕捉所有高峰”或“消除容量不足风险”。', '',
              '## 配对改进率与区间', '', '| 数据集 | 对照 | 指标 | 平均降幅 | 95%区间 | 改善种子数 |', '|---|---|---|---:|---|---:|']
    for r in paired:
        lines.append(f'| {r["dataset"]} | {labels[r["baseline"]]} | {labels[r["metric"]]} | {float(r["mean_reduction_pct"]):.2f}% | [{float(r["ci95_low_pct"]):.2f}%, {float(r["ci95_high_pct"]):.2f}%] | {r["seed_wins"]}/8 |')
    lines += ['', 'GÉANT全部配对区间均跨零，平均方向支持高需求评价改善，但稳定性弱于Abilene。Abilene相对全局权重两项平均降幅为17.22%与20.49%，8个种子均改善；相对恒定输入路由分别为7.66%与9.99%，各7/8个种子改善。本文中展示全局权重对照是为了延续核心融合比较，完整报告同时保留另三类对照。', '',
              '## 正文修改前后', '', '修改位置：2.5“运行开销与网络管理应用讨论”，原末段替换为三段；其他正文段落保持原样。', '', '**修改前**', '', before, '', '**修改后**', '']
    for p in paragraphs:
        lines += [p, '']
    lines += ['## 保留与可追溯性', '',
              '- 原有5幅图及尺寸、3张表、41个数学对象、11条参考文献保持不变；所有未涉及段落的XML保持一致。',
              '- 未改变任何原实验数据、训练脚本或检查点；新分析结果写入独立目录；未在正文加入机器硬件配置。',
              '- 分析脚本：`abilene_forecasting/analyze_high_demand.py`。',
              '- 来源核对：`abilene_forecasting/results/high_demand_analysis/analysis_audit.json`，逐项保存162份来源文件的SHA256。',
              '- 分种子结果：`per_seed.csv`；五模型汇总：`summary.csv`；配对降幅：`paired_reductions.csv`；各OD阈值：`abilene_thresholds.csv`、`geant_thresholds.csv`。',
              '- 文稿保护核对：`word_output/v61_step5_review/step5_changes.json`。', '']
    (OUTPUT / '2026.10.03v61_第五步修改对比与高需求分析.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
