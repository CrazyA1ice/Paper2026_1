"""Monitor the two fixed workers and produce a complete descriptive result report."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ctypes
import json
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/long_horizon_20261021'
LABELS={'dlinear':'DLinear','dlinear_scale_static':'固定等权','dlinear_scale_global':'全局可学习权重','dlinear_scale_constant_router':'恒定输入路由','dlinear_scale':'本文方法'}

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')

def alive(pid):
    kernel=ctypes.windll.kernel32
    kernel.OpenProcess.restype=ctypes.c_void_p
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle:return False
    code=ctypes.c_ulong()
    ok=kernel.GetExitCodeProcess(ctypes.c_void_p(handle),ctypes.byref(code))
    kernel.CloseHandle(ctypes.c_void_p(handle))
    return bool(ok and code.value==259)

def read_state(index):
    path=OUT/f'worker_{index}.json'
    if not path.exists():return {'worker':index,'status':'starting','done':0}
    for attempt in range(3):
        try:return json.loads(path.read_text(encoding='utf8'))
        except json.JSONDecodeError:
            if attempt==2:raise
            time.sleep(.1)

def make_report():
    status=json.loads((OUT/'analysis_status.json').read_text(encoding='utf8'))
    assert status['complete'] and status['scored_runs']==320
    summary=pd.read_csv(OUT/'summary.csv')
    paired=pd.read_csv(OUT/'paired_reductions.csv')
    seed=pd.read_csv(OUT/'per_seed_scores.csv')
    trends=json.loads((OUT/'trend_check.json').read_text(encoding='utf8'))
    assert len(summary)==40 and len(paired)==64 and len(seed)==320 and len(trends)==16
    assert not seed.duplicated(['dataset','horizon','model','seed']).any()
    assert np.isfinite(seed[['common_mse','common_mae','all_mse','all_mae']]).all().all()
    for _,group in seed.groupby(['dataset','horizon','model']):assert sorted(group.seed.tolist())==list(range(42,50))
    paired['mean_absolute_error_difference']=paired.baseline_mean-paired.proposed_mean
    paired.to_csv(OUT/'paired_reductions.csv',index=False,encoding='utf-8-sig')
    monotonic=sum(row['monotonically_increasing'] for row in trends)
    endpoint=sum(row['change_168_minus_24_percentage_points']>0 for row in trends)
    now=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M 北京时间')
    lines=['# 24至168小时预测补充实验结果','',f'完成时间：{now}。','',
        '本轮已完成240组新训练，并复用80组既有24小时训练记录，共评价320组模型与种子配置。五种模型均保持96小时输入，使用小时采样、原有训练验证测试划分、同一预处理与八个共同种子。主要比较采用能容纳168小时预测的共同起点，Abilene为669个，GÉANT为307个。','',
        '## 对优势随预测时长变化的检查','',
        f'在两个网络、四种对照和两个指标组成的16组比较中，八种子平均相对降幅随24、48、96、168小时依次不减的有{monotonic}组；168小时相对降幅高于24小时的有{endpoint}组。两个计数含义不同，应结合下表逐项判断。此处为预先固定配置下的描述性比较，未进行趋势显著性检验。','',
        '| 数据集 | 对照 | 指标 | 24 h降幅/% | 48 h降幅/% | 96 h降幅/% | 168 h降幅/% | 是否依次不减 |','|---|---|---|---:|---:|---:|---:|---|']
    for row in trends:
        values=' | '.join(f'{x:.2f}' for x in row['mean_reductions_pct'])
        lines.append(f"| {row['dataset']} | {LABELS[row['baseline']]} | {row['metric'].upper()} | {values} | {'是' if row['monotonically_increasing'] else '否'} |")
    lines+=['','相对降幅按每个共同种子分别计算100×（基线误差－本文方法误差）／基线误差，再对八个种子平均。负值表示该配置下本文方法的平均相对误差较高；完整保留所有结果。误差绝对差值另列于paired_reductions.csv。','',
        '## 完整MSE与MAE结果','',
        '表中为种子均值±样本标准差，均在原训练集确定的对数变换与逐变量标准化空间计算。同一预测时长内，各模型的起点、真实目标和变量一致；跨时长的预测起点也一致。每个时长全部有效起点的补充分数保存在同一汇总CSV的all字段。','',
        '| 数据集 | 预测时长/h | 模型 | MSE | MAE |','|---|---:|---|---:|---:|']
    for ds in ['abilene','geant']:
        for horizon in [24,48,96,168]:
            for model,label in LABELS.items():
                row=summary[(summary.dataset==ds)&(summary.horizon==horizon)&(summary.model==model)].iloc[0]
                lines.append(f'| {ds} | {horizon} | {label} | {row.common_mse_mean:.6f}±{row.common_mse_sd:.6f} | {row.common_mae_mean:.6f}±{row.common_mae_sd:.6f} |')
    lines+=['','## 术语与可复核资料','',
        '日周期朴素预测复制最近已观测日周期中相同小时的值，周周期朴素预测复制最近已观测周周期中相同星期和小时的值；其参考周期分别为24与168小时。参考周期与预测范围是不同概念。本轮五种学习模型的长预测时长实验不使用未来真实值进行周期复制。定义参见[Forecasting Principles and Practice](https://otexts.com/fpp2/simple-methods.html)。','',
        'protocol.json固定数据、代码SHA256与训练协议；jobs.json列出新训练配置；各运行文件夹保留检查点、原始预测、真实值、训练日志与完成标记；per_seed_scores.csv保留320组评分和预测文件SHA256；summary.csv、paired_reductions.csv与trend_check.json提供全部汇总。原论文中的24小时全窗口结果与本报告的共同起点评分属于不同评价集合。','',
        '本报告为实际实验结果的自动汇总，尚未将这些新结果写入投稿Word稿。']
    report=OUT/'长预测时长实验结果.md'
    report.write_text('\n'.join(lines)+'\n',encoding='utf8')
    return {'report':str(report),'scored_runs':320,'summary_rows':40,'paired_rows':64,'trend_groups':16,'monotonic_groups':monotonic,'endpoint_improved_groups':endpoint}

def main():
    started=time.time()
    monitor_path=OUT/'monitor_status.json'
    while True:
        states=[read_state(i) for i in (0,1)]
        for state in states:
            if state['status']=='failed':
                write_json(monitor_path,{'status':'needs_attention','reason':'worker_failed','workers':states,'updated_unix':time.time()})
                raise RuntimeError(f"Worker {state['worker']} failed; see its state and training log.")
            if state['status']=='running' and not alive(state['pid']):
                write_json(monitor_path,{'status':'needs_attention','reason':'worker_exited_before_completion','workers':states,'updated_unix':time.time()})
                raise RuntimeError(f"Worker {state['worker']} exited without completion.")
        progress={'status':'training','completed_new_runs':sum(s['done'] for s in states),'total_new_runs':240,'workers':states,'updated_unix':time.time()}
        write_json(monitor_path,progress)
        print(json.dumps({'status':'training','completed_new_runs':progress['completed_new_runs'],'total_new_runs':240},ensure_ascii=False),flush=True)
        if all(s['status']=='complete' for s in states):break
        if time.time()-started>24*3600:
            write_json(monitor_path,{'status':'needs_attention','reason':'monitor_24_hour_limit','workers':states,'updated_unix':time.time()})
            raise TimeoutError('Monitoring reached its 24-hour limit; inspect workers before taking action.')
        time.sleep(30)
    write_json(monitor_path,{'status':'scoring','completed_new_runs':240,'updated_unix':time.time()})
    with (OUT/'final_analysis.log').open('w',encoding='utf8',buffering=1) as log:
        result=subprocess.run([sys.executable,'-u',str(ROOT/'long_horizon_20261021.py'),'analyze'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=7200)
    if result.returncode:
        write_json(monitor_path,{'status':'needs_attention','reason':'analysis_failed','exit_code':result.returncode,'updated_unix':time.time()})
        raise RuntimeError('Final analysis failed; inspect final_analysis.log.')
    report=make_report()
    write_json(monitor_path,{'status':'complete',**report,'updated_unix':time.time()})
    print(json.dumps({'status':'complete',**report},ensure_ascii=False),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    main()
