from __future__ import annotations

import logging

import requests

from src.config import settings
from src.data.models import AnalysisResult

logger = logging.getLogger(__name__)


class FeishuNotifier:
    def __init__(self) -> None:
        self.webhook_url = settings.notification.feishu_webhook_url

    def send(self, result: AnalysisResult) -> bool:
        if not self.webhook_url:
            logger.warning("Feishu webhook URL not configured")
            return False
        card = self._build_card(result)
        try:
            resp = requests.post(self.webhook_url, json=card, timeout=10)
            resp.raise_for_status()
            logger.info(f"Feishu notification sent for {result.stock_code}")
            return True
        except Exception as e:
            logger.error(f"Feishu notification failed: {e}")
            return False

    def _build_card(self, result: AnalysisResult) -> dict:
        score = result.score
        signals_text = (
            "\n".join(
                f"{s.strategy_name}: **{s.signal}** ({s.strength:.0%})"
                for s in result.strategy_signals
            )
            if result.strategy_signals
            else "No signals"
        )
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"Analysis: {result.stock_name} ({result.stock_code})",
                    },
                    "template": "blue" if score.total > 0 else "red",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**Price:** {result.current_price} | **Score:** {score.total:.1f} | **Recommend:** {result.recommendation}",
                        },
                    },
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**Signals:**\n{signals_text}"},
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**Dims:** Tech={score.technical:.0f} Flow={score.capital_flow:.0f} Fund={score.fundamental:.0f} Sector={score.sector:.0f} Event={score.event:.0f}",
                        },
                    },
                ],
            },
        }
