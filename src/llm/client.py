from __future__ import annotations

import asyncio
import logging

from litellm import Router

from src.config import settings

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 120.0

_router: Router | None = None


def _get_router() -> Router:
    global _router
    if _router is not None:
        return _router

    cfg = settings.llm
    model_list = [
        {
            "model_name": "deepseek/deepseek-chat",
            "litellm_params": {
                "model": "deepseek/deepseek-chat",
                "api_base": cfg.deepseek_base_url,
                "api_key": cfg.deepseek_api_key,
            },
        },
    ]
    if cfg.gemini_api_key:
        model_list.append(
            {
                "model_name": "gemini/gemini-2.0-flash",
                "litellm_params": {
                    "model": "gemini/gemini-2.0-flash",
                    "api_key": cfg.gemini_api_key,
                },
            }
        )
    if cfg.ollama_base_url:
        model_list.append(
            {
                "model_name": f"ollama/{cfg.ollama_model}",
                "litellm_params": {
                    "model": f"ollama/{cfg.ollama_model}",
                    "api_base": cfg.ollama_base_url,
                    "api_key": "ollama",
                },
            }
        )

    _router = Router(
        model_list=model_list,
        num_retries=3,
        allowed_fails=2,
        cooldown_time=30,
        fallbacks=[
            {
                "deepseek/deepseek-chat": [
                    "gemini/gemini-2.0-flash",
                    f"ollama/{cfg.ollama_model}",
                ],
            }
        ],
        retry_policy={
            "TimeoutErrorRetries": 3,
            "RateLimitErrorRetries": 3,
            "InternalServerErrorRetries": 2,
            "AuthenticationErrorRetries": 0,
        },
    )
    logger.info(f"LLM Router initialized with {len(model_list)} providers")
    return _router


async def analyze(prompt, system="", model=None, temperature=None):
    router = _get_router()
    model = model or settings.llm.model
    temp = temperature if temperature is not None else settings.llm.temperature
    logger.info(f"LLM call: model={model}, prompt_len={len(prompt)}")
    try:
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system or "你是一位专业的A股投资分析师。"},
                {"role": "user", "content": prompt},
            ],
            temperature=temp,
        )
        response = await asyncio.wait_for(router.acompletion(**kwargs), timeout=LLM_TIMEOUT_SECONDS)
        result = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else "unknown"
        actual_model = getattr(response, "model", "unknown")
        logger.info(f"LLM response: model={actual_model}, tokens={tokens}")
        return result
    except TimeoutError:
        logger.error(f"LLM call timed out after {LLM_TIMEOUT_SECONDS}s")
        raise
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise
