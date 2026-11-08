# FutureCoins — Game Design Document (v0.1)

> Status: design reference (updated). The local free-to-play MVP is implemented (engine, Streamlit UI, tests, presets, Discovery Mode, achievements). Some original draft details evolved during implementation; this document remains a design/architecture reference.

---

## 1. Vision

FutureCoins is an educational sandbox where the player **designs a cryptocurrency's rules**
and then **watches a simulated population live inside those rules**.

The player does not "win" by making a number go up. The player wins by *understanding why
the number did what it did*.

### Design pillars

1. **Consequence over configuration.** Every slider must visibly change behaviour within
   a few ticks. A parameter that does nothing is a bug.
2. **Emergence over scripting.** No cutscenes. Crises arise from agent decisions plus
   randomness, not from a scripted timeline.
3. **Correct words, plain explanations.** Use "validator", "halving", "circulating supply"
   — then explain them in one sentence, in place.
4. **Honest abstraction.** Every simplified metric is labelled as such. We never imply the
   simulator reproduces a production blockchain.
5. **Understandable code.** The creator must be able to read every line. Cleverness is a
   cost, not a feature.

### Anti-goals

- Not a trading game, not a prediction tool, not financial advice.
- Not a blockchain. There is no consensus, no cryptography, no ledger.
- Not a marketplace, not multiplayer, not a token launch.
- Not a full governance simulator in v1.

---

## 2. Core loop

```
   ┌──────────────┐
   │  CONFIGURE   │  pick a preset, or move sliders
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │    RUN       │  ticks advance, grid animates, metrics update
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   OBSERVE    │  read the dashboard, open the event log, inspect agents
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   EXPLAIN    │  tooltips, glossary, "why did this happen?" panel
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │   ADJUST     │  change one thing, run again, compare
   └──────┴───────┘
```

The loop is deliberately short. A full "change one parameter → see the consequence" cycle
should take under 60 seconds.

### Session shape

- **Sandbox run:** free play, no target. 5–50 ticks typical.
- **Discovery run:** a target exists, a similarity score is shown, hints guide you.
- **Crisis run:** a scenario starts with a specific shock already in progress.

---

## 3. The grid

The grid is the emotional centre of the game. It must *look alive*.

| Property | MVP value | Rationale |
| --- | --- | --- |
| Grid size | 30 × 30 = 900 cells | Square board, readable emoji on a laptop |
| Cell content | one emoji, coloured by role | Instant role recognition |
| Cell meaning | one displayed agent (1:1); deterministic snapshot when population > cells | Population can exceed cell count; totals always shown |
| Offline agents | the cell becomes blank | The grid shows who is online, not who exists |
| Empty slots | a faint dot | Never confused with an agent that left |
| Update rate | 1 frame per tick, ~1–4 fps | Streamlit's minimum auto-rerun is 1 s |
| Population display | always shown separately | Never imply 900 agents when there are 4,000 |

**Sampled-view rule (implemented).** When `population > cells`, the grid shows a deterministic **1:1 snapshot of part of the population** (one displayed agent per shown cell), stable for the same seed/population. Totals, indicators, and simulation behavior always use the **full population**. The UI makes the sampled view explicit, e.g.:

```
4,820 agents · showing 900 of 900 cells (1:1 sampled view, deterministic) · 42 offline (hidden)
```

This is stated, not hidden. Confusing a visible sample with the full population is the single easiest
way to teach the wrong lesson. All indicators use the full population.

**Sizing.** The board is square and sized from the *height* budget first: hero, indicator
cards, population line and legend take their space, and the board fills what remains. A
30 × 30 board therefore never forces a vertical scroll on a wide screen. On a wide
landscape viewport the board sits beside the tabs, and the width the board gives up goes
to the tab panel and its chart. On a narrow or portrait-ish viewport the tabs stack below
the board instead of squeezing it.

---

## 4. Agent roles

Nine roles are specified in the brief. The MVP implements **six as agents** and **three as
institutional forces**, because media, governance and institutions act at the population
level and modelling them as 40 identical emoji would be dishonest without adding much.

| Role | Emoji | MVP | Core behaviour |
| --- | --- | --- | --- |
| Miner | ⛏️ | agent | Earns block rewards by hashrate share; exits when unprofitable |
| Validator | ✅ | agent | Earns rewards by stake share; exits when unprofitable |
| User | 👤 | agent | Generates transactions; leaves if fees are high or reliability is low |
| Trader | 📈 | agent | Buys/sells on momentum; amplifies volatility |
| Developer | 👨‍💻 | agent | Improves capacity and health slowly; can resign after a governance shock |
| Attacker | 🏴 | agent | Raises invalid-transaction rate and drains confidence (abstract only) |
| Media | 📺 | global force | `media_bias` shifts sentiment |
| Governance | 🏛️ | global force | `decentralization` sets upgrade speed and capture risk |
| Institutions | 🏢 | global force | `institutional_participation` adds liquidity and adoption |

Emoji note: single-codepoint emoji only. ZWJ sequences (👨🏻‍💼, 🏴‍☠️) render
inconsistently across Windows/macOS/Linux fonts and break fixed-width alignment. This is
tested in Milestone 2 and an ASCII fallback toggle is provided.

### Behaviour model (shared shape)

Every agent has the same fields, so one loop can update all of them:

```python
@dataclass
class Agent:
    id: int
    role: Role
    cell: tuple[int, int]      # (row, col) — spatial index, not physics
    balance: float             # tokens held
    active: bool
    confidence: float          # 0..1, personal optimism
    cost_per_tick: float       # operating cost
    capacity: float            # hashrate (miner) or stake (validator) or tx rate (user)
    streak_bad: int            # consecutive unprofitable ticks (hysteresis)
    streak_good: int
```

Role-specific behaviour is a small function `step_role(agent, ctx)`, dispatched by role.
No inheritance hierarchy: a `match` statement is easier to read than five subclasses.

### Why hysteresis matters

Without it, agents flip active/inactive every tick and the grid strobes. Each agent must
be unprofitable for `exit_patience_ticks` (default 3) before leaving, and profitable for
`entry_patience_ticks` (default 5) before returning. This is also how real mining works —
you do not unplug a rig because one block was unlucky.

---

## 5. Configuration

Three interface modes, all writing to the same `SimConfig` dataclass.

### Beginner Mode — 8 controls

| Control | Range | Default |
| --- | --- | --- |
| Consensus | PoW / PoS | PoW |
| Block time (target) | 1 s – 15 min | 10 min |
| Initial supply | 0 – 1 B | 0 |
| Max supply | 1 M – ∞ | 21 M |
| Initial block reward | 0 – 100 | 50 |
| Halving interval | 10 k – 1 M blocks | 210 k |
| Transaction fee (base) | 0 – 10 | 0.5 |
| Population size | 50 – 5 000 | 600 |

### Advanced Mode — adds

Transaction capacity, fee burn %, participation costs, per-role population, per-role
aggressiveness, event probabilities, sentiment adaptivity, liquidity depth, governance
centralization.

### Experimental Mode — adds

Raw numeric entry for every field, seed control, event scheduler override, and (post-MVP)
a validated JSON rules file. **Never** arbitrary Python execution.

### Presets (all modes)

`Blank Canvas`, `Bitcoin 2009`, `Ethereum 2015`, `Solana 2020`, `Stable Utility Coin`,
`Chaos Sandbox`. Presets are just named `SimConfig` values — no special code path.

**Blank Canvas is the default.** It is a healthy, ordinary network (570 agents, no cap,
50-token reward, 600-second blocks) that scores 78 % against the Bitcoin 2009 target. If
the app opened on the Bitcoin preset instead, Discovery Mode would be solved before the
player touched a slider, and the *Genesis Discovery* achievement would unlock for free.
A test now enforces that only the Bitcoin preset reaches the 95 % band.

---

## 6. Dashboard

Twelve metric cards, grouped so related numbers sit together and the *difference* is
visible side by side.

**Network**
- Active nodes / total nodes (two numbers in one card, always)
- Block interval (seconds, simulated)
- Transactions per second
- Average fee per transaction

**Money**
- Total supply
- Circulating supply
- Inflation rate (annualised, simulated)
- Burned to date

**Market**
- Simulated price index (base 100 at launch)
- Volatility (EWMA of |log return|)
- Market sentiment (0–100)

**Health**
- Network health (0–100, with the weighted breakdown available on click)

Every card has an ⓘ that opens the same explanation used in the glossary. Cards whose
value is a *model output* (price, health, sentiment) carry a small "model" badge.

### Metric pairs that must never be confused

| Pair | The lesson |
| --- | --- |
| Block time vs TPS | Block time is how often a block is made; TPS is how many transactions fit per second. A chain can have slow blocks and high TPS. |
| Total vs circulating supply | Total is everything minted minus everything burned. Circulating excludes the protocol treasury. |
| Price index vs market price | Ours is a formula. A real price is what a buyer and seller agree on. |
| Population vs active participants | Registered agents vs agents currently doing work. The gap *is* the story. |

---

## 7. Events

An event is data, not code:

```python
@dataclass(frozen=True)
class EventSpec:
    id: str
    name: str
    category: Literal["economic", "technical", "social"]
    probability_per_tick: float
    duration_ticks: int
    severity: float                  # 0..1
    effects: dict[str, float]        # multiplier per effect channel
    conditions: tuple[Condition, ...]  # declarative, JSON-able
    explanation: str                 # template with {placeholders}
```

### MVP events (3 required, 4 if time allows)

| Event | Category | Trigger | Effect | Lesson |
| --- | --- | --- | --- | --- |
| Market Crash | economic | random, higher if price rose > 40 % recently | sentiment −, price shock, traders sell | Reflexivity: price moves sentiment moves price |
| Network Congestion | technical | demand > 85 % capacity for 2 ticks | capacity −, fees +, users churn | Fees are a rationing mechanism |
| Negative Media Coverage | social | random, higher if health < 50 | sentiment −, adoption − | Narrative is an economic force |
| Validator Exodus | technical | PoS and participation < 40 % | deactivates a share of validators | Security scales with participation |

### Severity scaling

Severity is not purely random. It scales with the player's configuration:

```
effective_severity = base_severity
                   × (1 + concentration_penalty)     # few validators => worse
                   × (1 - resilience)                # healthy network absorbs shocks
```

A validator exodus in a 5-validator network is a catastrophe; in a 500-validator network
it is a headline. This is the mechanic that makes configuration choices *matter*.

### Event log

Every event writes a human sentence with real numbers, e.g.:

> **Tick 47 — Validator exodus.** 14 of 52 validators went offline. Participation cost
> (3.1/tick) exceeded expected reward (2.4/tick) after the price fell 38 %. Network health
> dropped 71 → 43. Block production is now 60 % of target.

That paragraph is generated from templates plus the actual tick state — not hand-written
per event.

---

## 8. Discovery Mode

The player is given a target's *behaviour* description, never its parameters, and must
reconstruct the configuration. Similarity feedback appears **after the simulation starts** (no pre-run percentage clue). Targets are educational abstractions with stated confidence/caveats.

### Implemented targets (abstractions)
- **Bitcoin — Genesis, 2009** (`bitcoin_2009`): no premine, slow/predictable blocks, generous reward that halves on schedule, no burn, PoW/no stake. High-confidence core parameters; some early-era estimates marked lower confidence.
- **Ethereum — Frontier, 2015 (early PoW-era abstraction)** (`ethereum_2015`): fast blocks, significant launch allocation/premine, no Bitcoin-style halving in the abstraction, no early fee-burn mechanism. Simplified; real Ethereum evolved over time.
- **Solana — Launch era, 2020 (abstraction)** (`solana_2020`): PoS validators, very fast block/slot pace, high throughput, very low fees, partial fee burn, no Bitcoin-style halving in the abstraction. Simplified; real Solana mechanics/schedules differ.

Each target has a weighted similarity score, visible breakdown, and progressive digit-free hints. Reaching **>= 95%** awards the matching discovery achievement and can unlock the corresponding preset.

### Feedback bands

| Score | Message |
| --- | --- |
| < 0.40 | "This is a different kind of money." |
| 0.40–0.60 | "Some characteristics match." |
| 0.60–0.80 | "You're getting close." |
| 0.80–0.95 | "Almost there — one or two rules are off." |
| ≥ 0.95 | "Discovery achieved." |

Hints are directional and never leak the value:

- "Your blocks are far too frequent for this era."
- "Your supply has a ceiling, but the schedule that creates it is too fast."
- "Something is being destroyed that this network never destroyed."

### The teaching moment

Bitcoin's 21 M cap is **not a constant in the code**. It is the sum of a geometric series
produced by halving. When the player gets close, the game says so explicitly:

> You set a hard cap of 21,000,000. Bitcoin never did. Its cap is the *result* of halving
> 50 BTC every 210,000 blocks forever: 210,000 × 50 × 2 = 21,000,000. Try removing your cap
> and setting the halving interval instead.

That single insight is worth more than the whole score.

---

## 9. Achievements

| ID | Name | Condition |
| --- | --- | --- |
| `first_currency` | First Currency | Complete 1 tick with ≥ 1 active agent |
| `survivor` | Survivor | 1825 ticks (five simulated years) with health > 0 |
| `genesis_discovery` | Genesis Discovery | Bitcoin 2009 similarity ≥ 0.95 |
| `ethereum_discovery` | Frontier Discovery | Ethereum 2015 early-era abstraction similarity ≥ 0.95 |
| `solana_discovery` | High-Throughput Discovery | Solana 2020 launch-era abstraction similarity ≥ 0.95 |
| `crisis_survivor` | Crisis Survivor | Survive a severity ≥ 0.6 event without health < 20 |
| `network_architect` | Network Architect | ≥ 90 % participation and ≥ 50 active nodes for 100 ticks |

Each award records: id, name, description, timestamp, config hash, seed, tick, metrics, and a
compact grid snapshot (rows×cols characters). Persisted to a local JSON file in the MVP; no database. Awards can be exported/imported as JSON.

### NFT minting (optional, post-MVP)

An achievement can be minted as a Metaplex Core asset on Solana **Devnet**. See
ARCHITECTURE §9. Minting is never required to play and never blocks a feature.

---

## 10. Education layer

Four surfaces, all fed by one glossary source of truth:

1. **Tooltip** (`help=` on every widget): one sentence.
2. **Info popover**: term, plain explanation, effect in this simulation, real-world
   example, one link.
3. **Glossary page**: searchable, filterable by category.
4. **"Why did this happen?" panel**: the last 10 ticks of notable changes, in sentences.

Rules:
- The technical term is always shown first. We explain, we do not rename.
- No link is presented without saying what the player will learn from it.
- Every "model output" metric is labelled as a model output.

---

## 11. MVP scope (frozen)

**In**
1. Configurable currency (Beginner + Advanced).
2. Agent simulation, 6 roles.
3. Emoji grid, animated.
4. PoW and PoS abstractions.
5. Dashboard, 12 metrics.
6. Run / Pause / Reset / Speed.
7. 3 events + event log.
8. Simplified economy + price index.
9. Bitcoin 2009 discovery + similarity + hints.
10. 3 achievements.
11. Glossary + tooltips + resources.
12. Deterministic seeded runs.
13. Tests for every module.
14. Optional: Solana Devnet memo attestation.

**Out (v1.1+)**
- Media / governance / institutions as agents.
- Difficulty retargeting, unbonding periods, slashing.
- More discovery targets (Ethereum, Solana, Visa, PayPal).
- Metaplex Core NFT minting.
- JSON rule engine.
- Multiplayer, marketplace, leaderboards.
- Wallet connection.

---

## 12. Current status & further development

**Implemented (local MVP):** configurable currency + presets, 6-role agent simulation on a 30×30 grid (1:1 deterministic sampled snapshot when population > cells), PoW/PoS abstractions, dashboard/health/why/history, events, simplified economy/price index (model), Discovery Mode targets for **Bitcoin 2009, Ethereum 2015 (early-era abstraction), Solana 2020 (launch-era abstraction)** with weighted scoring/progressive digit-free hints and pre-run gating, achievements with snapshots + JSON export/import, glossary/resources, deterministic seeded runs, and tests/lint.

**Discarded / evolved decisions (kept for context):** cohort-blended grid cells were replaced by a 1:1 sampled snapshot for legibility; “network health” means *cryptocurrency* network health (model), not internet connectivity; price/sentiment/health are model outputs (not forecasts).

**Further development (deferred, not required for MVP):**
- Add a Stable Utility Coin discovery target/unlock path (currently a locked mystery with no unlock route) and additional historical/educational targets.
- Expand event/agent depth (e.g., governance/media/institutions as richer actors, more scenarios) and calibrate balance with more playtest data.
- Improve onboarding/analytics-free UX polish, accessibility, and mobile-specific tuning (current design tested as usable on Android).
- Optional post-MVP adapters only if desired later: Solana Devnet memo attestation / NFT badge **without** changing the engine’s independence from blockchain/wallet/marketplace features.

**Historical open questions (draft context):** deadline/language/visual identity/reference-confidence questions above were part of the original planning draft; current implementation uses visible confidence flags in Discovery and English UI/docs.
