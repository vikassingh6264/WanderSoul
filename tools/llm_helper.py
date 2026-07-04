"""
Shared LLM client with timeout and error handling.

Provides a single async function to call the Groq LLM via LangChain
with consistent timeout wrapping, so no single slow call hangs the app.
Implements simple in-memory caching to avoid redundant identical calls.
"""

import asyncio
import hashlib
import logging
from collections import OrderedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

import config

logger = logging.getLogger(__name__)

# Simple LRU cache for LLM responses (avoids redundant calls)
_cache: OrderedDict[str, str] = OrderedDict()
_CACHE_MAX_SIZE = 50


def _get_llm() -> ChatGroq:
    """Create a ChatGroq LLM instance from config.

    Returns:
        Configured ChatGroq instance.
    """
    return ChatGroq(
        api_key=config.GROQ_API_KEY,
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
    )


def _cache_key(prompt: str) -> str:
    """Generate a short hash key for caching LLM responses.

    Args:
        prompt: The full prompt string.

    Returns:
        MD5 hex digest of the prompt.
    """
    return hashlib.md5(prompt.encode()).hexdigest()


async def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call the Groq LLM with timeout and caching.

    Args:
        system_prompt: System-level instructions for the LLM.
        user_prompt: The user's specific query/context.

    Returns:
        LLM response text.

    Raises:
        TimeoutError: If the LLM call exceeds the configured timeout.
        RuntimeError: If the LLM call fails for any other reason.
    """
    full_prompt = f"{system_prompt}\n---\n{user_prompt}"
    key = _cache_key(full_prompt)

    # Check cache first
    if key in _cache:
        logger.info("LLM cache hit for prompt hash %s", key[:8])
        _cache.move_to_end(key)
        return _cache[key]

    try:
        llm = _get_llm()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{system}"),
            ("human", "{query}"),
        ])
        chain = prompt_template | llm

        response = await asyncio.wait_for(
            chain.ainvoke({"system": system_prompt, "query": user_prompt}),
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
        result = response.content

        # Store in cache, evict oldest if full
        _cache[key] = result
        if len(_cache) > _CACHE_MAX_SIZE:
            _cache.popitem(last=False)

        return result

    except asyncio.TimeoutError:
        logger.error("LLM call timed out after %ds", config.LLM_TIMEOUT_SECONDS)
        raise TimeoutError(
            f"LLM response took longer than {config.LLM_TIMEOUT_SECONDS}s. "
            "Please try again."
        )
    except Exception as exc:
        logger.error("LLM call failed: %s", str(exc))
        raise RuntimeError(f"Failed to get LLM response: {type(exc).__name__}") from exc
