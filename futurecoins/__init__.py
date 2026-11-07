"""FutureCoins: an educational cryptocurrency simulation game.

The package is split into layers so that the simulation can be tested and
replayed without a user interface:

    config      frozen rules chosen by the player
    agents      the population
    consensus   who produces blocks and who gets paid
    economy     demand, fees, price index, sentiment
    events      declarative shocks
    engine      the tick pipeline that ties everything together
    grid        a projection of the population for the screen
    discovery   comparing a configuration to a historical target
    achievements long-term goals and their persistence
    education   glossary and external resources
    interface   Streamlit-only presentation code

Nothing in the engine imports Streamlit. That is a deliberate boundary: the
simulation is a library, the app is one possible client.
"""

from __future__ import annotations

from .config import DEFAULT_CONFIG, PRESETS, SimConfig
from .engine import Simulation, TickResult

__all__ = ["DEFAULT_CONFIG", "PRESETS", "SimConfig", "Simulation", "TickResult"]
__version__ = "0.1.0"
