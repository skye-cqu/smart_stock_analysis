from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Recommendation(StrEnum):
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"


class AnalystReport(BaseModel):
    role: str = Field(description="分析师角色名称")
    analysis: str = Field(description="分析内容")
    signal: str = Field(description="看涨/看跌/中性")
    confidence: float = Field(description="信心度 0-1", ge=0, le=1)
    key_points: list[str] = Field(default_factory=list, description="关键要点")


class DebateState(BaseModel):
    bull_history: str = ""
    bear_history: str = ""
    count: int = 0
    max_rounds: int = 2


class RiskDebateState(BaseModel):
    risky_history: str = ""
    safe_history: str = ""
    neutral_history: str = ""
    count: int = 0
    max_rounds: int = 1


class PortfolioDecision(BaseModel):
    recommendation: Recommendation = Field(description="最终建议")
    confidence: float = Field(description="信心度 0-1", ge=0, le=1)
    position_pct: float = Field(description="建议仓位百分比 0-100", ge=0, le=100)
    reasoning: str = Field(description="决策理由")
    risk_notes: str = Field(default="", description="风险提示")
    key_factors: list[str] = Field(default_factory=list, description="关键因素")


class QualityGrade(BaseModel):
    grade: str = Field(description="评级 A-F")
    score: float = Field(description="分数 0-100")
    issues: list[str] = Field(default_factory=list, description="发现的问题")
    summary: str = Field(description="质量总结")
