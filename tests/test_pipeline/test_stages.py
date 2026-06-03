from __future__ import annotations

from src.pipeline.stages import STAGE_ORDER, PipelineStage


class TestPipelineStage:
    def test_enum_values(self):
        assert PipelineStage.DATA_FETCH.value == "data_fetch"
        assert PipelineStage.STRATEGY_SCREEN.value == "strategy_screen"
        assert PipelineStage.SCORING.value == "scoring"
        assert PipelineStage.LLM_ANALYSIS.value == "llm_analysis"
        assert PipelineStage.NOTIFICATION.value == "notification"

    def test_enum_count(self):
        assert len(PipelineStage) == 5

    def test_stage_order_matches_stages(self):
        assert len(STAGE_ORDER) == len(PipelineStage)
        assert set(STAGE_ORDER) == set(PipelineStage)

    def test_stage_order_sequence(self):
        assert STAGE_ORDER[0] is PipelineStage.DATA_FETCH
        assert STAGE_ORDER[-1] is PipelineStage.NOTIFICATION
        assert STAGE_ORDER.index(PipelineStage.STRATEGY_SCREEN) < STAGE_ORDER.index(
            PipelineStage.SCORING
        )
        assert STAGE_ORDER.index(PipelineStage.SCORING) < STAGE_ORDER.index(
            PipelineStage.LLM_ANALYSIS
        )
