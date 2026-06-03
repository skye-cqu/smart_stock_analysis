from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.agents.schemas import (
    AnalystReport,
    DebateState,
    PortfolioDecision,
    QualityGrade,
    Recommendation,
    RiskDebateState,
)


class TestRecommendation:
    def test_enum_values(self):
        assert Recommendation.BUY == "买入"
        assert Recommendation.HOLD == "持有"
        assert Recommendation.SELL == "卖出"

    def test_enum_from_value(self):
        assert Recommendation("买入") is Recommendation.BUY


class TestAnalystReport:
    def test_construction(self):
        report = AnalystReport(
            role="技术分析师",
            analysis="看涨趋势",
            signal="看涨",
            confidence=0.8,
            key_points=["MA金叉", "RSI低位"],
        )
        assert report.role == "技术分析师"
        assert report.confidence == 0.8
        assert len(report.key_points) == 2

    def test_default_key_points(self):
        report = AnalystReport(role="test", analysis="x", signal="neutral", confidence=0.5)
        assert report.key_points == []

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            AnalystReport(role="t", analysis="x", signal="s", confidence=1.5)
        with pytest.raises(ValidationError):
            AnalystReport(role="t", analysis="x", signal="s", confidence=-0.1)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AnalystReport(role="t")


class TestPortfolioDecision:
    def test_construction(self):
        d = PortfolioDecision(
            recommendation=Recommendation.BUY,
            confidence=0.7,
            position_pct=30.0,
            reasoning="看好",
        )
        assert d.recommendation is Recommendation.BUY
        assert d.position_pct == 30.0
        assert d.risk_notes == ""

    def test_position_pct_clamped(self):
        with pytest.raises(ValidationError):
            PortfolioDecision(
                recommendation=Recommendation.HOLD,
                confidence=0.5,
                position_pct=120.0,
                reasoning="x",
            )

    def test_default_values(self):
        d = PortfolioDecision(
            recommendation=Recommendation.HOLD,
            confidence=0.5,
            position_pct=0,
            reasoning="x",
        )
        assert d.key_factors == []
        assert d.risk_notes == ""


class TestDebateState:
    def test_defaults(self):
        s = DebateState()
        assert s.bull_history == ""
        assert s.bear_history == ""
        assert s.count == 0
        assert s.max_rounds == 2


class TestRiskDebateState:
    def test_defaults(self):
        s = RiskDebateState()
        assert s.risky_history == ""
        assert s.safe_history == ""
        assert s.neutral_history == ""
        assert s.count == 0
        assert s.max_rounds == 1


class TestQualityGrade:
    def test_construction(self):
        g = QualityGrade(grade="A", score=95.0, issues=[], summary="优秀")
        assert g.grade == "A"
        assert g.score == 95.0

    def test_with_issues(self):
        g = QualityGrade(grade="D", score=30.0, issues=["过短", "缺要点"], summary="差")
        assert len(g.issues) == 2
