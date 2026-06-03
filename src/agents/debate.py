from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from src.agents.schemas import DebateState, RiskDebateState

logger = logging.getLogger(__name__)

LLMFunc = Callable[[str, str], Awaitable[str]]


async def bull_bear_debate(
    analysis_summary: str,
    llm_call: LLMFunc,
    max_rounds: int = 2,
) -> str:
    state = DebateState(max_rounds=max_rounds)

    for round_num in range(max_rounds):
        bull_prompt = f"""你是多头分析师。请基于以下分析数据，论证为什么应该买入该股票。

## 分析数据
{analysis_summary}

## 之前的讨论
{state.bull_history}
{state.bear_history}

请给出你的论据（3-5个要点）。"""

        bull_response = await llm_call(bull_prompt, "你是一位看涨的股票分析师。")
        state.bull_history += f"\n[多头 第{round_num + 1}轮]: {bull_response}"

        bear_prompt = f"""你是空头分析师。请基于以下分析数据，论证为什么不应该买入该股票。

## 分析数据
{analysis_summary}

## 之前的讨论
{state.bull_history}
{state.bear_history}

请给出你的反驳（3-5个要点）。"""

        bear_response = await llm_call(bear_prompt, "你是一位看跌的股票分析师。")
        state.bear_history += f"\n[空头 第{round_num + 1}轮]: {bear_response}"

        state.count += 1

    synthesis_prompt = f"""你是研究经理。请综合多空双方的辩论，给出最终判断。

## 多头论据
{state.bull_history}

## 空头论据
{state.bear_history}

请给出: 1.综合判断 2.关键分歧点 3.你的倾向"""

    return await llm_call(synthesis_prompt, "你是一位资深研究经理，负责综合多空观点做出最终判断。")


async def risk_debate(
    decision_summary: str,
    llm_call: LLMFunc,
    max_rounds: int = 1,
) -> str:
    state = RiskDebateState(max_rounds=max_rounds)

    roles = {
        "risky": ("激进派", "你倾向于高风险高收益，愿意承担更大风险获取更高回报。"),
        "safe": ("保守派", "你倾向于低风险稳健收益，优先保护本金安全。"),
        "neutral": ("中立派", "你平衡风险和收益，追求风险调整后的最优回报。"),
    }

    for _round_num in range(max_rounds):
        for key, (name, system) in roles.items():
            history_field = f"{key}_history"
            all_history = f"{state.risky_history}\n{state.safe_history}\n{state.neutral_history}"

            prompt = f"""你是{name}。请从你的角度评估以下投资决策。

## 决策摘要
{decision_summary}

## 之前的讨论
{all_history}

请给出你的观点和建议。"""

            response = await llm_call(prompt, system)
            setattr(state, history_field, getattr(state, history_field) + f"\n{name}: {response}")

        state.count += 1

    judge_prompt = f"""你是风控总监。请综合三方观点，给出最终风险评估。

## 激进派观点
{state.risky_history}

## 保守派观点
{state.safe_history}

## 中立派观点
{state.neutral_history}

请给出: 1.风险等级(低/中/高) 2.建议仓位 3.止损建议 4.风险提示"""

    return await llm_call(judge_prompt, "你是风控总监，负责综合各方观点做出最终风险评估。")
