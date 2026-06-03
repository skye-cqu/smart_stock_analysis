from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.agents.quality_gate import code_check, run_quality_gate
from src.agents.schemas import AnalystReport


def _make_report(
    role: str = "技术分析师",
    analysis: str = "A" * 100,
    signal: str = "看涨",
    confidence: float = 0.7,
    key_points: list[str] | None = None,
) -> AnalystReport:
    if key_points is None:
        key_points = ["要点1", "要点2"]
    return AnalystReport(
        role=role,
        analysis=analysis,
        signal=signal,
        confidence=confidence,
        key_points=key_points,
    )


class TestCodeCheck:
    def test_all_pass(self):
        reports = [_make_report()]
        result = code_check(reports)
        assert result["score"] == 100
        assert result["issues"] == []

    def test_short_analysis(self):
        reports = [_make_report(analysis="短")]
        result = code_check(reports)
        assert result["score"] == 85
        assert any("过短" in i for i in result["issues"])

    def test_low_confidence(self):
        reports = [_make_report(confidence=0.1)]
        result = code_check(reports)
        assert result["score"] == 85
        assert any("信心度过低" in i for i in result["issues"])

    def test_missing_key_points(self):
        reports = [_make_report(key_points=[])]
        result = code_check(reports)
        assert result["score"] == 85
        assert any("缺少关键要点" in i for i in result["issues"])

    def test_multiple_issues_per_report(self):
        reports = [_make_report(analysis="短", confidence=0.1, key_points=[])]
        result = code_check(reports)
        assert result["score"] == 55  # 100 - 3*15
        assert len(result["issues"]) == 3

    def test_multiple_reports(self):
        reports = [
            _make_report(role="技术分析师", analysis="短"),
            _make_report(role="基本面分析师", analysis="短"),
        ]
        result = code_check(reports)
        assert result["score"] == 70  # 100 - 2*15
        assert len(result["issues"]) == 2

    def test_score_floor_zero(self):
        reports = [_make_report(analysis="短", confidence=0.05, key_points=[])] * 10
        result = code_check(reports)
        assert result["score"] >= 0

    def test_empty_reports(self):
        result = code_check([])
        assert result["score"] == 100
        assert result["issues"] == []


class TestRunQualityGate:
    @pytest.mark.asyncio
    async def test_low_code_score_skips_llm(self):
        reports = [
            _make_report(role="技术分析师", analysis="短", confidence=0.05, key_points=[]),
            _make_report(role="基本面分析师", analysis="短", confidence=0.05, key_points=[]),
        ]
        llm = AsyncMock(return_value='{"grade":"A","score":90,"issues":[],"summary":"good"}')
        grade = await run_quality_gate(reports, llm)
        llm.assert_not_called()
        assert grade.grade == "D"

    @pytest.mark.asyncio
    async def test_high_code_score_calls_llm(self):
        reports = [_make_report()]
        llm = AsyncMock(return_value='{"grade":"A","score":90,"issues":[],"summary":"good"}')
        grade = await run_quality_gate(reports, llm)
        llm.assert_called_once()
        assert grade.score == 95.0  # (100 + 90) / 2

    @pytest.mark.asyncio
    async def test_llm_returns_garbage(self):
        reports = [_make_report()]
        llm = AsyncMock(return_value="not json at all")
        grade = await run_quality_gate(reports, llm)
        assert grade.grade == "C"  # fallback

    @pytest.mark.asyncio
    async def test_combined_issues(self):
        reports = [_make_report(confidence=0.15)]
        llm = AsyncMock(
            return_value='{"grade":"B","score":70,"issues":["LLM发现的问题"],"summary":"ok"}'
        )
        grade = await run_quality_gate(reports, llm)
        assert len(grade.issues) >= 2  # code issue + LLM issue
