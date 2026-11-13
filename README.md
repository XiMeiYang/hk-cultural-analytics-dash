# 香港公共文化消费的多维可视分析

成员4的完整分析模块，使用 **Python + Plotly + Dash**。数据来自原始《初步数据集.zip》，无随机模拟数据。仓库包含可运行应用、经过最小化处理的数据摘录、清洗与分析脚本、结果表、中文方法说明和课堂汇报稿。

## 三个问题与交付物

| 保留的维度与问题 | 实现的图表 | 交互 |
| --- | --- | --- |
| **空间维度 · 问题4：用当前事件级场地坐标验证历史空间格局** | 当前事件密度图、历史与当前份额的双变量场地点图、份额散点图、九色图例 | 活动类别、历史年度/季度、表演场次/入场人次、CSV下载 |
| **空间维度 · 问题5：场地与类别二部图社区检测** | 力导向二部网络图、社区类别构成热力图、社区空间分布图 | 活动类别、社区分辨率、节点悬停、CSV下载 |
| **类别维度 · 问题5：对应分析与数字化参与空间** | CA双标图、非实体参与占比条形图、互斥模式矩阵 | 悬停、缩放、CSV下载 |

**口径调整必须保留：**“数字化参与空间”沿用提案题名，但原始报告的 alternative modes 包含电视、广播、DVD/CD等，因此条形图明确标为“非实体参与占比”，不能宣称为纯线上参与率。

## 运行（Python 3.12 推荐）

在 GitHub 点击 **Code → Download ZIP**，解压后进入项目文件夹；也可克隆仓库。

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

macOS / Linux：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

在浏览器打开 **http://127.0.0.1:8050**。不需要 Mapbox token。浅色底图需要联网；离线时选择“空白底图”，保留经纬度点位但不显示道路。GitHub 仓库本身不运行 Python，仓库地址不是已部署网页。

如果 Windows PowerShell 不允许激活虚拟环境，可直接运行 `.venv\Scripts\python.exe -m pip install -r requirements.txt` 和 `.venv\Scripts\python.exe app.py`，不需要修改系统执行策略。

## 重建结果与验证

```bash
python scripts/build_outputs.py
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

生成无需启动 Dash 的单文件交互图表报告：

```bash
python scripts/export_html.py
```

输出 `exports/member4_report.html`，双击打开即可。报告固定为默认分析；包含Plotly脚本，地图使用无道路底图的坐标视图。

如果需要从原始压缩包重新提取数据：

```bash
python scripts/extract_archive.py /path/to/初步数据集.zip
python scripts/build_outputs.py
```

脚本只读取5个指定CSV，忽略压缩包内目录编码差异，不解压执行文件，不上传原始压缩包。

## 默认结果（原始快照）

- 878条事件，812条具有有效坐标，66条未定位；全部事件可连接到场地字典。
- 41条“某区内场地”的区域集合记录不进入具体设施网络；其余837条构成25设施 × 17类别、106条加权关联。
- 2025年完整季度且当前出现的共同设施为14个；历史表演份额与当前事件份额的Spearman ρ约 **0.257**。两者统计口径不同，不能把它解释为历史恢复趋势得到验证。
- γ=1时，贪心二部模块度得到8个社区，Q约 **0.507**。γ=0.5–1.5时社区数为5–9，因此“8组”不是唯一真值。
- CA使用9类别 × 3互斥模式，前两维惯量占比约 **66.69% / 33.31%**。三列最多只有两个有效维度，合计100%属于矩阵结构，不是模型预测准确率。

更多解读见 [分析结果](docs/RESULTS_ZH.md)、[方法说明](docs/METHODS_ZH.md)、[课堂汇报稿](docs/PRESENTATION_ZH.md)、[来源与数据字典](docs/DATA_SOURCES.md)。

## 文件结构

- `app.py`：交互应用与下载功能。
- `src/analysis.py`：清洗、设施映射、二部模块度、对应分析。
- `src/charts.py`：全部Plotly图表。
- `data/source/`：最小化原始摘录及校验和；不含联系人、邮箱、活动描述、原始PDF。
- `data/processed/`：可复查的清洗表、映射表、缺失清单、矩阵、社区、CA坐标、审计结果。
- `scripts/`：原包提取、结果重建、独立HTML导出。
- `tests/`：数据覆盖、缺失处理、数学一致性、应用接口与全部类别筛选测试。

## 重要限制

1. 事件快照为 **2026-10-02**，不是今天的实时数据，也不是2026年全年活动总数。
2. 历史场地统计明确不含租用者节目；当前事件清单包含不同主办方，比较只能用于探索空间分布。
3. 无区界文件，不生成伪造的18区边界或人口密度结论。场地坐标不是观众居住地。
4. HKADC 2022问卷的参考期是2021年7月至2022年7月，n=3017，公开百分比经过加权和四舍五入，不是个人微观数据。
5. 实体/非实体可重叠，必须先推导互斥模式。艺术类别之间也可重叠；CA不进行基于独立人数的显著性检验。

## 验证状态

本地7项测试通过，包括17个单类别与全部类别的回调、图表JSON和应用HTTP接口。浏览器视觉检查未完成：本地Chromium运行受限，云浏览器预览被自动审批拒绝。因此发布的是已通过计算与接口测试的实现，仍需在个人电脑检查实际字体、底图加载和小屏显示。

如部署到支持Python的主机，可用 `gunicorn app:server --bind 0.0.0.0:8050`（Linux/macOS）。本次仅提交项目到GitHub，未开通任何付费托管或对外运行服务。
