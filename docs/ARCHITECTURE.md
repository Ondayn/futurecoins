# FutureCoins — Technical Architecture (v0.1)

> Status: draft for approval. No implementation code exists yet.

---

## 1. The one decision that matters

**The simulation engine is a pure Python library with zero imports from Streamlit.**

```
        ┌─────────────────────────────────────────┐
        │  UI layer (Streamlit)                   │  app.py, interface/
        │  widgets, grid HTML, charts, tooltips   │
        └───────────────┬─────────────────────────┘
                        │  calls run_tick(), reads TickResult
                        ▼
        ┌─────────────────────────────────────────┐
        │  Engine (pure Python, deterministic)    │  simulation/, discovery/,
        │  no Streamlit, no network, no filesystem│  achievements/, education/
        └───────────────┬─────────────────────────┘
                        │  optional, last
                        ▼
        ┌─────────────────────────────────────────┐
        │  Blockchain adapter (Devnet only)       │  blockchain/
        └─────────────────────────────────────────┘
```

Why: the engine can be tested in milliseconds, run headless from a script, replayed from a
seed, and ported to a different UI later without touching a line of simulation code. It is
also the difference between "a Streamlit demo" and "a game with a Streamlit front-end".

**Rule:** if a file under `simulation/`, `discovery/`, `achievements/` or `education/`
contains the string `streamlit`, that is a bug.

---

## 2. Module responsibilities

```
futurecoins/
├── app.py                        # Streamlit entry point, page routing, session state
├── pyproject.toml                # dependencies + tool config (not requirements.txt alone)
│
├── simulation/
│   ├── config.py                 # SimConfig, NetworkParams, MonetaryParams, AgentParams
│   ├── agents.py                 # Agent dataclass, role enum, role step functions
│   ├── consensus.py              # PoW / PoS block production, rewards, participation
│   ├── economy.py                # fees, demand, price index, sentiment, liquidity
│   ├── events.py                 # EventSpec, EventEngine, active modifiers, log entries
│   ├── metrics.py                # Metrics snapshot, network health, volatility
│   ├── engine.py                 # Simulation class: the 10-stage tick pipeline
│   └── grid.py                   # population -> cells projection, emoji + HTML rendering
│
├── discovery/
│   ├── targets.py                # versioned reference configs with confidence flags
│   ├── scoring.py                # weighted similarity, per-parameter breakdown
│   └── hints.py                  # directional hint generation from the breakdown
│
├── achievements/
│   ├── conditions.py             # pure predicate functions over RunSummary
│   ├── manager.py                # evaluate, dedupe, award, persist
│   └── snapshots.py              # compact grid snapshot encode/decode
│
├── education/
│   ├── glossary.py               # single source of truth: term, plain text, effect, link
│   └── resources.py              # curated links + "what you will learn"
│
├── blockchain/                   # created only at Milestone 9
│   ├── wallet.py                 # keypair loading from env/secrets, address validation
│   └── attestation.py            # Memo transaction builder + sender (devnet)
│
├── interface/
│   ├── dashboard.py              # metric cards
│   ├── controls.py               # run/pause/reset/speed, config widgets by mode
│   ├── grid_view.py              # st.html wrapper around grid.render_html
│   ├── tooltips.py               # glossary -> help=/popover helpers
│   └── theme.py                  # CSS injected once
│
├── tests/                        # pytest, no Streamlit imports
└── docs/
```

Flattened from the brief's proposal: `simulation/grid.py` is a *projection* (engine →
cells), so it belongs with the engine, not the interface. The interface only turns cells
into HTML. Empty directories are not created.

---

## 3. Core data structures

```python
# simulation/config.py
@dataclass(frozen=True)
class SimConfig:
    seed: int = 42
    network: NetworkParams
    monetary: MonetaryParams
    agents: AgentParams
    social: SocialParams
    events: EventParams
```

```python
# simulation/engine.py
@dataclass(frozen=True)
class TickResult:
    tick: int
    metrics: Metrics
    events: tuple[EventLogEntry, ...]
    notable_changes: tuple[str, ...]   # sentences for the "why" panel
```

The UI only ever sees `TickResult` and `Simulation.metrics`. It never mutates agents.
That boundary is what keeps the UI dumb and the engine testable.

---

## 4. Time model — the most important convention

**1 tick = 1 simulated day.**

```
blocks_per_tick = 86400 / block_time_s
tx_capacity_per_tick = tx_per_block * blocks_per_tick
```

| Network | Block time | Blocks / tick | Why |
| --- | --- | --- | --- |
| Bitcoin-like | 600 s | 144 | 10-minute blocks |
| Ethereum-like | 12 s | 7 200 | slot time |
| Solana-like | 0.4 s | 216 000 | sub-second slots |

Consequences:
- One simulated year = **365 ticks**. Reachable with a "simulate 500 ticks" button.
- Economic and social dynamics (sentiment, adoption) update at a human timescale.
- `block_time` stays a *protocol parameter*, and TPS is derived from demand and capacity —
  the two metrics stay conceptually distinct, which is the lesson.

**Simplification, stated openly:** real PoW block time is an *outcome* of total hashrate
versus difficulty. We treat it as a target and use `availability_factor` (0–1) to model
slowdowns during outages and exoduses. Difficulty retargeting is v1.1.

---

## 5. The tick pipeline

Each stage is a function. Each stage is testable in isolation.

```python
def run_tick(self) -> TickResult:
    ctx = self._context()                    # 0. read-only snapshot of state

    self._advance_events(ctx)                # 1. expire/trigger events -> modifiers
    tx_demand = self._generate_transactions(ctx)   # 2. users create demand
    included, dropped, fees = self._process_mempool(tx_demand, ctx)  # 3. capacity + fees
    blocks, rewards = self._produce_blocks(ctx)    # 4. PoW or PoS
    self._settle(fees, rewards)              # 5. pay miners/validators, burn
    self._update_balances()                  # 6. apply
    self._update_agents(ctx)                 # 7. enter/exit, confidence, churn
    self._update_economy(included, dropped)  # 8. price, sentiment, adoption
    self._metrics = self._compute_metrics()  # 9. snapshot
    return TickResult(...)                   # 10. UI renders
```

Order matters and is deliberate: agents react to *last* tick's economy, then the economy
reacts to *this* tick's activity. That one-tick lag prevents instantaneous feedback loops
that explode numerically.

---

## 6. Formulas

All constants live in `config.py` with a comment naming the real-world intuition. All are
documented in the glossary.

### 6.1 Supply (exact accounting)

```
total_supply(t) = initial_supply + Σ issuance − Σ burned
circulating(t)  = total_supply(t) − protocol_treasury
```

Staked tokens **are** part of circulating supply (they still exist and can be sold after
unbonding). Treasury tokens are not. This definition is shown in the tooltip.

### 6.2 Issuance

```
blocks_this_tick = blocks_per_tick * availability_factor
issuance = blocks_this_tick * block_reward
if max_supply is not None:
    issuance = min(issuance, max_supply - total_supply)
```

Halving is counted in **blocks**, not ticks, because that is how real protocols do it:

```
halvings = total_blocks_produced // halving_interval_blocks
block_reward = initial_block_reward / (2 ** halvings)
```

Test: after `halving_interval_blocks` blocks, reward is exactly half.

### 6.3 PoW rewards

```
share_i    = hashrate_i / Σ hashrate_active
reward_i   = issuance * share_i + fees_pool * share_i
cost_i     = electricity_cost_per_tick
profit_i   = reward_i − cost_i
```

Expected-value accrual, not per-block lottery. Reason: with 6 blocks/hour and 300 miners,
a lottery means most miners earn nothing for hours and the grid becomes noise. Expected
value keeps the *aggregate* behaviour correct and the *individual* behaviour readable.
This is stated in the UI ("rewards are smoothed across miners for readability").

### 6.4 PoS rewards

```
share_i = stake_i / Σ stake_active
reward_i = issuance * share_i + fees_pool * share_i
cost_i = infra_cost_per_tick
```

If `Σ stake_active < min_security_stake`, `availability_factor` drops proportionally:
finality stalls. That is the PoS lesson in one line.

### 6.5 Transaction demand and fees

```
congestion   = demand / max(capacity, 1)
pressure     = max(0, congestion − 1)          # only full blocks ration space
fee          = base_fee * (1 + fee_congestion_multiplier * pressure)
demand_after = demand * exp(−fee_elasticity * (fee / base_fee − 1))
included     = min(demand_after, capacity)
dropped      = max(0, demand_after − capacity)
fees_pool    = included * fee
burned       = fees_pool * burn_rate
```

`exp(−k·x)` is used because demand should fall smoothly and never go negative. The
elasticity constant is a documented tuning knob, not a measured value.

`pressure = max(0, congestion − 1)` matters. An earlier version priced fees from
congestion itself, so a half-empty network still paid more than the base fee and
dropped transactions it had room for. Fees now move only when blocks are full, which
is what the word "congestion" is supposed to mean.

Fees are also limited by what users can actually pay: the engine caps the fee pool at
the aggregate user balance. A genesis network with no coins therefore collects almost
nothing, which is historically right for early Bitcoin.

### 6.6 Price index

Starts at **100.0** at launch. It is an index, not a price.

```
fundamental     = 100 * adoption * (0.8 + 0.4 * clamp(utilisation, 0, 1.5))
sell_pressure   = inflation_fraction * sell_propensity * (1 − sentiment)
                + 0.02 * (1 − reliability)
                + trader_pressure
liquidity_scale = sqrt(1_000_000 / max(liquidity, 1))

log_return = liquidity_scale * (k_flow * 0.15 * ln(fundamental / price)
             − 0.5 * sell_pressure
             + k_sent * (sentiment − 0.5)
             + event_shock)
             + N(0, sigma * liquidity_scale)

log_return = clamp(log_return, −0.35, 0.35)
price      = clamp(price * exp(log_return), 1.0, 100_000.0)
volatility = EWMA(|log_return|, alpha=0.2)
```

Two revisions were needed before this behaved:

- **Mean reversion.** The first version summed a constant sentiment offset every tick.
  A 5 % nudge per tick compounds to roughly a 12,000× rise in one simulated year, so the
  index pinned itself to the clamp. The index now pulls toward a *fundamental* level set
  by adoption and utilisation, and the sentiment term is small (`k_sent = 0.05`).
- **Liquidity as a scale, not a divisor.** Dividing net flow by liquidity made the
  constant meaningless at large values. `sqrt(1e6 / liquidity)` now scales the whole
  response, including noise: a thin market moves more, which is the intuition.

`clamp` exists so a bug cannot produce `price = 10^300` in a demo. `N(0, sigma)` uses the
seeded RNG, so the run is reproducible.

### 6.7 Sentiment

```
target = clamp(0.5 + 0.5*(health−50)/50 + media_bias + event_bias, 0, 1)
sentiment += adaptivity * (target − sentiment) + N(0, 0.01)
```

### 6.8 Network health (0–100)

```
participation   = min(1, active_nodes / target_nodes)
concentration   = Σ share_i²                     # Herfindahl index
decentralization = 1 − concentration
reliability     = 1 − dropped / max(attempted, 1)
security        = min(1, security_margin)

health = 100 * (0.30*participation
              + 0.20*decentralization
              + 0.25*reliability
              + 0.15*security
              + 0.10*sentiment)
```

Weights are visible in the UI when the player clicks the health card. "Network health" is
otherwise the vaguest metric in the brief; making the weights explicit is what turns it
from a vibe into a lesson.

### 6.9 Determinism

- One `random.Random(seed)` owned by `Simulation`, passed explicitly to every consumer.
- Agents iterated in **id order**, never dict insertion order.
- No `set` iteration in any code path that draws randomness.
- No wall-clock time inside the engine.
- No NumPy RNG in the MVP (a second RNG is a second failure mode).

Test: `run(seed=7, ticks=200)` twice produces byte-identical metric traces.

---

## 7. Discovery scoring

```
similarity(param) =
    numeric:              max(0, 1 − |player − target| / tolerance)
    categorical:          1 if equal else 0
    ordered categorical:  1 − |rank_player − rank_target| / (n − 1)

S = Σ (weight_i * similarity_i) / Σ weight_i
```

Each target parameter carries a `confidence` flag (`high` / `medium` / `low`). Low-confidence
parameters get half weight and are listed in the UI under "what historians are unsure
about". We never claim exact historical reproduction.

Bitcoin 2009 reference (v1):

| Parameter | Value | Weight | Confidence |
| --- | --- | --- | --- |
| Consensus | PoW | 0.20 | high |
| Target block time | 600 s | 0.15 | high |
| Max supply | 21 000 000 (or none + halving) | 0.10 | high |
| Initial block reward | 50 | 0.15 | high |
| Halving interval | 210 000 blocks | 0.20 | high |
| Burn rate | 0 | 0.10 | high |
| Tx per block | ~2 500 | 0.05 | medium |
| Base fee | very low | 0.05 | low |

Tolerances are wide for uncertain parameters and narrow for certain ones. The full table
ships in `discovery/targets.py` with a comment per row.

---

## 8. Grid rendering in the browser

### 8.1 Why not `st.markdown` + a string

Emoji are not monospaced. `😀😀` and `⛏️⛏️` occupy different widths depending on font,
platform, and whether the variation selector is present. A plain string grid drifts.

### 8.2 The approach

```python
# simulation/grid.py  (engine side: pure data)
def project(agents, rows, cols) -> list[list[Cell]]:
    """Assign agents to cells; if population > rows*cols, cells are cohorts."""

def render_html(grid, legend) -> str:
    """Cells -> a CSS grid of <span> elements. No Streamlit import."""
```

```html
<div class="fc-grid" style="--fc-cols:30;--fc-rows:30">
  <span class="fc-cell fc-miner" title="Cell 12,7 · 6 agents · 4 active">⛏️</span>
  <span class="fc-cell fc-empty" title="3 offline agents · hidden"></span>
  <span class="fc-cell fc-slot">·</span>
  ...
</div>
```

```css
.fc-grid { display: grid; grid-template-columns: repeat(var(--fc-cols), minmax(0, 1fr));
           width: min(100%, var(--fc-grid-max)); aspect-ratio: var(--fc-cols) / var(--fc-rows);
           container-type: size; }
.fc-cell { display: grid; place-items: center; font-size: min(2.2cqw, 1.5rem); }
.fc-empty { background: transparent; }   /* an agent went offline */
.fc-slot  { color: #1e2d4a; }             /* no agent was ever assigned */
```

A CSS grid with fluid, equal cells removes the alignment problem entirely. Opacity encodes
how much of a cohort is active, colour encodes role, and offline agents are blank rather
than greyed out — the board shows the network that is running, not the one that used to.

The board is sized from the height first: `--fc-grid-max` is the budget left after the
hero, the indicator cards, the population line and the legend, and `aspect-ratio` turns
that height into a width. A 30 × 30 board therefore fits one screen without scrolling
instead of growing until the page does.

On wide screens (more than 1200 px and a landscape viewport) the board sits in the left
column of a two-column split, and that column is **exactly as wide as the board**. The
remainder of the width goes to the tab panel and its chart, so shrinking the board to fit
the height makes the graph wider rather than leaving empty space beside it. The columns
never wrap: if they did, the tab panel would fall below the board. On narrow or
portrait-ish screens the split stacks, and the page may scroll — that is the deliberate
trade-off for keeping the board readable.

Rendered with `st.html(...)` (not `st.markdown(unsafe_allow_html=True)`), so the block
gets its own scoped container. All classes are prefixed `fc-` to avoid collisions.

### 8.3 Animation

Streamlit's `@st.fragment(run_every=...)` re-runs only the grid fragment on a timer. The
documented minimum interval is **1 second** — sub-second values raise. So the achievable
frame rate is ~1 fps, plus websocket latency.

That is acceptable *because the simulation is discrete*. A Game of Life at 1 fps is a
readable animation, not a broken one. We lean into it:

- one frame per tick, not per millisecond;
- CSS `transition` on opacity/transform so cells fade rather than snap;
- a "speed" control that changes **ticks per frame** (1, 2, 5, 20), not the frame rate.

So "fast" means "20 ticks per second shown as 1 frame per second", which is honest about
the medium and keeps the engine fast.

### 8.4 What Streamlit cannot do (and we accept)

- **Click a cell to inspect an agent.** A widget per cell is impossible at 900 cells.
  MVP workaround: an "Inspect" panel with a selectbox of agent IDs + a sortable table.
  Post-MVP: a custom component, if it is ever worth the JavaScript.
- **60 fps.** Requires a custom component or a canvas. Rejected for the MVP (see §10).
- **True streaming from a background thread.** Fragments re-run on the script thread;
  there is no push channel. Accepted.

---

## 9. Solana integration

### 9.1 Verified state of the tooling (checked 2026-11-08)

| Tool | Status | Verdict |
| --- | --- | --- |
| `seahorse-lang` (original) | **Deprecated**, broken with current Anchor | Do not use |
| `seahorse-dev` / `solana-developers/seahorse` | Fork, beta, v0.1.1, targets **Anchor 0.29**, self-described "not production-ready" | Not for a 20-hour build |
| `solders` 0.29 | Active, Rust-backed, supports Python 3.10–3.14 | Use |
| `solana-py` 0.41 | Active, requires Python ≥ 3.11; **sync `Client` removed in 0.40** — use `AsyncClient` | Use |
| Metaplex Core | Active standard; **SDKs exist only for JS/TS and Rust** | No Python SDK |
| `metaplex-foundation/python-api` | Legacy Token Metadata era, unmaintained | Do not use |

**Seahorse verdict: skip it.** It would mean writing a custom on-chain program to do
something an existing program already does, on a compiler that is beta and pinned to an
older Anchor. That is precisely the "unnecessary complexity" the brief forbids. It is a
great thing to explore *after* the hackathon, as a learning exercise, in an isolated repo.

**Metaplex verdict: skip it for the MVP.** There is no Python SDK. Minting would mean
hand-encoding a Core instruction with `solders` (discriminator + account metas + args) —
possible, but a poor use of the remaining hours, and fragile to demo.

### 9.2 Recommended MVP: signed memo attestation

A memo transaction is a real, verifiable, permanent record on Devnet, costs ~5 000
lamports, and is 30 lines of Python.

```
Memo (JSON, ~120 bytes):
{"app":"futurecoins","v":1,"ach":"genesis_discovery",
 "cfg":"sha256:9f2c…","tick":412,"ts":"2026-11-08T09:12:00Z"}
```

```python
# blockchain/attestation.py (shape, not final code)
async def attest(payload: dict, keypair: Keypair, rpc: str) -> str:
    """Send a memo transaction; return the signature."""
```

Why this is the right MVP:
- pure Python, no JS, no custom program, no new language;
- the achievement hash and config hash are genuinely on-chain and verifiable;
- it is honest: we call it an *attestation*, not an NFT.

### 9.3 Post-MVP: Metaplex Core NFT

When there is time, add a ~40-line Node helper (`mint_core.mjs`) invoked from Python via
`subprocess`. This is the **only** JavaScript in the project, and it is justified: Metaplex
publishes no Python SDK.

```
Python (Streamlit)  --subprocess-->  Node helper  --Umi-->  Metaplex Core (Devnet)
     |                                   |
     └── passes: player pubkey, metadata URI, name
```

- Cost: ~0.003 SOL per asset (Core single-account design).
- Program ID: `CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d` (same on Devnet).
- The player pastes their **public** address. The server mints with `owner = player`.
  No wallet adapter, no private key ever leaves the player's wallet.
- Metadata + PNG snapshot go to Irys/Arweave or IPFS; only the URI is on-chain.

### 9.4 Trust assumptions (must be documented in the UI)

- The server holds a Devnet hot wallet that pays for mints. It can mint, but it cannot move
  a player's assets: it never has the player's key.
- Minting is **not** proof that the achievement was earned — the server trusts its own
  local game state. A production version would need a program that verifies the claim.
- Devnet SOL has no value. Never point this at mainnet without a security review.

### 9.5 Key handling rules

1. Keypair from `SOLANA_KEYPAIR` env var or Streamlit secrets. Never in the repo.
2. `.env` and `*.json` keypair files in `.gitignore` from commit #1.
3. Never log a secret key. Log only the public address and the signature.
4. A pre-flight balance check, and a friendly error instead of a stack trace.

---

## 10. UI framework evaluation

| Option | Animation | Python-only | Build speed | Beginner docs | Verdict |
| --- | --- | --- | --- | --- | --- |
| **Streamlit 1.67** | 1 fps via fragments | ✅ | ★★★★★ | ★★★★★ | **Chosen** |
| NiceGUI | 30–60 fps, websockets | ✅ | ★★★ | ★★★ | Best alternative; more concepts to learn |
| FastAPI + HTMX | full control | ⚠️ HTML/JS | ★★ | ★★ | Too slow to build in 20 h |
| Gradio | rerun-based, similar limits | ✅ | ★★★★ | ★★★★ | Weaker layout control |
| PyScript / Pyodide | 60 fps canvas | ✅ | ★★ | ★★ | 10 MB+ download, no server-side Solana |
| Textual | terminal only | ✅ | ★★★ | ★★★ | Not a browser game |

Streamlit wins on the only axis that matters for a hackathon: **time to a working,
readable interface**, with free hosting. Its animation ceiling is a real constraint, and
§8.3 designs around it instead of pretending it does not exist.

The escape hatch is architectural, not aspirational: because the engine never imports
Streamlit, swapping in NiceGUI later is a rewrite of `interface/` only.

---

## 11. Dependencies

```toml
[project]
requires-python = ">=3.11"
dependencies = [
  "streamlit>=1.67,<2",
  "pandas>=2.2",          # tables + small charts only
]

[project.optional-dependencies]
solana = ["solana>=0.41,<0.42", "solders>=0.29,<0.30"]
dev    = ["pytest>=8", "ruff>=0.6", "mypy>=1.11"]
```

Deliberately absent: NumPy (not needed at 5 000 agents), Mesa (its scheduler/space
abstractions fight our grid-as-projection model), any plotting library beyond Streamlit's
built-ins, any database.

Python 3.14.6 is installed locally. `solana-py` requires ≥ 3.11 and lists 3.14 support;
`solders` 0.29 supports 3.14. Pin both if the Solana milestone happens.

---

## 12. Testing strategy

| Area | Test |
| --- | --- |
| Supply | `initial + Σissuance − Σburned == total` after 1 000 ticks |
| Halving | reward halves exactly at the interval; cap never exceeded |
| PoW | reward shares sum to issuance (±1e-9) |
| PoS | zero stake ⇒ no reward; share ∝ stake |
| Determinism | same seed, same config, 200 ticks ⇒ identical trace |
| Agents | population conservation; hysteresis prevents flapping |
| Events | conditions gate activation; severity scales with concentration |
| Metrics | health ∈ [0,100]; volatility ≥ 0; TPS ≤ capacity |
| Discovery | score ∈ [0,1]; identical config ⇒ 1.0; reproducible |
| Achievements | cannot be awarded unless the predicate is true; no double award |
| Grid | projection conserves population; render size ≤ limit |

`pytest` only. No browser tests, no snapshot tests of HTML. The engine is the product.

---

## 13. Risk register

| # | Risk | Impact | Mitigation |
| --- | --- | --- | --- |
| 1 | **20-hour deadline vs full MVP** | High | Ship the hackathon cut (no Solana). Solana is M9 and optional. |
| 2 | Streamlit's 1 s animation floor feels sluggish | Medium | Ticks-per-frame control, CSS transitions, batch simulation button |
| 3 | Emoji render differently per OS | Medium | Single-codepoint emoji only, fixed CSS cells, ASCII fallback toggle |
| 4 | Economy tuning produces absurd numbers | High | Clamps, sane presets, a `simulate 500 ticks` smoke test in CI |
| 5 | Similarity score feels arbitrary | Medium | Show per-parameter breakdown and weights in the UI |
| 6 | Devnet mint fails during the demo | High | Pre-recorded signature, offline mode, never gate a feature on it |
| 7 | Non-determinism from dict/set order | Medium | Id-ordered iteration, determinism test, no NumPy RNG |
| 8 | Educational accuracy vs simplification | Medium | Glossary states the abstraction; "model" badges on derived metrics |
| 9 | Python 3.14 wheel gaps for Solana libs | Medium | Isolated optional extra; test install before M9 |
| 10 | Streamlit Cloud cold start during judging | Medium | Deploy early, warm the app before presenting, local fallback |
| 11 | Scope creep into governance/marketplace | High | The "Out" list in GDD §11 is frozen |

---

## 14. What "done" means

A judge opens the app, moves three sliders, presses RUN, and within 20 seconds can say
*why* the price index moved. If they cannot, the interface failed regardless of how good
the engine is.
