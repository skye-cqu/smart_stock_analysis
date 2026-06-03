from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.data.models import AnalysisResult, ScoreResult, StrategySignal


def _make_result(total_score: float = 65.0) -> AnalysisResult:
    score = ScoreResult(
        total=total_score,
        technical=70.0,
        capital_flow=60.0,
        fundamental=55.0,
        sector=50.0,
        event=45.0,
    )
    return AnalysisResult(
        stock_code="000001",
        stock_name="平安银行",
        current_price=12.5,
        score=score,
        strategy_signals=[
            StrategySignal(
                strategy_name="ma_cross",
                stock_code="000001",
                signal="buy",
                strength=0.8,
            ),
        ],
        llm_analysis="test",
        recommendation="买入",
    )


class TestFeishuNotifier:
    @patch("src.notifications.feishu.requests.post")
    @patch("src.notifications.feishu.settings")
    def test_send_success(self, mock_settings, mock_post):
        mock_settings.notification.feishu_webhook_url = "https://hooks.feishu.cn/test"
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from src.notifications.feishu import FeishuNotifier

        notifier = FeishuNotifier()
        result = notifier.send(_make_result())

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["timeout"] == 10

    @patch("src.notifications.feishu.requests.post")
    @patch("src.notifications.feishu.settings")
    def test_send_failure_on_exception(self, mock_settings, mock_post):
        mock_settings.notification.feishu_webhook_url = "https://hooks.feishu.cn/test"
        mock_post.side_effect = ConnectionError("Network error")

        from src.notifications.feishu import FeishuNotifier

        notifier = FeishuNotifier()
        result = notifier.send(_make_result())

        assert result is False

    @patch("src.notifications.feishu.settings")
    def test_no_webhook_url_returns_false(self, mock_settings):
        mock_settings.notification.feishu_webhook_url = ""

        from src.notifications.feishu import FeishuNotifier

        notifier = FeishuNotifier()
        result = notifier.send(_make_result())

        assert result is False

    @patch("src.notifications.feishu.requests.post")
    @patch("src.notifications.feishu.settings")
    def test_card_header_blue_for_positive_score(self, mock_settings, mock_post):
        mock_settings.notification.feishu_webhook_url = "https://hooks.feishu.cn/test"
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from src.notifications.feishu import FeishuNotifier

        notifier = FeishuNotifier()
        notifier.send(_make_result(total_score=65.0))

        card = mock_post.call_args[1]["json"]
        assert card["card"]["header"]["template"] == "blue"

    @patch("src.notifications.feishu.requests.post")
    @patch("src.notifications.feishu.settings")
    def test_card_header_red_for_negative_score(self, mock_settings, mock_post):
        mock_settings.notification.feishu_webhook_url = "https://hooks.feishu.cn/test"
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from src.notifications.feishu import FeishuNotifier

        notifier = FeishuNotifier()
        notifier.send(_make_result(total_score=-20.0))

        card = mock_post.call_args[1]["json"]
        assert card["card"]["header"]["template"] == "red"

    @patch("src.notifications.feishu.requests.post")
    @patch("src.notifications.feishu.settings")
    def test_card_contains_stock_info(self, mock_settings, mock_post):
        mock_settings.notification.feishu_webhook_url = "https://hooks.feishu.cn/test"
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        from src.notifications.feishu import FeishuNotifier

        notifier = FeishuNotifier()
        notifier.send(_make_result())

        card = mock_post.call_args[1]["json"]
        title = card["card"]["header"]["title"]["content"]
        assert "000001" in title
        assert "平安银行" in title
