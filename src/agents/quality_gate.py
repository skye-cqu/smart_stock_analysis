from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from src.agents.schemas import AnalystReport, QualityGrade

logger = logging.getLogger(__name__)

LLMFunc = Callable[[str, str], Awaitable[str]]


def code_check(reports: list[AnalystReport]) -> dict:
    issues = []
    for r in reports:
        if len(r.analysis) < 50:
            issues.append(f"{r.role}: 分析内容过短")
        if r.confidence < 0.2:
            issues.append(f"{r.role}: 信心度过低 ({r.confidence})")
        if not r.key_points:
            issues.append(f"{r.role}: 缺少关键要点")
    score = max(0, 100 - len(issues) * 15)
    return {"score": score, "issues": issues}


async def llm_check(reports: list[AnalystReport], llm_call: LLMFunc) -> QualityGrade:
    reports_text = "\n\n".join(
        f"### {r.role}\n信号: {r.signal} | 信心度: {r.confidence}\n{r.analysis}" for r in reports
    )
    prompt = f"""请评估以下分析师报告的质量。

{reports_text}

用JSON格式返回:
{{"grade": "A/B/C/D/F", "score": 0-100, "issues": ["问题1"], "summary": "总结"}}"""

    raw = await llm_call(prompt, "你是一位质量审核员，负责评估分析师报告的质量和一致性。")
    try:
        import json

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        data = json.loads(raw.strip())
        return QualityGrade(**data)
    except Exception:
        return QualityGrade(grade="C", score=50, issues=["LLM质量检查解析失败"], summary=raw[:200])


async def run_quality_gate(
    reports: list[AnalystReport],
    llm_call: LLMFunc,
) -> QualityGrade:
    code_result = code_check(reports)
    if code_result["score"] < 50:
        return QualityGrade(
            grade="D",
            score=code_result["score"],
            issues=code_result["issues"],
            summary="代码层质量检查未通过",
        )
    llm_grade = await llm_check(reports, llm_call)
    avg_score = (code_result["score"] + llm_grade.score) / 2
    all_issues = code_result["issues"] + llm_grade.issues
    return QualityGrade(
        grade=llm_grade.grade,
        score=avg_score,
        issues=all_issues,
        summary=llm_grade.summary,
    )
