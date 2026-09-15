# 我的自用再平衡工具

Fork 自 TimeMoneyCode/portfolio-rebalancer，改造为 A 股自用版：

- 行情源：腾讯接口（A 股 .SS/.SZ），yfinance 兜底
- `my_portfolio.csv`：持仓 + 桶目标（股 40% / 金 30% / 债 30%）
- `check.py`：每日非交互检查 —— ±8pp 偏离带 + 2% 最小交易额，越带才提醒

运行：

```bash
UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" \
  uv run --with yfinance --with requests --no-project python check.py
```

exit 0 = 带内无需操作；exit 1 = 触发再平衡（cron 可据此提醒）；exit 2 = 行情失败不判断。
