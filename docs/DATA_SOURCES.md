# 来源、数据字典与公开范围

## 数据版本

输入是用户原始《初步数据集.zip》，其中补充数据说明记载事件抓取日期为2026-10-02。没有用当前网络数据覆盖旧快照。原始文件与仓库摘录的SHA256见 `data/source/manifest.json`。

| 文件 | 观察单位 | 主要字段 | 来源 |
| --- | --- | --- | --- |
| events_current_flat.csv | 一个事件记录 | event_id、cat1、cat2、venueid | LCSD events.xml 的原包展平结果 |
| venues_current_flat.csv | 一个子场地/区域集合代码 | venue_id、venuee、venuec、latitude、longitude | LCSD venues.xml 的原包展平结果 |
| event_category_codebook.csv | 一项官方分类代码 | code、name_sc、level | LCSD事件字典第7–9页的原包整理表 |
| lcsd_cultural_programmes_by_venue.csv | 场地×季度 | Year、Quarter、Venue_Code、Performance、Attendance、Remarks | LCSD开放数据原包快照，2023Q2–2026Q1 |
| stage3_participation_by_art_form.csv | 艺术类别×指标 | group、metric、value_pct、base_n、source_page | HKADC Stage 3市场总览第36页的原包转录表 |

LCSD原始接口：

- https://www.lcsd.gov.hk/datagovhk/event/events.xml
- https://www.lcsd.gov.hk/datagovhk/event/venues.xml
- https://www.lcsd.gov.hk/datagovhk/event/data_dictionary.pdf
- https://www.lcsd.gov.hk/datagovhk/

原包的 `supplement_sources.csv` 明确说明历史场地季度CSV的直接下载地址未被保存。因此这里只列已知官方入口，未编造精确历史端点。

HKADC报告入口：

https://www.hkadc.org.hk/en/research/behavioural-study-on-arts-participants-stage-3-survey-report-on-patterns-of-arts-participation_3004

原包所记市场总览PDF地址：

https://www.hkadc.org.hk/media/files/research_and_report/Behavioural%20Study%20Stage%203_2024/For%20Chi%20Website_0430/Behavioural%20Study%20on%20Arts%20Participants_Stage%203_Market%20Overview_.pdf

## 公开摘录范围

只公开分析需要的数字、类别代码、公开设施名称和设施坐标。事件表删除标题、描述、联系方式、邮箱、咨询字段与外链。仓库不包含原始65MB压缩包、完整PDF、个人调查微观数据、账号信息或登录资料。

原报告与数据的权利仍归各来源机构；本项目未声称拥有原始资料，也未为第三方数据另行授予开源许可。公开数值摘录用于可复查的课程分析。转发完整报告应从原机构页面获取并遵守其条款。

## 处理后表说明

- `events_clean.csv`：878条事件，含类别中文、设施名、映射状态、是否具体设施和是否有有效坐标。
- `history_clean.csv`：保留原始数值字符串与解析值，`-`仍可追溯。
- `venue_mapping.csv`：本次有事件的子场地与设施/历史代码映射；不等于完整香港设施名录。
- `unmapped_events.csv`：没有有效坐标的66条事件。
- `non_specific_venues.csv`：被排除出具体设施网络的41条区域集合记录。
- `spatial_2025_performance.csv`：共同完整设施份额、分类和历史观测数。
- `venue_category_matrix.csv`：设施×官方类别事件权重矩阵。
- `venue_communities.csv`、`category_communities.csv`：默认分辨率下的社区标签；标签数字没有固有顺序含义。
- `community_sensitivity.csv`：五种分辨率下的社区数和对应目标函数值。
- `participation_modes.csv`：互斥模式的全样本百分比及A/U占比。
- `ca_art_coordinates.csv`、`ca_mode_coordinates.csv`：行列主坐标。
- `audit.json`：覆盖率、行数、矩阵维度、相关系数及惯量校验结果。

## 技术文档

- Dash callbacks: https://dash.plotly.com/basic-callbacks
- Plotly MapLibre: https://plotly.com/python/mapbox-to-maplibre/
- NetworkX bipartite overview: https://networkx.org/documentation/stable/reference/algorithms/bipartite.html

项目的二部社区贪心优化由 `src/analysis.py` 显式实现；NetworkX用于力导向布局，没有隐藏调用普通Louvain作为二部算法。
