from pathlib import Path

QA = Path(__file__).resolve().parent
script = (QA.parent / 'v66_aigc_review/build_report.py').read_text(encoding='utf-8')
script = script.replace('v66', 'v67').replace('v65', 'v66').replace('2026.10.03v66', '2026.10.04v66')
script = script.replace('个高风险段落中的', '个被标记段落（23个高风险、2个中风险）中的')
script = script.replace('本次修改日期另存为2026.10.04v67.docx', '本次修改日期另存为2026.10.04v67.docx')
script = script.replace('v66的AIGC率为50.9%，AI特征字符数4881，总字符数9589；前部20%、中部60%、后部20%的分区AIGC率分别为24.5%、56.7%、60.8%。报告编号为PAPERPURE20261004111455，检测时间为2026-10-04 11:14:55。上一份v64报告为51.8%，本次下降0.9个百分点。',
                        'v66的AIGC率为47.8%，AI特征字符数4566，总字符数9557；前部20%、中部60%、后部20%的分区AIGC率分别为24.9%、51.6%、60.5%。报告编号为PAPERPURE20261004122224，检测时间为2026-10-04 12:22:24。上一份v66报告为50.9%，本次下降3.1个百分点。')
# The previous report was v65; the global version shift above also changed that historical label.
script = script.replace('上一份v66报告为50.9%', '上一份v65报告为50.9%')
script = script.replace('本轮仅处理报告标记的正文句式。', '本轮仅处理高风险和中风险的正文句式。已不再标红的尺度构造公式前说明、权重共享和图4预测行为分析保持v66原文。')
script = script.replace('应用讨论：按观测更新、窗口构造、预测、量纲恢复及链路需求分析组织句子，未写成已经部署的应用实验。',
                        '应用讨论：用预测范围说明用途，再交代观测更新、窗口构造、量纲恢复及链路需求分析，未写成已经部署的应用实验。')
script = script.replace('净减少{audit["modified_text_chars_before"]-audit["modified_text_chars_after"]}',
                        '净增加{audit["modified_text_chars_after"]-audit["modified_text_chars_before"]}')
script = script.replace('平均句长降低、句长变化增加，未引入口语或网络用语；长度相近的段落组数量未变。',
                        '句长与句长变化的实际数值见上表，未引入口语或网络用语；长度相近的段落组数量未变。')
script = script.replace('len(indices) == 28 and len(changes) == 34', 'len(indices) == 25 and len(changes) == 30')
script = script.replace("assert all(records[i]['risk'] == '高风险' for i in indices)",
                        "assert Counter(records[i]['risk'] for i in indices) == {'高风险': 23, '中风险': 2}")
(QA / 'build_report.py').write_text(script, encoding='utf-8')
print('Prepared comparison report builder')
