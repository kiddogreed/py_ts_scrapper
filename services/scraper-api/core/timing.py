# services/scraper-api/core/timing.py
"""
Human-like timing delays for anti-bot evasion.

WHY: Bots make requests at mechanically consistent intervals. Real users
have natural variance in timing — reading time, mouse movement, network
latency. We model request gaps as a Gaussian distribution (Box-Muller
transform) and simulate "think time" between page interactions.

Usage:
    from core.timing import human_delay, read_delay, random_scroll_pauses

    await human_delay()                    # default ~1.5s ± 0.5s
    await human_delay(mean_ms=2000, std_ms=600)
    await read_delay(content_length_chars=3000)
    pauses = random_scroll_pauses(n=4)    # list of floats in seconds
"""
import asyncio
import math
import random


def _gaussian(mean: float, std: float) -> float:
    """
    Box-Muller transform — produces a Gaussian sample without scipy.
    We clamp u1 away from 0 to avoid log(0).
    """
    u1 = max(1e-10, random.random())
    u2 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + z * std


async def human_delay(
    mean_ms: float = 1500.0,
    std_ms: float = 500.0,
    min_ms: float = 200.0,
    max_ms: float = 8000.0,
) -> float:
    """
    Awaitable Gaussian delay that mimics human "think time" between requests.

    Args:
        mean_ms:  Centre of the Gaussian in milliseconds (default 1.5 s).
        std_ms:   Standard deviation in milliseconds (default 0.5 s).
        min_ms:   Hard lower bound — never fires faster than this.
        max_ms:   Hard upper bound — prevents runaway waits on extreme samples.

    Returns:
        Actual delay in milliseconds (useful for logging).
    """
    delay_ms = max(min_ms, min(max_ms, _gaussian(mean_ms, std_ms)))
    await asyncio.sleep(delay_ms / 1000.0)
    return delay_ms


async def read_delay(content_length_chars: int = 500) -> float:
    """
    Simulate reading time proportional to page content length.
    Average adult reading speed ≈ 200 words/min ≈ 1 000 chars/min.
    Adds ±20 % random jitter so it doesn't look mechanical.

    Returns:
        Actual delay in milliseconds.
    """
    base_ms = (content_length_chars / 1000.0) * 60.0 * 1000.0  # chars → ms
    jitter_ms = base_ms * 0.2 * random.uniform(-1.0, 1.0)
    delay_ms = max(200.0, min(15_000.0, base_ms + jitter_ms))
    await asyncio.sleep(delay_ms / 1000.0)
    return delay_ms


def random_scroll_pauses(n: int = 3) -> list[float]:
    """
    Returns n pause durations (seconds) for simulating scroll behaviour.
    Each pause is sampled from Gaussian(μ=0.8s, σ=0.3s), clamped ≥ 0.1 s.
    """
    return [max(0.1, _gaussian(0.8, 0.3)) for _ in range(n)]


def jittered_interval(base_ms: float, jitter_pct: float = 0.25) -> float:
    """
    Returns a base interval with ±jitter_pct random noise (milliseconds).
    Useful for scheduled polling loops that shouldn't be perfectly periodic.
    """
    jitter = base_ms * jitter_pct * random.uniform(-1.0, 1.0)
    return max(100.0, base_ms + jitter)
