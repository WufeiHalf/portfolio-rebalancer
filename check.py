#!/usr/bin/env python3
"""每日再平衡检查 —— 非交互入口，给 cron / agent 用。

规则（2026-09 与持有者约定）：
  分桶目标   股(EQ) 40% / 金(GOLD) 30% / 债(BOND) 30%
  偏离带     任一桶 |当前权重 - 目标权重| > 8 个百分点 → 触发
  最小交易额 单桶调整金额 < 总资产 2% → 视为噪声，不触发
  调节资产   EQ 桶动 510300；GOLD/BOND 各自唯一成员
  检查频率   每交易日收盘后；时间条件（每半年强制全检）由调用方安排

输出：人可读报告；触发时 exit 1（cron 可据此发提醒），一切正常 exit 0。
"""
import sys
from portfolio import load_portfolio_from_csv
from data_fetcher import fetch_current_prices
from rebalance import minimal_rebalance

CSV_PATH = "my_portfolio.csv"
BAND = 0.08          # 偏离带：8 个百分点
MIN_TRADE = 0.02     # 最小交易额：总资产的 2%
GROUP_NAMES = {"EQ": "股票", "GOLD": "黄金", "BOND": "债券"}


def main() -> int:
    portfolio = load_portfolio_from_csv(CSV_PATH)
    assets = portfolio.get_assets()
    prices = fetch_current_prices(assets)

    missing = [a.ticker for a in assets if prices.get(a.ticker) in (None, 0)]
    if missing:
        print(f"⛔ 行情获取失败: {missing}，本次不判断（宁可不动作，不可用脏数据）")
        return 2

    total = sum(prices[a.ticker] * a.shares for a in assets)

    # 各桶权重 vs 目标
    groups = portfolio.by_group()
    target_total = sum(a.target_allocation for a in assets)
    lines, triggered = [], []
    for gname, gassets in sorted(groups.items()):
        value = sum(prices[a.ticker] * a.shares for a in gassets)
        cur = value / total
        tgt = sum(a.target_allocation for a in gassets) / target_total
        drift = cur - tgt
        marker = "⚠️" if abs(drift) > BAND else "✓"
        lines.append(
            f"  {marker} {GROUP_NAMES.get(gname, gname):>2} {cur:7.1%} "
            f"(目标 {tgt:.0%}, 偏离 {drift:+.1%})"
        )
        if abs(drift) > BAND:
            triggered.append((gname, abs(drift) * total))

    print(f"总资产 {total:,.0f} CNY（{len(assets)} 只持仓）")
    print("\n".join(lines))

    # 噪声过滤：偏离超带但调整额不足最小交易额 → 不建议动作
    real = [(g, v) for g, v in triggered if v >= MIN_TRADE * total]
    for g, v in triggered:
        if v < MIN_TRADE * total:
            print(f"ℹ️ {GROUP_NAMES.get(g, g)} 桶越带但调整额 {v:,.0f} < 最小交易额"
                  f" {MIN_TRADE * total:,.0f}，忽略")

    if not real:
        print("✅ 全部在带内（±8pp），无需操作。纪律：不动就是最优操作。")
        return 0

    suggestions = minimal_rebalance(portfolio, prices, "CNY", threshold=BAND)
    print("🔔 触发再平衡，建议（次日开盘执行，不挑时点）：")
    LOT = 100  # A股 ETF 最小交易单位：一手 = 100 份，必须整数倍下单
    for s in suggestions:
        raw = s["shares"]
        if s["action"] == "SELL":
            # 卖出向下取整手：宁可少卖，不可超卖
            snapped = raw // LOT * LOT
        else:
            # 买入四舍五入到整手，兼顾补齐目标与不过度买入
            snapped = round(raw / LOT) * LOT
        if snapped < LOT:
            print(f"  ℹ️ {s['ticker']} 建议 {raw:.0f} 份，不足一手（{LOT} 份）→ 放弃该笔。"
                  f"资金体量小、粒度粗，建议用新增资金分批补，而不是硬拆卖单")
            continue
        print(f"  {'买入' if s['action'] == 'BUY' else '卖出'} {s['ticker']}"
              f" {snapped:.0f} 份（{s['from']:.0f} → {s['from'] + snapped if s['action'] == 'BUY' else s['from'] - snapped:.0f} 份）")
    print("提醒：卖出前确认可用股数（T+1）；单桶动作一次到位，不分批。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
