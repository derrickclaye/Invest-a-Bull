from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def resolve_project_root() -> Path:
    override = os.environ.get("INVEST_A_BULL_PROJECT_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "invest_a_bull").exists():
            return candidate

    package_candidate = Path(__file__).resolve().parents[2]
    if (package_candidate / "pyproject.toml").exists() and (package_candidate / "src" / "invest_a_bull").exists():
        return package_candidate

    raise RuntimeError(
        "Could not determine the project root from the current working directory or package location. "
        "Run the command from a project checkout or set INVEST_A_BULL_PROJECT_ROOT."
    )


@dataclass(frozen=True)
class AnalysisConfig:
    project_root: Path = field(default_factory=resolve_project_root)
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
    min_history_days: int = 63
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
    notebook_timeout_seconds: int = 1800

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data" / "processed"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"
