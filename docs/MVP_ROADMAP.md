# FutureCoins — MVP Roadmap

> Status: draft for approval. Hours are estimates for one developer learning as they go.

---

## 0. The deadline, stated plainly

The MLH **Solana Hackathon** you are checked into runs 2026-11-06 17:00 UTC →
**2026-11-08 18:00 UTC**. At the time of writing that is roughly **20 hours**.

The full brief (15 MVP items + Solana NFT) is a 40–60 hour project. Trying to build all of
it in 20 hours produces a demo where nothing quite works. So there are two tracks:

| Track | Scope | When |
| --- | --- | --- |
| **A — Hackathon Cut** | Items 1–13 of the MVP, **no blockchain** | Next 20 hours |
| **B — Full MVP** | Track A + Solana attestation + NFT + polish | Following 1–2 weeks |

Track A is a complete, honest, demoable game. Track B adds the blockchain chapter once the
game is already good. This ordering is also what the brief asks for: *"The simulation
should work independently of Solana."*

---

## Track A — Hackathon Cut (≈ 15 h work + 5 h buffer)

### M0 · Foundations — 0.5 h

**Build:** git repo, `.gitignore`, `pyproject.toml`, virtualenv, `pytest` running one
trivial test, `streamlit hello` works.

**Acceptance:** `pytest` green; `streamlit run app.py` shows a page.

**You learn:** project layout, why `pyproject.toml` beats a bare `requirements.txt`,
why `.gitignore` comes before the first commit (secrets).

---

### M1 · Engine core — 2.5 h

**Build:**
- `config.py`: `SimConfig` + sub-dataclasses + the 6 presets (including Blank Canvas).
- `agents.py`: `Agent`, `Role`, `make_population(config, rng)`.
- `engine.py`: `Simulation` with the 10-stage pipeline, stages stubbed except agents,
  supply and metrics.
- `metrics.py`: `Metrics` snapshot + `network_health`.
- Tests: population conservation, supply conservation, determinism.

**Acceptance:** a headless script runs 500 ticks and prints a metrics table. No UI at all.
Same seed twice ⇒ identical output.

**You learn:** dataclasses, frozen configs, dependency injection of a seeded RNG,
why "pure function" makes tests trivial.

**Do not** touch Streamlit in this milestone. If you do, the engine becomes untestable.

---

### M2 · The grid — 2.5 h

**Build:**
- `grid.py`: `project(agents, rows, cols) -> cells` with cohort support.
- `grid.render_html(cells)` producing the CSS grid.
- `app.py`: sidebar controls (Run/Pause/Reset/Speed), `st.session_state` holding the
  `Simulation`, `@st.fragment(run_every="1s")` for the grid + metrics.
- ASCII fallback toggle.

**Acceptance:** press RUN, the grid changes every second, population counter is correct
when population > 800, pause actually pauses.

**You learn:** Streamlit's rerun model, `session_state`, fragments, why a fixed CSS cell
width beats monospace alignment for emoji.

**Risk checkpoint:** if emoji look broken on your machine, switch the role set now — not
at hour 18.

---

### M3 · Consensus and money — 2 h

**Build:**
- `consensus.py`: PoW and PoS block production, reward shares, participation, availability.
- Monetary policy: issuance, halving by block count, max-supply cap, fee burn.
- Agent entry/exit with hysteresis.
- Tests: halving exactness, cap never exceeded, reward shares sum to issuance.

**Acceptance:** switching PoW→PoS visibly changes which agents earn; halving at
210 000 blocks visibly drops miner income and triggers exits.

**You learn:** the difference between a protocol rule and an economic outcome; why
hysteresis is required in agent models.

---

### M4 · Economy and events — 2.5 h

**Build:**
- `economy.py`: demand, fees, congestion, price index, sentiment, volatility.
- `events.py`: `EventSpec`, trigger conditions, active modifiers, severity scaling,
  human-readable log entries.
- Three events: Market Crash, Network Congestion, Negative Media Coverage.
- "Why did this happen?" panel (last 10 notable changes).

**Acceptance:** a Market Crash produces a visible price drop, a sentiment drop, and a
sentence in the log explaining it with real numbers.

**You learn:** reflexive systems (price → sentiment → price), why every feedback loop
needs a damping term.

---

### M5 · Discovery Mode — 1.5 h

**Build:**
- `targets.py`: Bitcoin 2009 with weights + confidence flags.
- `scoring.py`: weighted similarity + per-parameter breakdown.
- `hints.py`: directional hints from the breakdown.
- Discovery page: riddle text, live score, band message, hints.

**Acceptance:** setting the Bitcoin preset scores 1.00; a random config scores low;
hints never print a target value.

**You learn:** how to compare heterogeneous parameters; why "confidence" belongs in a
scoring model.

---

### M6 · Achievements — 1 h

**Build:**
- `conditions.py`: pure predicates.
- `manager.py`: evaluate after each tick, dedupe, award, persist to `data/achievements.json`.
- `snapshots.py`: 800-char grid encoding.
- Three achievements: First Currency, Survivor, Genesis Discovery.

**Acceptance:** an achievement cannot be awarded when its predicate is false; re-running
does not duplicate it; the JSON survives a restart.

**You learn:** idempotency, and why "save the evidence" beats "save the badge".

---

### M7 · Education layer — 1 h

**Build:**
- `glossary.py`: 30–40 terms, one source of truth.
- Tooltips via `help=` on every widget; info popovers on every metric card.
- Glossary page with search.
- `resources.py` links attached to the relevant parameter.

**Acceptance:** every slider has a tooltip; every metric card has an explanation; the
glossary is searchable.

**You learn:** content design is engineering — one data structure, many surfaces.

---

### M8 · Polish, docs, deploy — 1.5 h

**Build:** dark neon theme CSS, event toasts, achievement popups, README with screenshots,
60-second demo script, deploy to Streamlit Community Cloud.

**Acceptance:** a stranger can open the URL and understand the game without you talking.

---

### Buffer — 5 h

Reserved for: emoji problems, economy tuning, deployment issues, and the demo video.
Do not spend it on new features.

---

## Track B — Full MVP (post-hackathon, ≈ 25 h)

| Milestone | Hours | Content |
| --- | --- | --- |
| B1 | 3 | Difficulty retargeting, unbonding, slashing, validator commission |
| B2 | 4 | Media / Governance / Institutions promoted to agents |
| B3 | 4 | Ethereum 2015 + Solana 2020 + Visa/PayPal discovery targets |
| B4 | 3 | Solana Devnet memo attestation (pure Python) |
| B5 | 5 | Metaplex Core NFT mint via Node helper, metadata upload, gallery |
| B6 | 3 | JSON rule engine with schema validation |
| B7 | 3 | Custom Streamlit component for click-to-inspect (optional) |

---

## What is deliberately *not* scheduled

- A custom Solana program (Seahorse or Anchor). Not needed, not worth the risk.
- Multiplayer, accounts, database, marketplace.
- 60 fps rendering.
- Mobile layout.

---

## Definition of done for Track A

1. A stranger presses RUN and sees a living network within 2 seconds.
2. Changing one slider produces a visible, explainable difference within 20 ticks.
3. Every number on screen can be traced to a formula in `ARCHITECTURE.md`.
4. `pytest` is green and covers supply, rewards, determinism, scoring, achievements.
5. The game runs with no network connection and no wallet.
