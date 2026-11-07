# FutureCoins — Game Design Document (v0.1)

> Status: draft for approval. Nothing here is implemented yet.

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
| Grid size | 40 × 20 = 800 cells | Fits a 1080p screen at readable emoji size |
| Cell content | one emoji, coloured by role | Instant role recognition |
| Cell meaning | one agent, or a cohort of agents | Population can exceed cell count |
| Update rate | 1 frame per tick, ~1–4 fps | Streamlit's minimum auto-rerun is 1 s |
| Population display | always shown separately | Never imply 800 agents when there are 4,000 |

**Cohort rule.** When `population > cells`, one cell represents
`ceil(population / cells)` agents. The cell shows the *dominant* role in that cohort and
its opacity reflects how many of the cohort are active. The header always reads, e.g.:

```
Population: 4,820 agents · 800 cells · ~6 agents per cell
```

This is stated, not hidden. Confusing population with cell count is the single easiest
way to teach the wrong lesson.

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
reconstruct the configuration.

### Target: Bitcoin — Genesis, 2009

Shown to the player:

> *"A network with no premine, no company, no foundation. Blocks arrive slowly and
> predictably. The reward for making a block is generous at first and shrinks on a fixed
> schedule. Nobody can burn coins. There are no validators, because there is no stake."*

Hidden: the reference config. Compared with a weighted similarity score (see
ARCHITECTURE §7).

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
| `survivor` | Survivor | 8 760 ticks (one simulated year) with health > 0 |
| `genesis_discovery` | Genesis Discovery | Bitcoin 2009 similarity ≥ 0.95 |
| `crisis_survivor` | Crisis Survivor | Survive a severity ≥ 0.6 event without health < 20 |
| `network_architect` | Network Architect | ≥ 90 % participation and ≥ 50 active nodes for 100 ticks |

Each award records: id, name, description, timestamp, config hash, final metrics, and a
compact grid snapshot (800 characters, one per cell). Persisted to a local JSON file in
the MVP; no database.

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

## 12. Open questions for the creator

1. **Hackathon deadline.** The MLH Solana Hackathon you're checked into closes
   **2026-11-08 18:00 UTC** — roughly 20 hours from now. The full MVP above is ~16 focused
   hours *if nothing goes wrong*, which for a first blockchain project it will. Do we build
   the 20-hour cut (no Solana), or the full MVP for a later submission?
2. **Language of the interface.** English or French? The docs are English; the UI could be
   either. Mixing is worse than choosing.
3. **Visual identity.** Emoji-only grid (fast, charming, inconsistent across OS) or emoji +
   CSS colour coding (slower to build, far more readable)? Recommendation: both.
4. **Bitcoin reference data confidence.** Some 2009 parameters are genuinely uncertain
   (typical transactions per block). Accept "medium confidence" flags in the UI, or drop
   uncertain parameters from the score?
