# FutureCoins — Learning Resources

> Every link here is attached to a specific in-game moment. The game never shows a bare
> link: it first says *what you just did* and *what to read next to understand it*.

---

## How to use this list

Do not read these top to bottom. Each entry is triggered by a moment:

| When the player… | Show |
| --- | --- |
| launches their first currency | §1 Bitcoin whitepaper (sections 1–4 only) |
| moves the block time slider | §2 Block time and difficulty |
| sets a max supply | §3 The 21 M cap is a sum, not a constant |
| switches to Proof of Stake | §4 PoS explained |
| sees congestion and rising fees | §5 Blockspace and fee markets |
| watches agents leave | §6 Agent-based modelling |
| watches the grid | §7 Cellular automata and Game of Life |
| tries Discovery Mode | §8 Bitcoin history and primary sources |
| mints an achievement | §9 Solana and NFTs |

---

## 1. Bitcoin — the primary source

- **Bitcoin: A Peer-to-Peer Electronic Cash System** — https://bitcoin.org/bitcoin.pdf
  Read sections 1–4. Section 4 (Proof-of-Work) is the only one you need for the game.
  *What you'll learn:* why a chain of blocks plus costly work replaces a central authority.

- **Bitcoin Developer Guide** — https://developer.bitcoin.org/devguide/
  *What you'll learn:* how blocks, transactions and fees actually fit together.

- **Bitcoin Developer Reference — Block Chain** — https://developer.bitcoin.org/reference/block_chain.html
  *What you'll learn:* the exact fields in a block header. Compare with our `Metrics`.

---

## 2. Block time, difficulty, and why they are different

- **Ethereum — Blocks** — https://ethereum.org/en/developers/docs/blocks/
  *What you'll learn:* how slot time differs from block time, and why "faster blocks" is not
  automatically "more throughput".

- **Bitcoin Wiki — Difficulty** — https://en.bitcoin.it/wiki/Difficulty
  *What you'll learn:* the retargeting rule we deliberately simplified in v1. It is the
  single best example of a protocol adapting to its own participants.

---

## 3. The 21 million cap

- **Bitcoin Wiki — Controlled supply** — https://en.bitcoin.it/wiki/Controlled_supply
  *What you'll learn:* the geometric series behind 21 M, and why the cap is a consequence
  of halving rather than a line of code.

This is the payoff of the Bitcoin discovery challenge. Show it only after the player
removes their hard cap and gets close to the halving interval.

---

## 4. Proof of Stake

- **Ethereum — Proof of Stake** — https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/
  *What you'll learn:* stake, slashing, and why "nothing at stake" was a real objection.

- **Ethereum — Staking** — https://ethereum.org/en/staking/
  *What you'll learn:* the economics a validator actually faces — the same reward ÷ cost
  decision our ✅ agents make.

---

## 5. Fees and blockspace

- **Ethereum — Gas and fees** — https://ethereum.org/en/developers/docs/gas/
  *What you'll learn:* why fees are a rationing mechanism, not a price list.

- **Ethereum Improvement Proposal 1559** — https://eips.ethereum.org/EIPS/eip-1559
  *What you'll learn:* the base-fee burn. Our `burn_rate` parameter is a cartoon version
  of this.

---

## 6. Agent-based modelling

- **Agent-based model (overview)** — https://en.wikipedia.org/wiki/Agent-based_model
  *What you'll learn:* why macro behaviour can emerge from simple micro rules.

- **Mesa documentation** — https://mesa.readthedocs.io/
  *What you'll learn:* how a real Python ABM framework structures agents, spaces and
  schedulers. We do not use Mesa (its abstractions fight our grid), but reading one example
  will make our `Simulation.run_tick()` obvious by comparison.

- **NetLogo — Models library** — https://ccl.northwestern.edu/netlogo/models/
  *What you'll learn:* classic ABM experiments you can port as scenarios later.

---

## 7. Cellular automata

- **Cellular automaton** — https://en.wikipedia.org/wiki/Cellular_automaton
  *What you'll learn:* the formal definition, and why our model is *not* a pure CA.

- **Conway's Game of Life** — https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life
  *What you'll learn:* the neighbour-update pattern you already implemented — and the
  difference between a cell's state and an agent's balance.

---

## 8. Discovery Mode sources

- **Bitcoin — Original release notes (2009)** — https://bitcoin.org/en/release/v0.1.0
  *What you'll learn:* what was actually shipped, versus what was added later.

- **Bitcoin Wiki — Genesis block** — https://en.bitcoin.it/wiki/Genesis_block
  *What you'll learn:* the first block, its timestamp, and the message inside it.

- **Ethereum — History** — https://ethereum.org/en/history/
  *What you'll learn:* Frontier (2015) and what "launch era" really meant.

- **Solana — Documentation** — https://solana.com/docs
  *What you'll learn:* why sub-second slots change what is possible, and what they cost.

Be explicit in the UI: historical parameters are **estimates**, and each one carries a
confidence flag. We are teaching the shape of a system, not certifying a fact.

---

## 9. Solana and NFTs

- **Solana Docs — Introduction** — https://solana.com/docs
  *What you'll learn:* accounts, programs, and why fees are so small.

- **Solana — Devnet** — https://solana.com/docs/references/clusters
  *What you'll learn:* what Devnet is for, and how to get free SOL.

- **Metaplex Core — Overview** — https://www.metaplex.com/docs/smart-contracts/core
  *What you'll learn:* why one account per NFT is cheaper than three.

- **Metaplex Core — Creating Assets** — https://www.metaplex.com/docs/smart-contracts/core/create-asset
  *What you'll learn:* the exact mint flow our optional Node helper mirrors.

- **solana-py documentation** — https://michaelhly.com/solana-py/
  *What you'll learn:* `AsyncClient`, transactions, and memo instructions in Python.

- **solders documentation** — https://kevinheavey.github.io/solders/
  *What you'll learn:* keypairs, public keys, and transaction serialisation.

---

## 10. Game and interface design (for the builder, not the player)

- **Streamlit — `st.fragment`** — https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
  *What you'll learn:* the 1-second auto-rerun limit that shapes our animation design.

- **Streamlit — Working with fragments** — https://docs.streamlit.io/develop/concepts/architecture/fragments
  *What you'll learn:* why a fragment rerun is the only way to animate without resetting state.

---

## A note on link hygiene

Every link above was checked against the organisation that publishes it. In the app:

1. Never show a URL without a sentence saying what the player will learn.
2. Prefer primary sources (bitcoin.org, ethereum.org, solana.com) over blog posts.
3. If a link 404s, remove it — a dead "learn more" is worse than no link.
