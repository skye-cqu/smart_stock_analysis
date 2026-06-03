from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    DATA_FETCH = "data_fetch"
    STRATEGY_SCREEN = "strategy_screen"
    SCORING = "scoring"
    LLM_ANALYSIS = "llm_analysis"
    NOTIFICATION = "notification"


STAGE_ORDER = [
    PipelineStage.DATA_FETCH,
    PipelineStage.STRATEGY_SCREEN,
    PipelineStage.SCORING,
    PipelineStage.LLM_ANALYSIS,
    PipelineStage.NOTIFICATION,
]
