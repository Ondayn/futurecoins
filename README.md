# FutureCoins

**Build a currency. Simulate its economy. Discover what makes it work.**

**▶ Try it in your browser (no install):** <https://futurecoins.streamlit.app/>

FutureCoins is an educational sandbox game about cryptocurrency networks. You configure a
virtual currency, launch an agent-based simulation on an emoji grid, and watch the
consequences of your protocol and monetary decisions unfold.

> The simulation is an **educational abstraction**. It is not a blockchain, not a
> forecast, and not investment advice. Every simulated number is labelled *model* in the
> interface.

## What you can do

- **Design a currency.** Consensus mechanism, block time, initial supply, supply cap,
  block reward, halving interval, base fee, burn rate, population, and (in Advanced mode)
  per-role populations, costs, market damping and event frequency.
- **Watch a population live under those rules.** Agents across six roles — miners,
  validators, users, traders, developers and attackers — on a 30 × 30 grid. If the
  population exceeds the grid, the board shows a deterministic 1:1 snapshot of part of
  the population, and the interface always shows real totals separately.
- **Read a dashboard.** Twelve metric cards grouped Network / Money / Market / Health,
  a decomposed health score with visible weights, and a live history chart.
- **Survive random events.** Market crashes, congestion spikes, negative media and
  producer exodus, each with a severity scaled by how fragile the network already is.
- **Play Discovery Mode.** Reconstruct currencies from their behaviour (educational abstractions):
  Bitcoin 2009, Ethereum 2015 (early-era), and Solana 2020 (launch-era), with weighted
  similarity scores, visible confidence, and progressive digit-free hints (feedback appears after running).
- **Unlock achievements.** Goals (including discovery achievements) record configuration hash, seed and a
  snapshot of the exact grid that earned it. Awards can be exported/imported as JSON.
- **Learn the words.** A 51-term glossary with in-game and real-world explanations, plus
  twelve curated external links that each say what you will learn before you click.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e ".[dev]"
streamlit run app.py
```

The app opens on the **Blank Canvas** preset — a healthy, ordinary network. Move sliders,
press **Apply config**, then **Run**.

### Controls

| Control | Meaning |
| --- | --- |
| **⚙️ Apply config** | Build a fresh simulation from the current sidebar settings |
| **Run / Pause** | Start or stop the clock (1 tick = 1 simulated day) |
| **Reset** | Return the current simulation to tick 0 with the same rules |
| **Speed** | Ticks advanced per frame: 1, 2, 5 or 20 (the frame rate stays ~1 fps) |
| **ASCII fallback** | Use letters instead of emoji if your font renders the grid oddly |

## Presets

| Preset | What it teaches |
| --- | --- |
| **Blank Canvas** *(default)* | A neutral, healthy network to design from |
| **Bitcoin 2009** | Proof of Work, no premine, and a 21 M cap that is *emergent* from halving |
| **Ethereum 2015** | Fast blocks, no halving, a treasury, and a large premine |
| **Solana 2020** | Proof of Stake, sub-second blocks, high throughput, fee burning |
| **Stable Utility Coin** | Fixed supply with fees as the only validator income |
| **Chaos Sandbox** | Tiny blocks, hyperinflation, frequent shocks — a deliberately fragile network |

Presets are just named `SimConfig` values; there is no special code path.

## Project layout

```
futurecoins/
  config.py        frozen rules, presets, derived values
  agents.py        the population and its roles
  consensus.py     who produces blocks and who gets paid
  economy.py       demand, fees, price index, sentiment
  events.py        declarative shocks
  engine.py        the tick pipeline
  metrics.py       snapshots and the health score
  grid.py          projection of agents onto cells
  discovery/       targets (BTC/ETH/SOL abstractions), scoring, hints
  achievements/    pure predicates, persistence, snapshots
  education/       glossary and external resources
  interface/       Streamlit-only presentation
app.py             the Streamlit application
tests/             unit tests for every module
docs/              design, architecture and learning material
```

**The engine never imports Streamlit.** It is a plain Python library with no UI
dependency, so it can be tested and replayed headlessly. `app.py` is one client of it.

## Determinism

One seeded `random.Random` per simulation, agents iterated in id order, no wall-clock
time in the engine. Two runs with the same configuration and seed produce identical
histories — which is what makes an achievement reproducible and a bug debuggable.

## Tests and lint

```bash
python -m pytest -q
python -m ruff check .
```

The suite covers configuration, agents, consensus, economy, metrics, the engine, events,
Discovery scoring, achievements, grid rendering, the glossary and the pure UI helpers.

## Documents

| Document | Purpose |
| --- | --- |
| [`docs/GDD.md`](docs/GDD.md) | Game Design Document — what the game is and why |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Technical architecture, formulas, module responsibilities |
| [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md) | Milestones, hour estimates, acceptance criteria |
| [`docs/IMPLEMENTATION_CHECKLIST.md`](docs/IMPLEMENTATION_CHECKLIST.md) | Ordered, beginner-friendly build checklist |
| [`docs/GLOSSARY.md`](docs/GLOSSARY.md) | Beginner glossary used by the in-game tooltips |
| [`docs/LEARNING_RESOURCES.md`](docs/LEARNING_RESOURCES.md) | Curated external reading, mapped to features |

## Scope

This is the local, free-to-play MVP. There is no blockchain connection, no wallet, no
marketplace and no multiplayer. A Solana Memo attestation and an optional NFT badge are
deliberately deferred; the design keeps the engine independent so they can be added as a
separate adapter later.

## Further development (notes)
- Add a Stable Utility Coin discovery target/unlock path (currently a locked mystery).
- Expand scenarios/balance based on playtests; improve accessibility/mobile polish.
- Keep engine independent from blockchain/wallet features; any on-chain adapter remains optional/post-MVP.

## Beginner walkthrough (first time here)

1. **Try the live app:** open <https://futurecoins.streamlit.app/> (no installation).
2. **Read the welcome guide** on first visit, then press **Start playing**.
3. **Pick a preset or start from Blank Canvas** in the sidebar, adjust settings, press **⚙️ Apply config**.
4. **Press Run.** Each tick = 1 simulated day. Watch the grid, indicator cards, and charts.
5. **Explore tabs:** **Dashboard** (health/history after you run), **Discovery** (choose a target such as Bitcoin 2009 / Ethereum 2015 / Solana 2020 and match it by observing behavior; similarity feedback appears after running), **Awards**, **Glossary**, **Why** (changes + feedback loops).
6. **Run locally (optional):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   pip install -e ".[dev]"
   streamlit run app.py
   ```
7. **Key folders:** `futurecoins/` = simulation engine + UI modules (engine has no Streamlit imports), `app.py` = Streamlit app, `tests/` = pytest suite, `docs/` = design/architecture/glossary.

## License

[MIT](LICENSE) © 2026 Ondayn.
