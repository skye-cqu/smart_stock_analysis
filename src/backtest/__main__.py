from __future__ import annotations

import argparse

from src.backtest.engine import run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(description="A股回测引擎")
    parser.add_argument("--stock", required=True, help="股票代码，如 000001")
    parser.add_argument("--start", required=True, help="开始日期，如 2024-01-01")
    parser.add_argument("--end", required=True, help="结束日期，如 2024-12-31")
    parser.add_argument("--strategy", default="ma_cross", help="策略名称，默认 ma_cross")
    parser.add_argument("--capital", type=float, default=100_000, help="初始资金，默认 100000")
    args = parser.parse_args()

    result = run_backtest(
        stock_code=args.stock,
        start_date=args.start,
        end_date=args.end,
        strategy_name=args.strategy,
        initial_capital=args.capital,
    )

    if not result.trades:
        print("无交易记录")
        return

    print(f"\n{'=' * 50}")
    print(f"回测结果: {args.stock} ({args.start} ~ {args.end})")
    print(f"策略: {args.strategy}")
    print(f"{'=' * 50}")
    print(f"交易次数: {len(result.trades)}")
    print(f"总收益率: {result.total_return:.2%}")
    print(f"年化收益: {result.annual_return:.2%}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"胜率:     {result.win_rate:.2%}")
    print(f"{'=' * 50}")

    print("\n交易明细:")
    print(f"{'日期':<12} {'方向':<6} {'价格':>10} {'数量':>8} {'金额':>12}")
    print("-" * 50)
    for t in result.trades:
        direction_cn = "买入" if t.direction == "buy" else "卖出"
        print(f"{t.date:<12} {direction_cn:<6} {t.price:>10.3f} {t.shares:>8} {t.cost:>12.2f}")


if __name__ == "__main__":
    main()
