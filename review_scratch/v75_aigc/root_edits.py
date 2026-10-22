EDITS={
3:[
('小时级骨干网络流量预测需要同时刻画短期波动与长期趋势。针对这一需求，设计一种轻量自适应多尺度预测模型。','面向小时级骨干网络流量预测，设计一种轻量自适应多尺度预测模型，以同时刻画短期波动与长期趋势。'),
('历史窗口数据按三种时间分辨率输入模型，由独立分解线性专家分别生成预测结果。路由网络从当前窗口提取均值、标准差、末时刻均值和平均绝对一阶差分，再由多层感知器计算融合权重。','三种时间分辨率的历史窗口数据分别交由独立分解线性专家预测。当前窗口的均值、标准差、末时刻均值和平均绝对一阶差分由路由网络提取，多层感知器据此给出融合权重。'),
('实验采用Abilene和GÉANT，以 96 步历史输入预测未来 24 步。','以Abilene和GÉANT检验模型，历史输入为 96 步，预测目标为未来 24 步。'),
('在3个共同随机种子的比较中，单尺度分解线性模型作为对照，本文方法的均方误差分别降低','3个共同随机种子的实验中，相比单尺度分解线性模型，本文方法的均方误差在两套数据上分别降低'),
('；采样导向轻量模型LightTS作为对照时，降幅为','；相比采样导向轻量模型LightTS，对应降幅为'),
('8种子消融实验以全局可学习权重和恒定输入路由作对照，Abilene的逐种子平均改进率均约为','在8种子消融实验中，与全局可学习权重和恒定输入路由比较，Abilene的逐种子平均改进率均约为'),
('，GÉANT的对应改进率分别为','，GÉANT上分别为'),
('多尺度候选预测与低维路由机制配合，在仅引入少量融合参数的条件下获得更低的平均预测误差。输出结果可为次日网络流量需求分析与容量规划提供参考。','实验中，多尺度候选预测结合低维路由机制，在增加少量融合参数的条件下获得更低的平均预测误差，所得预测可为次日网络流量需求分析与容量规划提供参考。')],
9:[
('Hourly backbone network traffic forecasting requires a representation of both short-term fluctuations and long-term trends. A lightweight adaptive multiscale forecasting model was developed for this purpose.','A lightweight adaptive multiscale forecasting model was developed for hourly backbone network traffic forecasting to represent short-term fluctuations and long-term trends.'),
('Three temporal resolutions were used to represent historical windows; at each resolution, independent decomposition linear experts generated candidate forecasts.','Historical windows were represented at three temporal resolutions, with independent decomposition linear experts generating candidate forecasts at each resolution.'),
('For the current window, a routing network extracted four statistics: the mean, standard deviation, mean at the last time step, and mean absolute first difference. These statistics served as inputs to a multilayer perceptron with two fully connected layers, which calculated fusion weights.','A routing network extracted the mean, standard deviation, mean at the last time step, and mean absolute first difference from the current window. A multilayer perceptron with two fully connected layers calculated fusion weights from these four statistics.'),
('On Abilene and GÉANT, experiments used 96 historical steps for predicting the next 24 steps.','Experiments on Abilene and GÉANT used an input length of 96 historical steps and a forecast length of 24 steps.'),
('With three common random seeds, the proposed method reduced mean squared error by','Across three common random seeds, mean squared error decreased by'),
('Relative to the sampling-oriented lightweight model LightTS, the corresponding reductions were','The corresponding reductions relative to the sampling-oriented lightweight model LightTS were'),
('In ablation experiments across eight random seeds, learned global weights and a constant-input router served as controls for the proposed method. Against both controls, the mean seed-wise improvements on Abilene were approximately','Ablation experiments across eight random seeds compared the proposed method with learned global weights and a constant-input router. Mean seed-wise improvements over both controls were approximately'),
('%; on GÉANT, the respective improvements were','% on Abilene; on GÉANT, they were'),
('Lower mean forecasting errors were obtained by combining multiscale candidate forecasts with low-dimensional routing while adding few additional fusion parameters. For next-day network traffic demand analysis and capacity planning, the forecasts can serve as a reference.','Combining multiscale candidate forecasts with low-dimensional routing achieved lower mean forecasting errors with few additional fusion parameters. The forecasts can provide a reference for next-day network traffic demand analysis and capacity planning.')],
11:[
('容量规划则需要掌握各节点对未来的需求变化。本文针对小时级OD流量预测未来一天的需求，为高需求时段观察和容量安排提供参考。','掌握各节点对未来的需求变化是容量规划的依据。本文以小时级OD流量预测未来一天的需求，供高需求时段观察和容量安排参考。'),
('流量变化的复杂性与云计算、视频业务和数据中心互联所增加的业务迁移与聚集有关。各OD变量量级不同，周期变化又与局部波动、突发变化叠加，因此较慢趋势和短时变化均需由预测模型刻画。','云计算、视频业务和数据中心互联增加了业务迁移与聚集，流量变化的复杂性与此有关。OD变量之间存在量级差异，周期变化中又叠加局部波动与突发变化，预测模型需同时刻画较慢趋势和短时变化。')],
12:[
('综述了网络流量预测方法，指出机器学习与深度学习等数据驱动方法的应用不断增加。网络规模扩大后，仅分析单一序列难以覆盖OD变量之间的关联。','在网络流量预测方法综述中指出，机器学习与深度学习等数据驱动方法的应用不断增加。随网络规模扩大，OD变量之间的关联难以仅由单一序列分析覆盖。'),
('采用图神经网络处理空间关联与时间依赖','通过图神经网络处理空间关联与时间依赖'),
('这些研究从时间依赖、变量关联和周期结构等角度开展预测。','上述预测研究分别涉及时间依赖、变量关联及周期结构。')],
13:[
('原始序列中的短时扰动经时间聚合后得到平滑，较慢趋势随之更明显。不同时间分辨率所提供的信息具有互补性。','时间聚合平滑了原始序列中的短时扰动，使较慢趋势更易观察；不同时间分辨率由此提供互补信息。'),
('采用深度回声状态网络开展多尺度流量预测。轻量预测方法中，','以深度回声状态网络进行多尺度流量预测。在轻量预测方法中，'),
('将序列分解与线性映射结合使用。TimeMixer','结合序列分解与线性映射。TimeMixer'),
('进行多尺度混合。LightTS','使用多尺度混合，LightTS'),
('则采用采样导向的多层感知器','采用采样导向的多层感知器'),
('本文以DLinear作为主干，考察不同尺度预测结果的融合方式。','不同尺度预测结果的融合方式是本文的研究对象，预测主干采用DLinear。')],
14:[
('当各尺度专家采用相同结构时，本文考察融合比例随当前窗口状态调整后能否降低预测误差。固定权重能够组合多尺度预测结果，其融合比例却无法随窗口间的状态差异调整。','本文在各尺度专家结构相同的条件下，考察按当前窗口状态调整融合比例能否降低预测误差。固定权重可组合多尺度预测结果，但不同窗口使用同一融合比例，无法体现窗口间的状态差异。')],
17:[
('图1中预测分支与路由分支共享同一预处理历史窗口，DLinear专家内部结构通过梯形虚线展开。','图1给出预测分支和路由分支，两者共享同一预处理历史窗口；梯形虚线表示DLinear专家内部结构的展开。'),
('历史OD窗口经对数变换与标准化处理，得到尺度1、2和4的序列。独立DLinear专家将趋势项与余项分别映射，两部分的24步预测相加后形成候选预测。','历史OD窗口完成对数变换与标准化后构造尺度1、2和4的序列。每个独立DLinear专家分别映射趋势项与余项，两部分的24步预测相加构成候选预测。'),
('尺度路由网络从原始时间分辨率的预处理输入中取得4项统计特征，用于计算Softmax权重。模型输出由3个尺度候选预测加权求和得到。图中曲线和色块仅作示意。','尺度路由网络使用原始时间分辨率预处理输入的4项统计特征计算Softmax权重。模型随后按这些权重对3个尺度候选预测加权求和，得到输出。曲线与色块在图中仅作示意。')],
20:[
('各尺度的预测彼此独立，均采用相同DLinear结构。原始尺度中保留局部波动，较粗尺度经时间聚合突出较慢趋势。融合权重由路由网络按当前窗口特征分配，在统一预测主干上结合多尺度输入与按样本加权。','相同DLinear结构用于各尺度，预测由各专家独立完成。原始尺度保留局部波动，时间聚合后的较粗尺度突出较慢趋势。路由网络依据当前窗口特征分配融合权重，使统一预测主干结合多尺度输入与按样本加权。')],
71:[
('均方误差（MSE）、平均绝对误差（mean absolute error，MAE）及均方根误差（root mean squared error，RMSE）作为预测性能的评价指标。','预测性能采用均方误差（MSE）、平均绝对误差（mean absolute error，MAE）及均方根误差（root mean squared error，RMSE）评价。'),
('测试集MSE的计算沿用式（14）的平均规则，样本数为测试窗口数。式（15）中的Nte表示测试样本数，MAE和RMSE按下式定义','在测试集上计算MSE时，式（14）的平均规则保持不变，样本数取测试窗口数。式（15）用Nte表示测试样本数，MAE和RMSE的定义为')],
86:[
('图3展示本文方法相对DLinear和固定等权多尺度模型的逐种子改进分布。单个种子的改进率以散点表示，均值以黑色菱形标出，横向误差线对应95%置信区间。','图3给出本文方法相对DLinear和固定等权多尺度模型的逐种子改进分布。散点对应单个种子的改进率，黑色菱形给出均值，横向误差线给出95%置信区间。')],
89:[
('图3所列的不同随机种子改进率中，两类基线下三个指标的平均改进率均为正。以DLinear为对照，','图3中，相对两类基线的三个指标平均改进率均为正。DLinear作为对照时，'),
('平均改进率依次为','的平均改进率分别为'),
('，MSE和RMSE在8次实验中均有改善。','，MSE和RMSE均在8次实验中改善。'),
('GÉANT的三项对应平均改进率为','同样三个指标在GÉANT上的平均改进率为'),
('，负改进率涉及更多种子，种子间波动也较大。改用固定等权模型作为对照后，按相同指标顺序，','，出现负改进率的种子更多，种子间波动较大。固定等权模型作为对照时，仍按上述指标顺序，'),
('，GÉANT上则为','，GÉANT的对应值为')],
92:[
('图4（a、b）使用8个种子的全测试预测点，按真实值分位点划分为最多40组，并绘制分组平均预测；种子间±1个标准差以浅色带表示。','图4（a、b）的统计覆盖8个种子的全测试预测点。按真实值分位点将这些预测点分成最多40组，分别绘出分组平均预测，浅色带对应种子间±1个标准差。'),
('图4（c～f）取种子42的预测结果，依据真实序列选择标准差接近第75百分位的OD通道，窗口的平均绝对一阶差分则接近中位数、第90百分位。','图4（c～f）采用种子42的预测结果，选取真实序列标准差接近第75百分位的OD通道，再选平均绝对一阶差分接近中位数、第90百分位的窗口。')],
96:[
('图5汇总8个种子的测试窗口权重。各随机种子的窗口平均权重用彩色点表示；黑色菱形及误差线标出这些均值的均值±1个标准差。短横线标出汇总分布中位数，水平虚线对应固定等权1/3。','图5汇总8个种子的测试窗口权重，彩色点分别给出各随机种子的窗口平均权重。对这些均值再求均值±1个标准差，以黑色菱形及误差线表示。汇总分布中位数由短横线标出，水平虚线标出固定等权1/3。')],
99:[
('Abilene的三个尺度汇总平均权重依次取','Abilene三个尺度的汇总平均权重分别为'),
('；GÉANT的对应取值为','；相同尺度顺序下，GÉANT的取值为'),
('。各取值均偏离固定等权的1/3。按来源划分汇总权重方差后，GÉANT三个尺度约有','。这些取值均偏离固定等权的1/3。将汇总权重方差按来源分解，GÉANT三个尺度中约'),
('来自种子间差异，Abilene的对应比例为','的方差来自种子间差异，Abilene的对应比例为'),
('。GÉANT在同一种子内部仅有较小的窗口间权重变化。图5同时呈现不同尺度的总体权重分配及随机种子间的差异。','。在GÉANT的同一种子内，权重随窗口的变化较小。总体尺度权重分配和随机种子间差异在图5中同时呈现。')],
100:[
('测试窗口以训练阶段窗口波动强度的三分位数划分为低、中、高三组，用于考察不同波动水平下模型的表现；波动强度采用平均绝对一阶差分度量。','为考察不同波动水平下的预测表现，依据训练阶段窗口波动强度的三分位数，将测试窗口划为低、中、高三组；平均绝对一阶差分用于度量波动强度。'),
('以全局权重模型作对照时，Abilene三组的逐种子平均MSE改进率依次为','与全局权重模型比较，Abilene三组的逐种子平均MSE改进率分别为'),
('，相应的样本窗口数为','，对应的样本窗口数为'),
('GÉANT按相同训练阈值划分后，测试集中没有低波动窗口。中、高波动组分别有','GÉANT测试窗口按相同训练阈值划分，没有窗口进入低波动组。中、高波动组的窗口数分别为'),
('个窗口，其对应改进率为','个，相应改进率为'),
('Abilene高波动组的尺度1平均权重超过中波动组，误差优势却未随权重增加而增强。GÉANT的中、高波动组权重取值近似相同，误差改善幅度仍存在差异。因此，误差变化与权重调整之间并非简单的对应关系。','Abilene高波动组的尺度1平均权重高于中波动组，误差优势并未随之增强；GÉANT中、高波动组的权重近似相同，误差改善幅度却不同。这些分组结果表明，权重调整与误差变化并非简单对应。')],
102:[
('单尺度DLinear包含4656个可训练参数，使用三个尺度专家的固定等权模型含8208个参数。','单尺度DLinear的可训练参数为4656个，三个尺度专家构成的固定等权模型共含8208个参数。'),
('在固定等权结构上加入三个全局权重参数后，参数总数为8211个；样本级路由和恒定输入路由的参数总数均为8339个。','固定等权结构加入三个全局权重参数后，总参数量为8211个；样本级路由与恒定输入路由均含8339个参数。'),
('与固定等权及全局权重模型相比，路由网络分别增加131个和128个参数。恒定输入路由虽然保留样本级路由的网络结构，恒为零的输入却使首层输入权重不参与有效计算。','路由网络比固定等权及全局权重模型分别多131个和128个参数。样本级路由的网络结构仍保留在恒定输入路由中，但输入恒为零，首层输入权重因此不参与有效计算。')],
103:[
('种子42～49的8个模型检查点用于测量前向耗时，预测长度设为24，批量大小设为16。','前向耗时按种子42～49的8个模型检查点分别测量，预测长度为24，批量大小为16。'),
('关闭梯度计算并将测试张量预先载入显存后，各检查点预热20个批次，再对完整测试集重复计时10次。','测试张量预先载入显存，计时过程关闭梯度计算。各检查点先预热20个批次，完整测试集随后重复计时10次。'),
('每次测量以总耗时除以批次数，随后对10次测量取平均，再对8个检查点取平均。','以每次总耗时除以批次数得到每批耗时，先平均10次测量结果，再平均8个检查点的结果。'),
('Abilene与GÉANT上，本文方法测得的平均每批前向耗时分别为','在Abilene与GÉANT上测得，本文方法的平均每批前向耗时分别为'),
('上述测量不包含数据读取与传输开销。','数据读取与传输开销未计入上述测量。')],
104:[
('小时级网络管理中，全部有效OD变量未来24 h的逐小时需求预测由模型一次输出。观测更新后，各OD最近96 h的流量按训练预处理规则构成历史窗口，预测结果按时间与节点对组织，供需求分析使用。','模型在小时级网络管理中一次给出全部有效OD变量未来24 h的逐小时需求预测。更新观测后，按训练预处理规则将各OD最近96 h的流量构成历史窗口；需求分析使用的预测结果按时间与节点对组织。')],
105:[
('实际需求分析使用的预测结果需由标准化空间还原到原始流量量纲。利用训练阶段保存的逐 OD 统计量做逆标准化后，进行逆对数变换，并将结果截断至非负范围。','用于实际需求分析时，预测结果须恢复原始流量量纲。先根据训练阶段保存的逐 OD 统计量对标准化空间内的结果做逆标准化，随后进行逆对数变换，并截断至非负范围。'),
('结合网络拓扑与路由关系，各 OD 的预测需求可汇总到对应链路上；比较链路预测需求与可用容量，可为容量调度与扩容决策提供参考。','各 OD 的预测需求可依照网络拓扑与路由关系汇总至对应链路，链路预测需求与可用容量的比较可供容量调度与扩容决策参考。')],
108:[
('高需求预测点上的MAE和低估误差均值较低，这与图4较高真实值区间的预测结果相符。Abilene在不同随机种子下的改善较为一致；GÉANT两项配对改进率的95%置信区间均包含零，各随机种子下的改善有所不同。上述结果可供高需求时段的流量监测与容量规划参考。','高需求预测点上较低的MAE和低估误差均值，与图4较高真实值区间的预测结果相符。Abilene的改善在不同随机种子下较为一致；GÉANT两项配对改进率的95%置信区间均包含零，改善幅度随随机种子而异。高需求时段的流量监测与容量规划可参考这些结果。')],
110:[
('独立分解线性专家生成预测结果，基于窗口统计特征的尺度路由网络以自适应多尺度加权协调各尺度输出，在较小参数规模下完成小时级骨干网流量预测。两套数据的重复实验中，平均误差均低于所设单尺度与固定融合对照。预测输出可供未来一天需求分析参考，后续将在更多网络数据和预测长度下检验模型适用性。','本文以独立分解线性专家生成预测结果，基于窗口统计特征的尺度路由网络通过自适应多尺度加权融合各尺度输出，以较小参数规模完成小时级骨干网流量预测。两套数据重复实验的平均误差均低于所设单尺度与固定融合对照，预测可供未来一天需求分析参考。后续将在更多网络数据和预测长度下检验模型适用性。')],
}
