"""Runtime configuration. Everything secret comes from environment variables, never from code."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # optional local .env support for people running it on their own machine
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class ModelSpec:
    """A model we call on Nebius Token Factory, with list prices in USD per 1M tokens."""

    role: str
    model_id: str
    price_in: float
    price_out: float


@dataclass(frozen=True)
class Settings:
    nebius_api_key: str = field(default_factory=lambda: _env("NEBIUS_API_KEY"))
    nebius_base_url: str = field(
        default_factory=lambda: _env("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
    )
    tavily_api_key: str = field(default_factory=lambda: _env("TAVILY_API_KEY"))
    # Hard cap on live model spend per day (USD) so judges' traffic can't drain credits.
    daily_spend_cap_usd: float = field(default_factory=lambda: float(_env("DAILY_SPEND_CAP_USD", "2.0")))

    # Model IDs are overridable because Token Factory's live catalog is the source of truth.
    # Defaults come from third-party catalog listings (Oct 2026) and MUST be confirmed with
    # `python -m scripts.smoke_test` (it calls GET /v1/models).
    nano: ModelSpec = field(
        default_factory=lambda: ModelSpec(
            "nano", _env("MODEL_NANO", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"), 0.06, 0.24
        )
    )
    super_vl: ModelSpec = field(
        default_factory=lambda: ModelSpec(
            "super_vl", _env("MODEL_SUPER_VL", "nvidia/Nemotron-3.5-Super-VL"), 0.30, 0.90
        )
    )
    ultra: ModelSpec = field(
        default_factory=lambda: ModelSpec(
            "ultra", _env("MODEL_ULTRA", "nvidia/Nemotron-3-Ultra-550b-a55b"), 1.00, 3.00
        )
    )

    @property
    def live_models(self) -> bool:
        return bool(self.nebius_api_key)

    @property
    def live_tavily(self) -> bool:
        return bool(self.tavily_api_key)


settings = Settings()
