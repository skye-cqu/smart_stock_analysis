from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from src.agents.debate import bull_bear_debate, risk_debate
from src.agents.memory import TradingMemoryLog
from src.agents.quality_gate import run_quality_gate
from src.agents.roles import ALL_ANALYSTS
from src.agents.schemas import AnalystReport, PortfolioDecision, Recommendation
from src.data.models import AnalysisResult, ScoreResult

logger = logging.getLogger(__name__)

LLMFunc = Callable[[str, str], Awaitable[str]]


class AgentOrchestrator:
    def __init__(self, llm_call: LLMFunc):
        self.llm_call = llm_call
        self.memory = TradingMemoryLog()

    async def run_full_analysis(
        self,
        result: AnalysisResult,
        score: ScoreResult,
    ) -> PortfolioDecision:
        stock_code = result.stock_code
        stock_name = result.stock_name
        logger.info(f"Starting full analysis for {stock_name} ({stock_code})")

        # Step 1: Get past context
        past_context = self.memory.get_past_context(stock_code)

        # Step 2: Run 7 analysts in parallel
        logger.info("Running 7 analysts in parallel...")
        analyst_factory = [fn(self.llm_call) for fn in ALL_ANALYSTS]
        reports = await asyncio.gather(
            *[fn(result, score) for fn in analyst_factory],
            return_exceptions=True,
        )
        valid_reports = [r for r in reports if isinstance(r, AnalystReport)]
        logger.info(f"Got {len(valid_reports)} analyst reports")

        # Step 3: Quality gate
        quality = await run_quality_gate(valid_reports, self.llm_call)
        logger.info(f"Quality gate: {quality.grade} ({quality.score:.0f})")

        # Step 4: Build analysis summary for debate
        summary = f"## 股票: {stock_name} ({stock_code})\n"
        summary += f"## 价格: {result.current_price} | 评分: {score.total:.1f}/100\n\n"
        for r in valid_reports:
            summary += f"### {r.role} [{r.signal}] (信心度: {r.confidence})\n{r.analysis}\n\n"
        if past_context:
            summary += f"\n{past_context}"

        # Step 5: Bull/Bear debate
        logger.info("Starting bull/bear debate...")
        debate_result = await bull_bear_debate(summary, self.llm_call)

        # Step 6: Risk debate
        logger.info("Starting risk debate...")
        risk_result = await risk_debate(debate_result, self.llm_call)

        # Step 7: Final decision
        logger.info("Making final decision...")
        final_prompt = f"""你是投资总监。请基于以下所有分析，做出最终投资决策。

## 分析师报告摘要
{summary}

## 多空辩论结果
{debate_result}

## 风险评估
{risk_result}

## 质量评级: {quality.grade} ({quality.score:.0f})

用JSON格式返回:
{{"recommendation": "买入/持有/卖出", "confidence": 0.0-1.0, "position_pct": 0-100, "reasoning": "决策理由", "risk_notes": "风险提示", "key_factors": ["因素1", "因素2"]}}"""

        raw = await self.llm_call(final_prompt, "你是投资总监，负责做出最终投资决策。")
        try:
            import json

            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            data = json.loads(raw.strip())
            decision = PortfolioDecision(**data)
        except Exception as e:
            logger.warning(f"Failed to parse final decision: {e}")
            decision = PortfolioDecision(
                recommendation=Recommendation.HOLD,
                confidence=0.3,
                position_pct=0,
                reasoning=raw[:300],
                risk_notes="决策解析失败，建议保守操作",
            )

        # Step 8: Store decision in memory
        self.memory.store_decision(
            stock_code=stock_code,
            stock_name=stock_name,
            recommendation=decision.recommendation.value,
            price=result.current_price,
            reasoning=decision.reasoning,
        )

        logger.info(
            f"Final decision: {decision.recommendation.value} (confidence: {decision.confidence})"
        )
        return decision
