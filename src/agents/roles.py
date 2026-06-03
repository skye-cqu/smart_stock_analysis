from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from src.agents.schemas import AnalystReport
from src.data.models import AnalysisResult, ScoreResult

logger = logging.getLogger(__name__)

LLMFunc = Callable[[str, str], Awaitable[str]]


def _build_system_prompt(role: str, description: str) -> str:
    return f"""你是一位{role}。{description}

请用中文分析，输出JSON格式:
{{"analysis": "详细分析", "signal": "看涨/看跌/中性", "confidence": 0.0-1.0, "key_points": ["要点1", "要点2"]}}
"""


def create_analyst(role: str, description: str, focus: str):
    def factory(llm_call: LLMFunc):
        async def analyze(result: AnalysisResult, score: ScoreResult) -> AnalystReport:
            prompt = f"""## 股票: {result.stock_name} ({result.stock_code})
## 当前价格: {result.current_price}
## 综合评分: {score.total:.1f}/100
## 技术面: {score.technical:.1f} | 资金流: {score.capital_flow:.1f} | 基本面: {score.fundamental:.1f}
## 策略信号:
{chr(10).join(f"- {s.strategy_name}: {s.signal} ({s.strength:.0%})" for s in result.strategy_signals) or "无信号"}

请从{focus}角度进行分析。"""
            system = _build_system_prompt(role, description)
            raw = await llm_call(prompt, system)
            try:
                import json

                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0]
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0]
                data = json.loads(raw.strip())
                return AnalystReport(
                    role=role,
                    analysis=data.get("analysis", ""),
                    signal=data.get("signal", "中性"),
                    confidence=float(data.get("confidence", 0.5)),
                    key_points=data.get("key_points", []),
                )
            except Exception as e:
                logger.warning(f"Failed to parse {role} output: {e}")
                return AnalystReport(role=role, analysis=raw[:300], signal="中性", confidence=0.3)

        return analyze

    return factory


# 7 analyst roles
create_technical_analyst = create_analyst(
    "技术分析师", "专注于K线形态、均线系统、MACD、RSI、KDJ等技术指标分析。", "技术面"
)

create_fundamental_analyst = create_analyst(
    "基本面分析师", "专注于PE/PB/ROE、营收增长、行业地位、估值合理性分析。", "基本面"
)

create_news_analyst = create_analyst(
    "新闻分析师", "专注于市场情绪、新闻事件、公告影响分析。", "消息面"
)

create_policy_analyst = create_analyst(
    "政策分析师", "专注于宏观政策、行业监管、利率/汇率政策对股票的影响。", "政策面"
)

create_hot_money_analyst = create_analyst(
    "游资分析师", "专注于主力资金流向、北向资金、龙虎榜、大单分析。", "资金面"
)

create_lockup_analyst = create_analyst(
    "解禁分析师", "专注于限售股解禁、股东增减持、大宗交易分析。", "筹码面"
)

create_risk_manager = create_analyst(
    "风控经理", "专注于风险评估、止损位设定、仓位建议、风险收益比分析。", "风险"
)

ALL_ANALYSTS = [
    create_technical_analyst,
    create_fundamental_analyst,
    create_news_analyst,
    create_policy_analyst,
    create_hot_money_analyst,
    create_lockup_analyst,
    create_risk_manager,
]
