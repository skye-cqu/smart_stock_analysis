from __future__ import annotations

import logging

from src.data.models import ScoreResult, StockDailyData, StockInfo

logger = logging.getLogger(__name__)


class FiveDimensionScorer:
    WEIGHTS = {
        "technical": 0.30,
        "capital_flow": 0.30,
        "fundamental": 0.15,
        "sector": 0.15,
        "event": 0.10,
    }

    def __init__(self) -> None:
        from src.scoring.capital_flow_scorer import CapitalFlowScorer
        from src.scoring.event_scorer import EventScorer
        from src.scoring.fundamental_scorer import FundamentalScorer
        from src.scoring.sector_scorer import SectorScorer
        from src.scoring.technical_scorer import TechnicalScorer

        self.scorers = {
            "technical": TechnicalScorer(),
            "capital_flow": CapitalFlowScorer(),
            "fundamental": FundamentalScorer(),
            "sector": SectorScorer(),
            "event": EventScorer(),
        }

    def score(self, info: StockInfo, daily_data: list[StockDailyData]) -> ScoreResult:
        scores = {}
        veto = False
        veto_reason = ""
        for dim, scorer in self.scorers.items():
            try:
                s = scorer.score(info, daily_data)
                scores[dim] = s
                if s < -50:
                    veto = True
                    veto_reason = f"{dim} score critically low: {s}"
            except Exception as e:
                logger.warning(f"Scorer {dim} failed: {e}")
                scores[dim] = 0.0
        total = sum(scores.get(dim, 0) * weight for dim, weight in self.WEIGHTS.items())
        return ScoreResult(
            total=total if not veto else -100,
            technical=scores.get("technical", 0),
            capital_flow=scores.get("capital_flow", 0),
            fundamental=scores.get("fundamental", 0),
            sector=scores.get("sector", 0),
            event=scores.get("event", 0),
            veto=veto,
            veto_reason=veto_reason,
        )
