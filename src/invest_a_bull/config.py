from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnalysisConfig:
    project_root: Path = Path(__file__).resolve().parents[2]
    top_n: int = 5
    screener_queries: tuple[str, ...] = (
        "most_actives",
        "day_gainers",
        "growth_technology_stocks",
    )
    screener_count: int = 25
    price_history_period: str = "6mo"
    benchmark_ticker: str = "SPY"
    min_price: float = 5.0
    min_market_cap: int = 10_000_000_000
    allowed_exchanges: tuple[str, ...] = ("NMS", "NYQ", "ASE", "NGM")
    fallback_universe: tuple[str, ...] = (
        "AAPL",
        "AMD",
        "AMZN",
        "AVGO",
        "CRM",
        "GOOGL",
        "HOOD",
        "INTC",
        "JPM",
        "META",
        "MSFT",
        "NFLX",
        "NVDA",
        "ORCL",
        "PLTR",
        "SHOP",
        "TSLA",
    )
    risk_free_rate: float = 0.04
    monte_carlo_simulations: int = 250
    monte_carlo_days: int = 252
    random_seed: int = 42

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data" / "processed"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

