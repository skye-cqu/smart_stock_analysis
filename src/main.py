from __future__ import annotations

import argparse
import logging
import sys

from src.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Smart Stock Analysis")
    parser.add_argument("--stock", type=str, help="Stock code to analyze")
    parser.add_argument(
        "--mode",
        type=str,
        default="quick",
        choices=["quick", "full"],
        help="Analysis mode: quick=single LLM, full=multi-agent debate",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached data if available (default: always fetch fresh data)",
    )
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    if not args.stock:
        parser.error("--stock is required")

    logger.info(f"Analyzing {args.stock} in {args.mode} mode")

    from src.pipeline.runner import run_pipeline_sync

    result = run_pipeline_sync(args.stock, args.mode, no_cache=not args.use_cache)

    if result.success and result.result:
        r = result.result
        print(f"\n=== {r.stock_name} ({r.stock_code}) ===")
        print(f"Price: {r.current_price}")
        print(f"Score: {r.score.total:.1f}/100")
        print(f"Recommendation: {r.recommendation}")
        print("\nSignals:")
        for s in r.strategy_signals:
            print(f"  {s.strategy_name}: {s.signal} ({s.strength:.0%})")
        if args.mode == "full":
            print("\n--- Multi-Agent Analysis ---")
            print(r.llm_analysis)
        if settings.notification.feishu_webhook_url:
            from src.notifications.feishu import FeishuNotifier

            FeishuNotifier().send(r)
    else:
        print(f"Analysis failed: {result.error}")


if __name__ == "__main__":
    main()
