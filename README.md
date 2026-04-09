# Super Analyze

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20WSL2%20%7C%20Linux-6A6A6A)

A **human-in-the-loop** statistical analysis agent for experimental datasets.

Super Analyze converts raw study data into a traceable analysis script through deterministic detection, transparent assumptions checks, and explicit user confirmations.

---

## 目录

- [概览](#概览)
- [功能一览（Feature Cards）](#功能一览feature-cards)
- [快速开始](#快速开始)
- [推荐用法（命令矩阵）](#推荐用法命令矩阵)
- [分析流程](#分析流程)
- [统计方法映射](#统计方法映射)
- [产物清单](#产物清单)
- [支持的问卷类型](#支持的问卷类型)
- [背后依赖：rcode](#背后依赖rcode)
- [贡献](#贡献)
- [许可](#许可)

---

## 概览

Super Analyze 适合需要重复、可复现、可审计统计流程的研究场景：

- 输入实验数据（CSV/Excel）
- 自动识别问卷与设计结构
- 人工确认关键假设与方法选择
- 生成可复用的分析脚本和汇总输出

核心目标是“**减少重复劳动、保留决策痕迹**”。

---

## 功能一览（Feature Cards）

| 🎯 能力卡 | 说明 |
|---|---|
| **自动识别引擎** | 自动探测问卷类型（`IPQ` / `SSQ` / `SUS` / `NASA-TLX` / 通用数据）、被试列、条件列、设计结构（组内/组间） |
| **双确认机制** | 关键节点（检测结果、方法选择）均需用户确认，避免“盲选模型” |
| **分层分析建议** | 在每个因变量上给出参数检验与非参数替代路径，带风险说明 |
| **脚本可追溯** | 产出的 `analyze_*.py` 清晰标注每段来源（`rcode` 还是本地 fallback） |
| **插件友好** | 内置 Claude Code 插件命令，无需重复配置复杂流程 |
| **轻量可复现** | 输出脚本、清洗文件、摘要与图表，便于版本管理与复核 |

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 2. 本地注册 Claude Code 插件

```bash
/plugin marketplace add C:/Users/adminroot/Documents/GitHub/vibe_example
/plugin install super-analysis@vibe-example-local
```

### 3. 运行分析

```bash
/super-analysis:run text_dataset/ipq.csv
# 或简写
/super-analysis text_dataset/ipq.csv
```

### 4. 直接调用 CLI

```bash
.\myenv\Scripts\python.exe .\scripts\super_analyze.py scan path/to/dataset.csv
.\myenv\Scripts\python.exe .\scripts\super_analyze.py recommend path/to/dataset.csv
```

本机未使用该虚拟环境时可改用 `python`。

---

## 推荐用法（命令矩阵）

| 场景 | 命令 | 说明 |
|---|---|---|
| 交互式一键分析 | `/super-analysis <数据路径>` | 面向 Claude Code 的推荐入口 |
| 仅检测结构 | `python scripts\super_analyze.py scan <数据路径>` | 获取自动检测摘要，便于快速预览 |
| 获取方法建议 | `python scripts\super_analyze.py recommend <数据路径>` | 获取逐 DV 的方法建议与假设结果 |
| 仅刷新环境 | `pip install -r requirements.txt` | 依赖更新后重装开发环境 |

> 说明：如需稳定运行请优先使用 `myenv` 下的 `python`。

---

## 分析流程

```text
输入数据 → 自动检测 → 人工确认 → 预处理 → 假设检测 → 人工确认 → 主分析 → 产物输出
```

### Phase 1：自动检测

- 探测问卷类型（`IPQ` / `SSQ` / `SUS` / `NASA-TLX` / 通用）
- 自动识别 subject / condition / DV 列
- 推断设计结构（within / between，单因素 / 多因素）

### Phase 2：确认节点

- 审核并修正自动检测到的结果，确认后继续

### Phase 3：预处理

- 以 `rcode` 工具函数优先打分与清洗
- 生成清洗后的中间数据文件

### Phase 4：假设检验与方法推荐

- 自动执行描述统计与常用分布/方差假设检查
- 每个因变量输出推荐分析方法与备选方案

### Phase 5：确认节点 2

- 对每个因变量确认推荐方法，或选择备选替代路径

### Phase 6：脚本与结果输出

- 生成可复现分析脚本与摘要，统一归档

---

## 统计方法映射

| 设计 | 参数方法 | 非参数方法 |
|---|---|---|
| 2 条件 / 被试内 | 配对 t 检验 | Wilcoxon 符号秩检验 |
| 2 条件 / 被试间 | 独立样本 t 检验 | Mann–Whitney U |
| 多条件 / 被试内 | 重复测量 ANOVA | Friedman |
| 多条件 / 被试间 | 单因素 ANOVA | Kruskal-Wallis |
| 多因素设计 | 二/多因子 ANOVA（或等效模型） | ART 或非参数替代 |

---

## 产物清单

| 文件 | 用途 |
|---|---|
| `analyze_<dataset>.py` | 追溯脚本（每段含来源说明） |
| `<dataset_stem>_cleaned_scored.csv` | 清洗/评分后的数据 |
| `analysis_summary.txt` | 结果与关键结论摘要 |
| `figures/*.png` | 自动生成图表 |

---

## 支持的问卷类型

- `IPQ` / `SSQ` / `SUS`：优先走 `rcode` 内置打分路径
- `NASA-TLX`：当前按本地 fallback 处理
- 通用数据：跳过问卷评分，直接进入描述统计与推断分析链路

---

## 背后依赖：rcode

`Super Analyze` 是工作流编排层，核心统计能力由 `rcode` 提供（打分、检验、报告与图形）。

完整统计工具说明见：[README-rcode.md](README-rcode.md)。

---

## 贡献

欢迎贡献：
- 在 `README-rcode.md` 里保持统计方法与实现行为一致；
- 在 `.claude-plugin/` 与 `commands/` 里保持插件约定；
- 改动后补充命令示例与行为说明，确保可复现。

---

## 许可

MIT License.
