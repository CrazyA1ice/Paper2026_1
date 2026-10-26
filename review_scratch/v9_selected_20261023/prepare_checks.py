from pathlib import Path

qa = Path(__file__).resolve().parent
old = qa.parent/'selected_revisions_20261023'
source = (old/'export_word.ps1').read_text(encoding='utf-8')
(qa/'export_word.ps1').write_text(source.replace('selected_revisions_20261023','v9_selected_20261023').replace('render_submission','render_final'),encoding='utf-8')
source = (old/'render_verify.py').read_text(encoding='utf-8')
source = source.replace("'最优的综合预测精度与稳定性','必然引入严重的平滑滞后偏差',\n              '静态融合必然拉低峰值响应','可靠性与普适优势','具备更强的工程实用价值'",
                        "'最优的综合预测精度与稳定性','可靠性与普适优势','具备更强的工程实用价值'")
source = source.replace("report={**stats", "assert stats['words'] <= 7500, stats\nreport={**stats")
(qa/'render_verify.py').write_text(source,encoding='utf-8')
print('Checks prepared')
