# FutureCoins — Implementation Checklist

A beginner-friendly, ordered list. Each step says **what to do**, **how to know it worked**,
and **what you are learning**. Do not skip the "verify" line — that is where the learning is.

---

## Phase 0 — Setup (30 min)

- [ ] Create the project folder and `git init`.
- [ ] Add `.gitignore` **before** anything else:
      `.venv/`, `__pycache__/`, `.env`, `*.key`, `keypair*.json`, `data/`, `.streamlit/secrets.toml`
- [ ] Create and activate a virtual environment:
      `python -m venv .venv` then `.venv\Scripts\activate`
- [ ] Create `pyproject.toml` with `streamlit` and `pytest`.
- [ ] `pip install -e ".[dev]"`
- [ ] Verify: `pytest` runs (0 tests is fine), `streamlit hello` opens a browser.
- [ ] First commit: `chore: project skeleton`.

**Learning:** a virtual environment is a private box of packages. Without it, one project's
dependency upgrade breaks another's.

---

## Phase 1 — Engine, no UI (2.5 h)

- [ ] `simulation/config.py`: `SimConfig` and its sub-configs as frozen dataclasses.
- [ ] Write the six presets as constants (Blank Canvas is the default). **Verify:**
      `print(PRESETS["Blank Canvas"])`.
- [ ] `simulation/agents.py`: `Role` enum, `Agent` dataclass, `make_population()`.
- [ ] **Verify:** 600 agents, correct role counts, all cell coordinates inside the grid.
- [ ] `simulation/metrics.py`: `Metrics` dataclass and `network_health()`.
- [ ] **Verify:** health is 0–100 for hand-built edge cases (all inactive, all active).
- [ ] `simulation/engine.py`: `Simulation` with `run_tick()`, stages stubbed.
- [ ] `tests/test_engine.py`: population conservation, supply conservation.
- [ ] `tests/test_determinism.py`: same seed twice ⇒ identical trace.
- [ ] **Verify:** `pytest -q` green; a 500-tick headless script runs in under 2 seconds.

**Learning:** a dataclass is a named tuple with types. `frozen=True` means "config cannot
change mid-run" — a guarantee that removes a whole class of bugs.

**Trap:** if this phase feels slow, resist adding Streamlit. The engine is the project.

---

## Phase 2 — Grid + shell (2.5 h)

- [ ] `simulation/grid.py`: `project()` — agents → 1:1 cells; deterministic sampled snapshot when population > cells.
- [ ] `render_html()` producing the CSS grid. No Streamlit import in this file.
- [ ] **Verify:** population 4 000 on a 30×30 grid shows a clear sampled snapshot (e.g. "showing 900... 1:1 sampled view") while real totals remain accurate.
- [ ] `app.py`: `st.session_state` holds one `Simulation`; sidebar has Run/Pause/Reset.
- [ ] `@st.fragment(run_every="1s")` renders grid + metrics.
- [ ] **Verify:** RUN animates, PAUSE stops, RESET restores tick 0.
- [ ] Add the ASCII fallback toggle.
- [ ] **Verify:** emoji alignment on your machine **and** in a different browser.

**Learning:** Streamlit reruns your whole script on every interaction. `session_state` is
the only thing that survives a rerun. Fragments rerun *part* of the script — that is why
the grid can animate without resetting your sliders.

**Trap:** emoji width. If cells drift, it is the font, not your code. Fixed CSS width wins.

---

## Phase 3 — Consensus and money (2 h)

- [ ] `consensus.py`: PoW reward shares; PoS reward shares.
- [ ] Availability factor from participation / outages.
- [ ] Issuance, halving by **block count**, max-supply cap, fee burn.
- [ ] Agent entry/exit with `streak_bad` / `streak_good`.
- [ ] Tests: halving exact, cap never exceeded, shares sum to issuance.
- [ ] **Verify:** run Bitcoin preset for 1 000 ticks, then check supply < 21 M and reward
      still 50.

**Learning:** a protocol rule (halving interval) is not an outcome (21 M cap). The cap is
the *sum* of the series. This is the single best teaching moment in the game — make sure
the code makes it true.

**Trap:** floating point. Compare with `pytest.approx`, never `==`.

---

## Phase 4 — Economy and events (2.5 h)

- [ ] `economy.py`: demand, congestion, fee, price index, sentiment, volatility.
- [ ] Clamp the price. Clamp sentiment to [0, 1]. Never let a formula divide by zero.
- [ ] `events.py`: `EventSpec`, declarative conditions, active modifiers.
- [ ] Three events with severity scaling.
- [ ] Event log entries generated from templates + real numbers.
- [ ] **Verify:** force a crash at tick 50; the log explains it in one readable sentence.

**Learning:** every feedback loop needs damping, or it oscillates to infinity. `exp()` and
`clamp()` are the seatbelts.

**Trap:** if the price goes to 10^9 in 30 ticks, the damping is wrong. Fix the model, do
not add a bigger clamp.

---

## Phase 5 — Discovery (1.5 h)

- [ ] `targets.py`: Bitcoin 2009 + weights + confidence flags.
- [ ] `scoring.py`: weighted similarity + per-parameter breakdown.
- [ ] `hints.py`: directional hints, magnitude buckets, never the target value.
- [ ] Discovery page: riddle, score, band message, hint list.
- [ ] **Verify:** preset scores 1.00; a deliberately wrong config scores < 0.5; changing one
      parameter moves the score in the expected direction.

**Learning:** similarity is a design decision, not a fact. Showing the weights is what
makes it educational instead of a guessing game.

---

## Phase 6 — Achievements (1 h)

- [ ] `conditions.py`: pure predicates over `RunSummary`.
- [ ] `manager.py`: evaluate, dedupe by id, persist JSON.
- [ ] `snapshots.py`: 900-char grid encoding.
- [ ] **Verify:** a predicate that is false never awards; running twice never duplicates.

**Learning:** "idempotent" means doing it twice has the same effect as doing it once.

---

## Phase 7 — Education (1 h)

- [ ] `glossary.py`: 30–40 terms. Term, plain sentence, effect here, real example, link.
- [ ] `help=` on every widget.
- [ ] Info popover on every metric card.
- [ ] Searchable glossary page.
- [ ] **Verify:** no widget is unexplained; no link is bare (each says what you'll learn).

**Learning:** one data structure, four surfaces. Never duplicate educational text.

---

## Phase 8 — Ship (1.5 h)

- [ ] Dark neon theme, readable contrast (check with a colour-blindness simulator).
- [ ] Achievement popup + event toast.
- [ ] README with 3 screenshots and a 60-second demo script.
- [ ] Deploy to Streamlit Community Cloud.
- [ ] **Verify:** open the public URL on a phone-sized window. Does it still make sense?

---

## Phase 9 — Optional Solana (2 h, only if everything above is green)

- [ ] `pip install ".[solana]"` in a **separate** venv first; confirm wheels install on
      Python 3.14.
- [ ] Generate a Devnet keypair. Store it in `.streamlit/secrets.toml`, never in git.
- [ ] `blockchain/attestation.py`: build + send a Memo transaction with `AsyncClient`.
- [ ] **Verify:** signature visible on `explorer.solana.com/?cluster=devnet`.
- [ ] Handle failure gracefully: the achievement is still awarded locally.

**Learning:** a memo is the cheapest possible "proof on chain". It is a real transaction
with no program and no token.

**Trap:** `solana-py` 0.40+ removed the synchronous `Client`. Use `AsyncClient` and
`asyncio.run()` from the Streamlit callback.

---

## Always

- [ ] Commit after every green test, with a message that says *why*, not *what*.
- [ ] Never commit a key. If you do: rotate it, do not just delete the commit.
- [ ] Keep the engine free of `import streamlit`.
- [ ] When a number looks wrong, write a test before changing the formula.
- [ ] When you learn something, write it in `docs/GLOSSARY.md`. Future you is a beginner too.
