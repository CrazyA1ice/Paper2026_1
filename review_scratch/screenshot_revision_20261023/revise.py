from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import csv
import json
import re
import sys

from lxml import etree as E

sys.stdout.reconfigure(encoding='utf-8')
QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
JOURNAL = ROOT / 'paper_template/长春工程学院学报(自然科学版)'
SOURCE = JOURNAL / '自适应多尺度加权的多变量网络流量预测_ccgcxyxbV3_行文连贯性修订稿.docx'
OUTPUT = JOURNAL / '截图逐项修改_20261023/自适应多尺度加权的多变量网络流量预测_ccgcxyxbV4_截图逐项修改稿.docx'
SOURCE_SHA = '625685542a13f7ec84ad45f82583f258324a47af6fe3c02224c7b59deed95357'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert not OUTPUT.exists() or sha256(OUTPUT.read_bytes()).hexdigest()=='f734d4ad05caa8b050b330716524982ffdf99a63f58688b710e8eff487e864e5', 'Regenerate only the known unreleased draft.'

# These are the supplied screenshot paragraphs, without editorial rewriting.
# Braces mark native inline math and are not part of the visible prose.
TEXT = {
    'abstract': '摘要：针对骨干网小时级源—目的（OD）流量序列兼具高频突发波动与长周期演化趋势、传统多尺度模型参数冗且静态融合易受噪声干扰的问题，提出一种自适应多尺度加权的多变量网络流量预测方法。该方法通过非重叠时间聚合构造多分辨率输入，利用三个参数独立的分解线性专家（DLinear）解耦并提取各尺度下的趋势项与余项特征，进而设计仅含131个参数的轻量级窗口路由网络，提取历史窗口的四维时域统计特征，自适应生成样本级多尺度融合权重。在Abilene和GÉANT真实骨干网数据集上的重复实验表明：在24 h预测任务中，所提方法仅以LightTS模型6.41%和2.17%的参数规模（仅8339个参数），实现了29.80%和46.89%的均方误差（MSE）降幅，相较于单尺度DLinear及静态多尺度融合策略，MSE最高降低4.31%，且在高需求峰点的平均低估误差降低达16.07%。在GÉANT数据集168 h长周期预测任务中，其MSE和平均绝对误差（MAE）较DLinear分别显著降低23.16%和11.16%，展现出优异的精度—复杂度平衡性与工程预测稳健性，可为骨干网容量规划与资源调度提供可靠支撑。',
    'intro1': '在时间结构建模方面，现有研究逐渐从单尺度映射转向多尺度特征提取。Zhou等[5]通过深度回声状态网络开展多尺度流量预测，但循环结构在长序列上的计算开销较大。Zeng等提出的分解线性模型（DLinear）[6]将序列解耦为趋势项和余项并分别映射，以极简结构超越了诸多复杂Transformer模型，但其单一时间分辨率难以同时兼顾小时级流量的局部尖峰与跨日趋势。针对多尺度建模，TimeMixer[7]采用可分解多尺度混合架构，TimesNet公开基准[8]则引入基于多层感知机（MLP）的LightTS处理多维时序。然而，这类通用多尺度模型通常依赖复杂的跨尺度交互层或高维通道映射，模型参数量随OD变量维度急剧膨胀，易在样本有限的网络流量数据上引发过拟合。此外，采用固定权重或全局静态权重的尺度融合策略忽略了流量窗口的时变非平稳性，在流量突变切换期反而会因粗尺度滞后效应拉低预测精度。',
    'intro2': '为突破上述“精度—复杂度”权衡困境并克服静态融合的滞后干扰，本文将三个独立的多分辨率DLinear专家与四维统计特征驱动的动态尺度路由相结合，提出一种极轻量化的自适应多尺度网络流量预测框架。首先，通过多粒度时间聚合构造互补的多尺度输入，各尺度专家在数百维OD变量间共享时间映射以严格锁定参数规模；其次，设计基于窗口均值、标准差、末态水平与一阶差分的低维路由分支，仅以131个额外参数即可动态感知当前时间窗口的平稳度与突变状态，实现样本级（Window-wise）的自适应加权融合。在Abilene和GÉANT数据集上的多维度实验佐证，本文方法在24 h常规预测、90分位高需求峰值估计以及168 h一周超长期预测中均取得显著领先优势。',
    'method12': '在骨干网通信场景下，尺度集合{{S={1,2,4}}}具有明确的物理对应关系：尺度{{s=1}}（96步）完整保留1 h粒度的原始高频波动与局部突发尖峰；尺度{{s=2}}（48步）通过2 h均值滤波平滑短时毛刺，刻画半日内的潮汐过渡节奏；尺度{{s=4}}（24步）则以4 h块均值浓缩长达4天的宏观负载基线。三个尺度互为补充，从微观瞬态到宏观趋势构建起层次化的表征空间。同时，在每个尺度上统一采用长度{{q=25}}的移动平均核提取趋势项，使细粒度专家聚焦于日周期（24 h）附近的趋势剥离，而粗粒度专家则捕获跨越多日的超长周期基线水平，从而最大化不同专家预测输出的多样性与互补性。',
    'method13': '上述四维统计特征从不同侧面完整刻画了当前流量窗口的运行工况：全局均值{{μ_n}}表征当前窗口的整体业务负载水位，标准差{{σ_n}}衡量窗口内的整体能量离散度与宏观波动幅度；末时刻均值{{ℓ_n}}捕捉历史窗口向未来预测区间过渡时的最新静态边界水平，提供关键的近期锚点信息；平均绝对一阶差分{{d_n}}则直接量化相邻小时之间的高频抖动剧烈程度。当网络处于夜间低谷或平稳运行期时，{{σ_n}}与{{d_n}}较小，路由网络可提高粗尺度专家（{{s=2,4}}）的权重以抑制随机噪声；反之，当早晚高峰切换或突发流量涌入导致{{ℓ_n}}与{{d_n}}激增时，路由网络能够迅速将权重向细粒度专家（{{s=1}}）倾斜，避免粗尺度平滑带来的相位滞后。通过在全变量间聚合这四个统计量，模型既规避了单变量局部异常噪点的误导，又将路由输入压缩至4维，从根本上杜绝了过拟合风险。',
    'results22a': '由表2可见，本文方法在Abilene和GÉANT两套数据集上的MSE与MAE指标均全面优于单尺度DLinear与LightTS基线，展现出最优的综合预测精度与稳定性。具体而言，在Abilene数据集上，本文方法不仅将MSE降至0.186，更将MAE从DLinear的0.188大幅降至0.168（相对降低10.64%），且MAE的样本标准差低至0.001，仅为DLinear（0.009）的1/9和LightTS（0.008）的1/8，表明自适应多尺度机制有效增强了模型对不同随机初始化的鲁棒性。',
    'results22b': '图2进一步展示了本文方法相对于主流MLP架构LightTS的误差降幅与参数量级对比。在预测精度方面，本文方法在Abilene和GÉANT上的MSE平均相对降幅高达29.80%和46.89%，MAE平均相对降幅分别达17.57%和29.15%；在模型复杂度方面，LightTS的参数规模随OD变量增加而急剧膨胀（两套配置分别高达130162和384382个参数），而本文方法得益于变量间共享的多尺度映射与极简路由设计，参数量恒定为8339，仅为LightTS的6.41%和2.17%（即参数量大幅缩减93.59%和97.83%）。这充分证明本文方法以不到LightTS十五分之一乃至四十六分之一的参数代价，实现了近30%～47%的误差削减，在模型轻量化与预测精度之间取得了极具竞争力的帕累托优势。',
    'results23a': '表3的消融实验结果深刻揭示了多尺度融合机制在复杂网络流量预测中的核心作用。首先，对比最终性能可知，本文方法在Abilene和GÉANT上的MSE与MAE均取得全场最优：相较于单尺度DLinear，两套数据集的MSE平均相对降低2.77%和2.35%，Abilene上的MAE更是从0.189显著降至0.173（降幅达8.47%）；相较于全局可学习权重，MSE分别进一步降低1.80%和4.31%，Abilene上的MAE降低达8.95%。',
    'results23b': '其次，深入剖析消融对照可以发现一个关键规律：在变量规模高达524维、流量突发特性更复杂的GÉANT数据集上，“固定等权”（MSE为0.447）、“全局可学习权重”（0.446）以及“恒定输入路由”（0.449）三种静态融合策略的误差反而均高于单尺度DLinear（0.437），这一现象有力地证明：多尺度表征并非简单叠加即可奏效，粗粒度尺度（{{s=2,4}}）在提取平滑趋势的同时不可避免地损失了高频细节，若采用不随样本窗口变化的静态权重进行无差别融合，在流量剧烈波动的窗口中必然引入严重的平滑滞后偏差，导致多尺度负迁移。相比之下，“恒定输入路由”虽然保留了与本文完全相同的网络结构与参数量，但由于缺失真实窗口统计特征输入，退化为静态加权，同样无法遮掩性能下降，唯有本文方法通过四维窗口量实时感知样本波动状态，动态抑制突变窗口下的粗尺度干扰并放大有效尺度的贡献，成为GÉANT上唯一成功突破单尺度DLinear性能上限的多尺度模型，充分印证了窗口自适应路由机制的必要性与有效性。',
    'results24setup': '在骨干网容量配置与流量工程中，高负载峰值时段的预测精度直接关系到链路拥塞控制与服务质量（QoS）保障，尤其当模型对高需求流量产生低估时，极易引发带宽分配不足与突发丢包。为此，以训练集各OD变量的第90百分位值{{τ_c}}为高需求阈值，构建测试集高需求样本点集合{{OMEGA_SET}}，并在{{Ω}}上重点考察高需求MAE与平均低估误差（average underestimation error，AUE）。其中，AUE专门量化预测值低于真实峰值时的短缺幅度，定义为',
    'results24definition': '式中，{{|Ω|}}为测试集中高需求目标点的总数。高需求点的MAE与AUE对比结果如图3所示。',
    'results24': '由图3可见，本文方法在两套数据集上的高需求MAE与平均低估误差均显著低于所有对照模型（Abilene上分别为0.147和0.137，GÉANT上分别为0.632和0.577）。同样值得注意的是，静态多尺度方法（固定等权、全局权重）在两套数据的高需求点上再次出现误差劣于单尺度DLinear的现象，原因在于均值池化削平了波峰，静态融合必然拉低峰值响应。而本文方法在Abilene上相较DLinear将高需求MAE与平均低估误差分别大幅降低13.96%和16.07%（相对固定等权更是降低约17.4%和21.3%）。这表明当窗口处于高负载爬升期时，路由特征中的末态均值{{ℓ_n}}与均值{{μ_n}}能够有效引导模型向保留完整波峰形态的细粒度专家赋权，从而显著缓解了传统多尺度模型常见的“削峰低估”弊端，具备更强的工程实用价值。',
    'results25a': '在图4中，本文方法在168 h超长周期预测任务上展现出压倒性的性能优势，其测试集MSE和MAE分别为0.841±0.088和0.536±0.028，大幅领先于所有四种对照模型。具体而言，相较于单尺度DLinear，本文方法的MSE和MAE平均相对降幅分别高达23.16%和11.16%；相较于固定等权、全局权重与恒定路由三种多尺度对照，MSE更是大幅降低23.77%～26.11%，MAE降低11.19%～12.39%。同时，在{{H=168}}配置下，路由网络参数量仍保持131不变，仅占模型总参数量（57587）的0.23%。',
    'results25b': '对比24 h与168 h任务可以发现，本文方法对DLinear的MSE降幅从2.35%跃升至23.16%（提升近10倍）。这是因为在长达一周（168步）的跨度下，单尺度模型极易受局部噪声误导而产生严重的远期趋势漂移；而本文方法依托粗尺度专家（{{s=2,4}}）提供的跨日宏观锚点与动态路由调控，有效抑制了长程预测中的误差累积效应。此外，图4中全部8个随机种子下的单次实验散点均稳定落于零轴右侧的正向增益区内（胜率达100%），充分证实了所提方法在长周期流量需求估计中的可靠性与普适优势。',
}

evidence = json.loads((ROOT/'review_scratch/results_explanation_20261022/evidence_audit.json').read_text(encoding='utf-8'))
summary = list(csv.DictReader((JOURNAL/'图表组织优化修订_20261022/图表与核验数据/24h均值与标准差.csv').open(encoding='utf-8-sig')))
abilene = {r['model']: r for r in summary if r['dataset']=='abilene'}
sd_ours = float(abilene['dlinear_scale']['mae_sd'])
ratio_d = 100*sd_ours/float(abilene['dlinear']['mae_sd'])
ratio_l = 100*sd_ours/float(abilene['lightts']['mae_sd'])
max_static_gain = max(r['mean'] for r in evidence['baseline_effects'] if r['metric']=='mse' and r['baseline']!='lightts')
assert f'{ratio_d:.2f}%' == '99.23%' and f'{ratio_l:.2f}%' == '106.26%'
assert f'{max_static_gain:.2f}%' == '4.97%'
CORRECTIONS = {
    'abstract': [('29.80%', '25.77%'), ('46.89%', '43.74%'), ('4.31%', '4.97%')],
    'results22a': [('0.186','0.189'), ('0.188','0.189'), ('0.168','0.173'), ('10.64%','8.01%'), ('0.001','0.008'), ('0.009','0.008'), ('1/9','99.23%'), ('1/8','106.26%')],
    'results22b': [('29.80%','25.77%'), ('46.89%','43.74%'), ('17.57%','12.66%'), ('29.15%','29.09%'), ('30%～47%','26%～44%')],
    'results23a': [('8.47%','8.01%'), ('8.95%','8.91%')],
    'results24': [('17.4%','17.47%'), ('21.3%','20.84%')],
}
FINAL = dict(TEXT)
for key,pairs in CORRECTIONS.items():
    for a,b in pairs:
        assert FINAL[key].count(a)==1, (key,a)
        FINAL[key]=FINAL[key].replace(a,b)
assert all(FINAL[k]==TEXT[k] for k in TEXT if k not in CORRECTIONS)

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W,M='{'+NS['w']+'}','{'+NS['m']+'}'
with ZipFile(SOURCE) as z:
    infos=z.infolist()
    members={i.filename:z.read(i.filename) for i in infos}
old=E.fromstring(members['word/document.xml'])
new=E.fromstring(members['word/document.xml'])
body=new.find('w:body',NS)
original=list(body)
assert len(original)==117
assert ''.join(original[13].xpath('.//w:t/text()',namespaces=NS)).startswith('在时间结构建模方面')
assert '(16)' in original[83].xpath('.//w:t/text()',namespaces=NS)
old_setup_math=original[82].findall('m:oMath',NS)
assert len(old_setup_math)==2
math_w_rpr=deepcopy(old_setup_math[0].find('.//w:rPr',NS))

def el(tag,text=None,**attrs):
    x=E.Element(M+tag,{M+k:v for k,v in attrs.items()})
    if text is not None:x.text=text
    return x

def mr(value,upright=False):
    rr=el('r')
    pp=el('rPr'); pp.append(el('sty',val='p' if upright else 'i'))
    rr.append(pp); rr.append(deepcopy(math_w_rpr)); rr.append(el('t',value))
    return rr

def math(value):
    if value=='τ_c':return deepcopy(old_setup_math[0])
    if value=='OMEGA_SET':return deepcopy(old_setup_math[1])
    mm=el('oMath')
    if re.fullmatch('[μσℓd]_n',value):
        ss=el('sSub'); base=el('e'); base.append(mr(value[0])); ss.append(base)
        ix=el('sub'); ix.append(mr('n')); ss.append(ix); mm.append(ss)
    else:
        for part in re.findall('[A-Za-zΩ]+|[^A-Za-zΩ]+',value):
            mm.append(mr(part,not bool(re.fullmatch('[A-Za-zΩ]+',part))))
    return mm

def wr(value,bold=False,sup=False):
    rr=E.Element(W+'r')
    if bold or sup:
        pp=E.SubElement(rr,W+'rPr')
        if bold:E.SubElement(pp,W+'b')
        if sup:E.SubElement(pp,W+'vertAlign',{W+'val':'superscript'})
    tt=E.SubElement(rr,W+'t')
    if value[:1].isspace() or value[-1:].isspace():tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    tt.text=value
    return rr

def make_para(template,key):
    p=deepcopy(template)
    # Keep section properties, styles and paragraph properties from the source.
    # Newly cloned paragraphs receive no duplicate Word paragraph IDs.
    for attr in list(p.attrib):
        if E.QName(attr).localname in ('paraId','textId'):del p.attrib[attr]
    for c in list(p):
        if c.tag!=W+'pPr':p.remove(c)
    value=FINAL[key]
    for token in re.split(r'(\{\{S=\{1,2,4\}\}\}|\{\{.*?\}\}|\[\d+\]|摘要：)',value):
        if not token:continue
        if token.startswith('{{'):p.append(math(token[2:-2]))
        else:p.append(wr(token,bold=token=='摘要：',sup=bool(re.fullmatch(r'\[\d+\]',token))))
    return p

replacements={5:['abstract'],13:['intro1'],14:['intro2'],71:['results22a','results22b'],
              79:['results23a','results23b'],82:['results24setup'],85:['results24'],92:['results25a','results25b']}
insert_after={31:['method12'],42:['method13'],83:['results24definition']}
created={}
for index,node in enumerate(original):
    if index in replacements:
        at=body.index(node)
        for offset,key in enumerate(replacements[index]):
            item=make_para(node,key); body.insert(at+offset,item);created[key]=item
        body.remove(node)
    if index in insert_after:
        at=body.index(node)+1
        for offset,key in enumerate(insert_after[index]):
            item=make_para(original[43],key); body.insert(at+offset,item);created[key]=item

def canon(x):
    x=deepcopy(x);E.cleanup_namespaces(x)
    return E.tostring(x,method='c14n')

def math_flat(s):
    if s=='OMEGA_SET':return ''.join(old_setup_math[1].xpath('.//m:t/text()',namespaces=NS))
    return s.replace('_','')

for key,p in created.items():
    expected=re.sub(r'\{\{(.*?)\}\}',lambda m:math_flat(m[1]),FINAL[key])
    visible=''.join(p.xpath('.//w:t/text() | .//m:t/text()',namespaces=NS))
    assert visible==expected,(key,visible,expected)

for index,node in enumerate(original):
    if index not in replacements:
        assert node.getparent() is body
        assert canon(old.find('w:body',NS)[index])==canon(node), index
assert [canon(t) for t in old.xpath('.//w:tbl',namespaces=NS)]==[canon(t) for t in new.xpath('.//w:tbl',namespaces=NS)]
# All source native equations remain as a subsequence, including tau, Omega and AUE.
old_math=[canon(t) for t in old.xpath('.//m:oMath',namespaces=NS)]
new_math=[canon(t) for t in new.xpath('.//m:oMath',namespaces=NS)]
position=0
for item in old_math:
    position=new_math.index(item,position)+1
assert [canon(t) for t in old.xpath('.//w:drawing',namespaces=NS)]==[canon(t) for t in new.xpath('.//w:drawing',namespaces=NS)]

xml=E.tostring(new,xml_declaration=True,encoding='UTF-8',standalone=True)
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(OUTPUT,'w') as z:
    for info in infos:z.writestr(info,xml if info.filename=='word/document.xml' else members[info.filename])
with ZipFile(OUTPUT) as z:
    changed=[k for k,v in members.items() if z.read(k)!=v]
assert changed==['word/document.xml']
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
audit={
    'source':str(SOURCE),'source_sha256':SOURCE_SHA,'output':str(OUTPUT),
    'output_sha256':sha256(OUTPUT.read_bytes()).hexdigest(),
    'source_unchanged':True,'changed_package_parts':changed,
    'replaced_source_indices':list(replacements),'insert_after_source_indices':list(insert_after),
    'screenshot_paragraphs':len(created),'only_numeric_edits_to_screenshot_prose':True,
    'numeric_corrections':CORRECTIONS,'all_other_source_nodes_unchanged':True,
    'tables_unchanged':True,'images_unchanged':True,'source_math_preserved':True,
    'original_native_math':len(old_math),'native_math':len(new_math),
    'sections':len(new.xpath('.//w:sectPr',namespaces=NS)),
    'visual_review_pending':True,
}
(QA/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'screenshot_text_and_corrections.json').write_text(json.dumps({'screenshot_text':TEXT,'final_text':FINAL,'numeric_corrections':CORRECTIONS},ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'artifact.md').write_text(
    '# Screenshot-directed manuscript revision\n\nSource: '+str(SOURCE)+'\nSHA256: '+SOURCE_SHA+'\n\n'
    'Edit exactly the seven supplied screenshot sections. Preserve screenshot prose verbatim apart from a whitelist of verified numeric corrections. '
    'Preserve original file, every unrelated paragraph, all tables, figures, styles, headers, footers, section geometry and original native math. '
    'Retain existing inline citation superscripts. Add editable inline math. Do not translate or rewrite the unchanged English abstract. '
    'Render and inspect every final page without reducing font size or compressing the supplied prose.\n',encoding='utf-8')

lines=['# 截图逐项修改与数据核对记录','',
       '底稿：'+SOURCE.name,'修改稿：'+OUTPUT.name,'',
       '已按7张截图依次替换或补入摘要、引言、1.2、1.3、2.2—2.5相关文字。除下列数值外，未对截图正文进行润色或改写。原稿、表格、图片、原有公式、版式及其他段落保持不变。','',
       '## 按八次实验记录修正的数值','',
       '- 相对LightTS：两套数据MSE平均配对降幅为25.77%、43.74%；MAE为12.66%、29.09%。概括区间相应改为近26%～44%。',
       '- 摘要中“最高降低”统计单尺度DLinear及固定等权、全局权重、恒定输入路由三个静态融合对照，最大MSE平均配对降幅为4.97%（GÉANT对恒定输入路由）。',
       '- Abilene：本文MSE为0.189；DLinear与本文MAE为0.189、0.173；配对MAE平均降幅为8.01%。',
       '- Abilene的MAE样本标准差：本文、DLinear与LightTS保留三位小数均为0.008；按未四舍五入值计算，本文分别为两种基线的99.23%、106.26%，不再采用旧结果中的1/9、1/8。',
       '- 相对全局权重的Abilene MAE平均配对降幅为8.91%。',
       '- 高需求点相对固定等权的Abilene MAE和AUE平均配对降幅为17.47%、20.84%。',
       '- 168 h相关均值、标准差、配对降幅及100%正向配对比例与实验记录一致。','',
       '## 按要求保留、但不能视为已验证的文字判断','',
       '本次只允许调整实验数值，因而原样保留了截图中的非数值表述。以下判断不因完成文字替换而得到证实：','',
       '- “最优……稳定性”“有效增强……随机初始化的鲁棒性”：当前Abilene MAE标准差接近DLinear且略高于LightTS，GÉANT标准差也较DLinear高，不能据此声称稳定性全面最优。',
       '- “从根本上杜绝了过拟合风险”：四维路由输入不能从原理上排除整个预测模型的过拟合。',
       '- 特定高峰/低谷时段权重向粗细尺度转移、静态融合必然导致削峰或相位滞后、长程误差改善由跨日锚点机制导致等解释，未见对应的路由轨迹或机制验证实验。',
       '- “显著”没有在本次工作中进行统计显著性检验；两个数据集和所列对照的结果不能直接证明“普适优势”。',
       '- 中文摘要按截图扩写；未自行改写英文摘要或按投稿摘要字数要求压缩。','',
       '上述说明只用于作者核对，未放入论文正文。',
]
(OUTPUT.parent/'修改与核对说明.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
