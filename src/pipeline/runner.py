from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from src.data.models import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    stock_code: str
    success: bool
    result: AnalysisResult | None = None
    error: str = ""


_provider = None
_registry = None
_scorer = None


def _get_provider(no_cache: bool = False):
    global _provider
    if _provider is None:
        from src.data.provider import DataProvider

        _provider = DataProvider(no_cache=no_cache)
    return _provider


def _get_registry():
    global _registry
    if _registry is None:
        from src.strategy.registry import StrategyRegistry

        _registry = StrategyRegistry()
    return _registry


def _get_scorer():
    global _scorer
    if _scorer is None:
        from src.scoring.engine import FiveDimensionScorer

        _scorer = FiveDimensionScorer()
    return _scorer


async def run_pipeline(
    stock_code: str, mode: str = "quick", no_cache: bool = False
) -> PipelineResult:
    try:
        from src.agents.reflection import verify_decisions
        from src.llm.client import analyze
        from src.llm.parsers import parse_analysis
        from src.llm.prompts import STOCK_ANALYSIS_TEMPLATE
        from src.strategy.builtin.ma_cross import compute_ma
        from src.strategy.builtin.rsi_oversold import compute_rsi

        provider = _get_provider(no_cache=no_cache)

        # Verify past decisions against current prices (fire-and-forget)
        try:
            await verify_decisions(provider)
        except Exception:
            logger.warning("Decision verification failed, continuing analysis")

        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=60)).isoformat()

        daily_data = provider.get_daily_data(stock_code, start_date, end_date)
        if not daily_data:
            return PipelineResult(stock_code=stock_code, success=False, error="No data available")

        info = provider.get_stock_info(stock_code)
        if info is None:
            from src.data.models import StockInfo

            info = StockInfo(code=stock_code, name="Unknown")

        registry = _get_registry()
        signals = registry.run_all(stock_code, daily_data)

        scorer = _get_scorer()
        score_result = scorer.score(info, daily_data)

        prices = [d.close for d in daily_data]
        ma5_vals = compute_ma(prices, 5)
        ma20_vals = compute_ma(prices, 20)
        rsi = compute_rsi(prices)

        prompt = STOCK_ANALYSIS_TEMPLATE.format(
            stock_code=stock_code,
            stock_name=info.name,
            current_price=prices[-1],
            ma5=f"{ma5_vals[-1]:.2f}" if ma5_vals[-1] else "N/A",
            ma20=f"{ma20_vals[-1]:.2f}" if ma20_vals[-1] else "N/A",
            rsi=f"{rsi:.2f}" if rsi else "N/A",
            macd_dif="N/A",
            macd_dea="N/A",
            pe_ratio=f"{info.pe_ratio:.2f}" if info.pe_ratio else "N/A",
            pb_ratio=f"{info.pb_ratio:.2f}" if info.pb_ratio else "N/A",
            roe=f"{info.roe:.2f}" if info.roe else "N/A",
            strategy_signals="\n".join(
                f"- {s.strategy_name}: {s.signal} (strength={s.strength:.2f})" for s in signals
            )
            or "No signals",
            total_score=f"{score_result.total:.1f}",
            technical_score=f"{score_result.technical:.1f}",
            capital_flow_score=f"{score_result.capital_flow:.1f}",
            fundamental_score=f"{score_result.fundamental:.1f}",
            sector_score=f"{score_result.sector:.1f}",
            event_score=f"{score_result.event:.1f}",
        )

        llm_output = await analyze(prompt)
        parsed = parse_analysis(llm_output)

        result = AnalysisResult(
            stock_code=stock_code,
            stock_name=info.name,
            current_price=prices[-1],
            score=score_result,
            strategy_signals=signals,
            llm_analysis=llm_output,
            recommendation=parsed.recommendation,
        )

        # Full mode: run multi-agent debate
        if mode == "full":
            from src.agents.orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator(lambda p, s: analyze(p, system=s))
            decision = await orchestrator.run_full_analysis(result, score_result)
            result.recommendation = decision.recommendation.value
            factors = ", ".join(decision.key_factors)
            result.llm_analysis = (
                f"## 多角色辩论决策\n\n{decision.reasoning}\n\n"
                f"**风险提示**: {decision.risk_notes}\n"
                f"**建议仓位**: {decision.position_pct}%\n"
                f"**关键因素**: {factors}"
            )

        # Generate Markdown report
        try:
            from src.report.generator import generate_report

            report_path = generate_report(result)
            logger.info(f"Report saved: {report_path}")
        except Exception:
            logger.warning("Report generation failed")

        return PipelineResult(stock_code=stock_code, success=True, result=result)
    except Exception as e:
        logger.error(f"Pipeline failed for {stock_code}: {e}", exc_info=True)
        return PipelineResult(
            stock_code=stock_code, success=False, error="Pipeline execution failed"
        )


def run_pipeline_sync(
    stock_code: str, mode: str = "quick", no_cache: bool = False
) -> PipelineResult:
    return asyncio.run(run_pipeline(stock_code, mode, no_cache=no_cache))
