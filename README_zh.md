# Super Analyze

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Active-2ea44f.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20WSL2%20%7C%20Linux-6A6A6A)

`Super Analyze` 是一个面向实验数据的 **human-in-the-loop** 统计分析助手。

它通过自动识别、显式确认节点和可追踪产物，将原始实验数据转为可复现的分析工作流。

<p align="center">
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/English-switch-1f6feb?style=for-the-badge" /></a>
  <a href="README_zh.md"><img alt="中文" src="https://img.shields.io/badge/中文-当前-111827?style=for-the-badge" /></a>
</p>

---

## 目录

- [项目是什么](#项目是什么)
- [功能卡片](#功能卡片)
- [安装](#安装)
- [使用方式](#使用方式)
- [分析流程](#分析流程)
- [方法映射](#方法映射)
- [输出产物](#输出产物)
- [支持的问卷](#支持的问卷)
- [关于 rcode](#关于-rcode)
- [贡献](#贡献)
- [许可](#许可)

---

## 项目是什么

`Super Analyze` 的目标是降低实验数据处理中的重复劳动，并提升决策可追溯性。

- 自动识别问卷类型与实验设计。
- 在关键环节（检测结果、方法选择）强制用户确认。
- 输出可复现脚本和可复审的分析结果。

核心目标：**更少重复操作、更高复现性、更清晰的决策链路**。

---

## 功能卡片

| 功能 | 作用 |
|---|---|
| **智能识别** | 自动识别 `IPQ`、`SSQ`、`SUS`、`NASA-TLX`（或通用）数据结构、被试列、条件列与 DV。 |
| **双确认机制** | 检测与方法选择均需用户确认，避免自动化误判直接进入分析。 |
| **方法推荐** | 针对每个因变量给出参数检验与非参数替代方案。 |
| **可追溯脚本** | 输出 `analyze_<dataset>.py`，并标注每个模块来源（`rcode` / fallback）。 |
| **插件集成** | 与 Claude Code 命令联动，可直接进行对话式分析。 |
| **统一产物** | 一次运行输出清洗文件、摘要和图像，便于版本管理。 |

---

## 安装

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 注册 Claude Code 插件

```bash
/plugin marketplace add <你的仓库路径>
/plugin install super-analysis@vibe-example-local
```

示例：

```bash
/plugin marketplace add C:/Users/adminroot/Documents/GitHub/vibe_example
/plugin install super-analysis@vibe-example-local
```

---

## 使用方式

### 方式一（推荐）：Claude 命令

```bash
/super-analysis:run text_dataset/ipq.csv
# 或简写
/super-analysis text_dataset/ipq.csv
```

### 方式二：直接 CLI 调用

```bash
python .\scripts\super_analyze.py scan path/to/dataset.csv
python .\scripts\super_analyze.py recommend path/to/dataset.csv
```

若存在虚拟环境，优先使用：

```bash
.\myenv\Scripts\python.exe .\scripts\super_analyze.py scan path/to/dataset.csv
```

---

## 分析流程

```text
数据文件 → 检测 → 确认 → 预处理 → 假设检验与建议 → 确认 → 生成脚本与产物
```

### 第 1 阶段：自动检测

- 自动识别问卷类型及相关字段。
- 推断实验设计：组内/组间、单因素/多因素。

### 第 2 阶段：确认 1

- 用户确认或修正检测结果。

### 第 3 阶段：预处理

- 根据可用能力先行打分/清洗并保存中间结果。

### 第 4 阶段：假设检验与推荐

- 输出每个因变量的描述性统计、假设检查与方法建议。

### 第 5 阶段：确认 2

- 用户确认推荐方法，或改选备选方法。

### 第 6 阶段：结果生成

- 输出脚本、清洗文件与摘要，完成一次可复查交付。

---

## 方法映射

| 设计 | 参数检验 | 非参数检验 |
|---|---|---|
| 两条件、被试内 | 配对 t 检验 | Wilcoxon 符号秩检验 |
| 两条件、被试间 | 独立样本 t 检验 | Mann–Whitney U |
| 多条件、被试内 | 重复测量 ANOVA | Friedman |
| 多条件、被试间 | 单因素 ANOVA | Kruskal-Wallis |
| 多因素 | 二/多因子 ANOVA（或等效模型） | ART 或非参数替代 |

---

## 输出产物

| 文件 | 用途 |
|---|---|
| `analyze_<dataset>.py` | 可追溯分析脚本 |
| `<dataset_stem>_cleaned_scored.csv` | 清洗/打分后的数据 |
| `<dataset_stem>_analysis_summary.txt` | 分析摘要 |
| `figures/*.png` | 自动生成图表 |

---

## 支持的问卷

- `IPQ`、`SSQ`、`SUS`：优先使用 `rcode` 的打分函数。
- `NASA-TLX`：在缺少专用包装函数时走本地 fallback 路径。
- 通用数据：跳过问卷评分，直接进入统计流程。

---

## 关于 rcode

`Super Analyze` 负责流程编排，`rcode` 负责统计计算、检查和报告工具。

完整能力与函数说明见：[README-rcode.md](README-rcode.md)。

---

## 贡献

- 遵循 `.claude-plugin/` 和 `commands/` 的插件行为约定。
- 修改工作流时补充示例、用例和说明。
- 保持文档与命令、产物说明同步更新。

---

## 许可

MIT.

---
