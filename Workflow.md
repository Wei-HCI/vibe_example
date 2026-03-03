# rCode 项目自动化统计分析与 APA 报告工作流

本手册详细记录了基于 `rCode` R 语言工具包进行数据清理、统计检验及学术报告生成的标准化流程。

---

## 1. 分步骤说明

### 第一步：环境初始化 (Setup)
在 R 脚本开头调用配置函数，确保全局环境符合分析要求（包括冲突处理、数值精度和绘图主题）。

### 第二步：数据预处理 (Data Preprocessing)
导入原始数据并进行清洗，重点在于长宽表转换（Long-to-Wide / Wide-to-Long）以及异常值处理，确保格式符合 `ggstatsplot` 的要求。

### 第三步：假设检验 (Assumptions Check)
在执行方差分析（ANOVA）前，系统自动运行 Shapiro-Wilk 正态性检验。根据 $p$ 值结果，工作流将自动在参数化检验（Parametric）与非参数化检验（Non-parametric）之间切换。

### 第四步：统计分析与可视化 (Analysis & Viz)
执行核心统计函数，生成包含显著性标记（Asterisks）和统计参数（$F$, $p$, $\eta_p^2$）的学术图表。

### 第五步：生成 APA 报告 (Reporting)
导出符合 APA 格式的 LaTeX 文本，直接用于论文写作。

---

## 2. 核心 Prompts (提示词)

在开发与数据分析过程中，以下提示词用于引导 AI 准确执行任务：

- **理解项目上下文：**
  > "请阅读 `DESCRIPTION` 和 `README.md` 文件，总结 `rCode` 包的核心功能和依赖关系。"
- **函数逻辑分析：**
  > "分析 `r_functionality.R` 中关于 `*WithPriorNormalityCheck` 的逻辑，解释它是如何自动选择统计检验方法的。"
- **错误排查：**
  > "当 `geom_signif` 报错 'groups should have 2 elements' 时，请检查我的输入数据列是否存在多余的 Level。"

---

## 3. 代码示例

### 3.1 自动化环境配置
```r
# 加载 rCode 并初始化环境
library(rCode)
rcode_setup()
```

### 3.2 带正态性检查的组间分析
```r
# 自动根据分布选择 t-test 或 Mann-Whitney U 检验，并生成带星号的图表
ggbetweenstatsWithPriorNormalityCheckAsterisk(
  data = survey_data,
  x = Condition,         # 自变量
  y = Score,             # 因变量
  ylab = "Task Score",
  type = "auto"          # 自动选择检验类型
)
```

### 3.3 生成 LaTeX 格式的 APA 报告
```r
# 运行非参数方差分析并获取报告
res <- np.anova(Score ~ Condition * Device + Error(ID/Condition), data = df)
reportNPAV(res, "Task Completion Time")
```

---

## 4. AI 生成的解释

### 关于自动切换逻辑
AI 解释到，`rCode` 通过封装 `shapiro.test`，当 $p < .05$ 时，内部逻辑会自动将 `type` 参数由 `"p"` (Parametric) 更改为 `"np"` (Non-parametric)，从而避免了人工判断的误判风险。

### 可视化增强
AI 指出，该工作流利用 `ggstatsplot` 作为底层，但通过自定义函数解决了原包在多重比较时显著性标记（Significance Bars）难以自动对齐的问题。

---

## 5. 可视化图表

- **主效应/交互作用图：** 通过 `generateEffectPlot` 生成，用于展示不同实验条件下因变量的变化趋势。
- **统计推断图：** 包含贝叶斯因子（Bayes Factor）和效应量估计，图表上方自动标注显著性星号。

---

## 6. 已知局限与 Troubleshooting

### 常见问题与解决方案

| 问题现象 | 可能原因 | 解决方法 |
| --- | --- | --- |
| LaTeX 报错 `\F undefined` | 缺少宏定义 | 在 LaTeX 导言区添加：`\newcommand{\F}[3]{$F({#1},{#2})={#3}$}` |
| `filter` 函数报错 | 包冲突 | 确保先运行 `rcode_setup()`，或使用 `dplyr::filter()` 显式调用 |
| 显著性连线错位 | 分组超过 3 个 | *Asterisk 系列函数对多组数据支持有限，建议手动调整 `step_increase` 参数 |

### 排错建议

- **检查数据类型：** 确保自变量（`x`）是 `factor` 类型，因变量（`y`）是 `numeric` 类型。
- **更新依赖：** 若图表渲染异常，请运行 `update.packages(c("ggstatsplot", "ggplot2"))`。
- **剪贴板错误：** Windows 用户若无法自动复制报告，请检查是否安装了 `clipr` 包。

