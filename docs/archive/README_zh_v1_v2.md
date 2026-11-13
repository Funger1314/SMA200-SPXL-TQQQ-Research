# 第二轮审稿修订 v2

**状态：新的模型和离线测试已完成，但融资成本/分红修正后的整段回测尚未完整重算；旧版收益数字不能冒充新版。**

关键材料：[审稿意见逐项答复](REVIEWER_RESPONSE.md)、[新版英文论文 PDF](paper/SMA200_Review_Revision_v2.pdf)、[新版 Word](paper/SMA200_Review_Revision_v2.docx)。

新增：FRED 前月末 DTB3 无前视现金利息、合成 3× ETF 两倍融资成本、复权调整、重叠日 1bp 校验、SPY/QQQ 1× 对照、平均仓位配比的 3×/现金组合、固定 30% 波动目标策略、风险指标（Sharpe/Calmar/CVaR/CDaR/Ulcer）、逐笔进出及滚动起点；风险 Bootstrap 在旧的月度净值上运行，只是补充证据，不能替代日线。

运行：`pip install -r requirements.txt` → `python -m pytest -q` → `python scripts/reviewer_risk_bootstrap.py` → `python scripts/fetch_data.py` → `python scripts/review_revision.py --tail-mode public`。若跨数据商的价格衔接差异超过 1bp，程序会直接报错，必须统一数据来源再重算。

---

# SPXL / TQQQ 的 200 日均线策略研究

这是一份准备公开到 GitHub 的**探索性量化研究**，论文位于 [`paper/SMA200_Leveraged_ETF_Research.pdf`](paper/SMA200_Leveraged_ETF_Research.pdf)。它不是前瞻预注册实验，也不能证明策略有显著 Alpha。

**规则保持不变：** SPY 指示 SPXL；QQQ 指示 TQQQ。信号只用未加杠杆 ETF 的 **SMA200**。收盘达到 SMA200 的 **104%**，下一交易日开盘买入目标总资产的 20%，连续满足则增加至 40%、60%、80%、100%；收盘跌破 SMA200 的 **97%**，下一交易日开盘全清；位于缓冲区间时维持原持仓。每次买卖按成交金额扣 0.10%（手续费假设 0.05% + 滑点假设 0.05%）；不计税、空仓利息、SGOV。

**2010-02-11 至 2026-11-12（两只杠杆 ETF 均已上市）**：SPXL 版本 CAGR **21.14%**、最大日度回撤 **-52.88%**，TQQQ 版本 CAGR **26.93%**、最大日度回撤 **-62.09%**。同期各自 ETF 买入持有 CAGR **28.94%** 和 **40.91%**，因此 SMA200 版本的主要历史价值是**控制部分回撤，而非跑赢买入持有收益**。

**1999-12-22 至 2026-11-12（含上市前模拟）**：SPXL 版本 CAGR **15.38%**、最大回撤 **-52.88%**；TQQQ 版本 CAGR **13.70%**、最大回撤 **-90.49%**。上市前只是用标的 ETF 日收益近似构造三倍杠杆，不能视为真实基金可交易历史。由于 QQQ 成立于 1999 年 3 月，需先形成完整 200 个交易日均线，公平起点为 1999 年 12 月。

**过拟合与后视镜效应：** 2010 年以后每只标的测试了 27 个相邻参数，虽然 CAGR 都为正，但它们大多处于美股长期牛市，且参数是事后选择的。SPY 与 QQQ 都属于高度相关的美股资产，不能据此宣称跨资产普适性。2018 年之后的拆分只能算伪样本外，真正检验需要将规则冻结后再运行未来样本，并公开记录每次调整和失败的参数尝试。

**运行方法：**

```bash
pip install -r requirements.txt
python -m pytest -q
python scripts/reproduce.py --fetch
```

GitHub 公开版本内包含论文、收益和回撤图、各类 CSV 统计结果、完整回测代码及测试。**完整原始第三方行情文件不直接分发**：因 Yahoo Finance、IBKR 市场数据可能有再分发限制，我们提供上游来源、校验哈希和下载脚本，由运行者在合规范围内自行获取。保存的 `data/results/monthly_equity_*.csv` 是由实际日度回测净值抽样得到的月末结果，非原始价格。

完整风险、数据口径差异以及如何扩展为可发表的研究，请阅读英文论文和 `LIMITATIONS.md`。
