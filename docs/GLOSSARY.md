# FutureCoins — Glossary

> The single source of truth for every explanation shown in the game. `education/glossary.py`
> is generated from this document. If a term is not here, it does not appear in the UI.

Format: **Term** — one-sentence definition. *In the game:* what it changes.
*Real world:* an example.

---

## Money and supply

**Token supply** — the total number of tokens that exist right now.
*In the game:* the "Total supply" card. It only changes when tokens are minted or burned.
*Real world:* Bitcoin's supply grows with every block, then stops growing.

**Circulating supply** — the part of the supply that is not locked in a treasury or reserve.
*In the game:* total supply minus the protocol treasury.
*Real world:* a company holding 40 % of its own tokens means circulating supply is 60 %.

**Inflation** — an increase in the total number of tokens in circulation.
*In the game:* the annualised issuance rate, as a percentage.
*Real world:* Bitcoin's inflation started near 0 % and fell at every halving.

**Issuance** — new tokens created by the protocol, usually as a reward for producing blocks.
*In the game:* `blocks_this_tick × block_reward`.
*Real world:* every Bitcoin block creates new BTC until the reward reaches zero.

**Block reward** — tokens paid to whoever produces a block.
*In the game:* a slider. Higher reward attracts more miners/validators, then dilutes holders.
*Real world:* 50 BTC in 2009, 3.125 BTC in 2024.

**Halving** — an event where the block reward is cut in half, usually on a fixed schedule.
*In the game:* the reward halves every *N* blocks. Bitcoin: every 210 000 blocks.
*Real world:* Bitcoin halvings in 2012, 2016, 2020, 2024.

**Max supply** — a hard ceiling on how many tokens can ever exist.
*In the game:* if set, issuance stops at the cap.
*Real world:* Bitcoin's 21 M is not a constant in its code — it is the *sum* of a halving
series. That distinction is the point of the Bitcoin challenge.

**Burning** — permanently destroying tokens so they can never be used again.
*In the game:* a percentage of transaction fees is removed from supply.
*Real world:* Ethereum burns part of every transaction fee (EIP-1559).

**Tokenomics** — the economic rules that determine how a cryptocurrency's tokens are
created, distributed and used.
*In the game:* the whole Monetary panel.
*Real world:* a token with infinite issuance and no utility tends to lose value.

---

## Network and consensus

**Consensus mechanism** — the method a network uses to agree on which transactions are valid.
*In the game:* Proof of Work or Proof of Stake. It decides who earns rewards and how.
*Real world:* Bitcoin uses PoW; Ethereum moved to PoS in 2022.

**Proof of Work (PoW)** — a consensus method where participants spend computing power to
earn the right to produce a block.
*In the game:* rewards are shared by hashrate. Miners leave when electricity costs exceed
rewards.
*Real world:* Bitcoin, Litecoin.

**Proof of Stake (PoS)** — a consensus method where participants lock tokens as collateral
for the right to validate blocks.
*In the game:* rewards are shared by stake. Validators leave when rewards fall below costs.
*Real world:* Ethereum, Solana (with additional mechanisms).

**Miner** — a participant that competes to produce blocks under Proof of Work.
*In the game:* ⛏️ agents. They react to reward ÷ cost.
*Real world:* a mining farm with electricity bills.

**Validator** — a participant that helps verify transactions and maintain the network.
*In the game:* ✅ agents. They must stake tokens to participate.
*Real world:* a Solana validator node.

**Staking** — locking tokens to support a network in exchange for rewards.
*In the game:* a validator's `stake` field. More stake ⇒ more reward share.
*Real world:* ETH staking, SOL delegation.

**Block time** — the average time between two blocks being created.
*In the game:* a parameter. With a 600 s block time there are 144 blocks per simulated day.
*Real world:* Bitcoin ~10 min; Solana ~0.4 s.

**Transactions per second (TPS)** — how many transactions the network processes each second.
*In the game:* included transactions ÷ 3 600, capped by capacity.
*Real world:* TPS is a *result* of block time × transactions per block, not a separate knob.

**Transaction capacity** — the maximum number of transactions that fit in one block.
*In the game:* the ceiling on demand. Demand above it becomes congestion.
*Real world:* Bitcoin's ~1 MB blocks limit it to a few thousand transactions.

**Congestion** — demand exceeding capacity, so some transactions wait or are dropped.
*In the game:* `demand / capacity`. Congestion raises fees.
*Real world:* a popular NFT mint jamming a chain.

**Transaction fee** — the payment a user makes to have a transaction included.
*In the game:* rises with congestion; high fees push users away.
*Real world:* Solana fees are fractions of a cent; Bitcoin fees have hit $50+.

**Availability** — the fraction of expected block production the network actually achieves.
*In the game:* drops during outages and validator exoduses.
*Real world:* a chain halt, or a client bug that stops block production.

**Participation** — the share of the expected network that is actually active.
*In the game:* active nodes ÷ target nodes. Low participation lowers health and security.
*Real world:* a network where only 30 % of validators are online is fragile.

**Decentralization** — how spread out power is among participants.
*In the game:* `1 − Herfindahl index` over hashrate or stake shares.
*Real world:* one pool controlling 51 % of Bitcoin's hashrate is a centralization risk.

---

## Markets

**Liquidity** — how easily tokens can be bought or sold without moving the price.
*In the game:* a divisor. Thin liquidity means small flows move the index a lot.
*Real world:* a new token with a tiny pool swings 40 % on a $10 000 trade.

**Volatility** — how much the price moves around, regardless of direction.
*In the game:* an exponentially weighted average of the absolute log return.
*Real world:* a "stablecoin" has low volatility; a memecoin does not.

**Sentiment** — the market's collective mood, from panic to euphoria.
*In the game:* 0–100. It pushes the price index and is pushed back by it.
*Real world:* fear and greed indices.

**Adoption** — how many people actually use the network for something.
*In the game:* drives transaction demand. Rises with utility, falls with bad events.
*Real world:* daily active addresses.

**Speculation** — buying an asset for its price movement rather than its usefulness.
*In the game:* traders amplify moves; they do not create utility.
*Real world:* a token with high volume and no users.

**Reflexivity** — when price changes alter the fundamentals that justify the price.
*In the game:* price ↑ → sentiment ↑ → demand ↑ → price ↑.
*Real world:* a bank run, in either direction.

---

## Simulation and computing

**Agent** — one simulated participant with its own balance, role and behaviour rules.
*In the game:* one displayed agent per grid cell (1:1); when population exceeds the grid, the board shows a deterministic snapshot of part of the population while totals remain accurate.
*Real world:* an agent-based model of a market, a city, or an epidemic.

**Agent-based model (ABM)** — a simulation where global behaviour emerges from many
individual decision rules.
*In the game:* the whole simulation.
*Real world:* epidemic models, traffic models, market microstructure research.

**Cellular automaton** — a grid of cells that update from their neighbours' states.
*In the game:* the grid *looks* like one, and neighbour effects exist, but agents also
respond to global prices and events — so this is an ABM on a grid, not a pure CA.
*Real world:* Conway's Game of Life.

**Tick** — one discrete step of the simulation.
*In the game:* 1 tick = 1 simulated day. One year = 365 ticks.
*Real world:* a "block" is the closest analogue, but a tick can contain many blocks.

**Emergence** — complex behaviour that nobody programmed directly.
*In the game:* a miner death spiral that you never wrote as a rule.
*Real world:* traffic jams forming from individually rational driving.

**Deterministic** — same inputs, same outputs, every time.
*In the game:* a seed makes a run reproducible, so a bug can be replayed.
*Real world:* reproducible research, and why seeds matter in machine learning.

**Random seed** — the starting number for a pseudo-random sequence.
*In the game:* shown in Advanced mode. Change it to explore; keep it to compare.
*Real world:* `random.seed(42)` in every tutorial you have ever read.

**Hysteresis** — a system that resists flipping back and forth near a threshold.
*In the game:* an agent must lose money for 3 ticks before leaving, not 1.
*Real world:* a thermostat that waits before switching.

**Model output** — a number produced by our formulas, not measured from reality.
*In the game:* every price, health and sentiment value carries a "model" badge.
*Real world:* a weather forecast is a model output; the thermometer reading is not.

---

## Governance and society

**Governance** — the way decisions about a network's future are made.
*In the game:* a global "decentralization" setting that changes upgrade speed and capture risk.
*Real world:* on-chain votes, core developer consensus, foundation control.

**Upgrade** — a change to the protocol's rules.
*In the game:* developers raise capacity and health over time; a governance crisis can
reverse that.
*Real world:* Ethereum's Merge, Bitcoin's Taproot.

**Attack (abstract)** — an attempt to break the network's rules or trust.
*In the game:* attackers raise the invalid-transaction rate and lower confidence. Modelled
as pressure, never as instructions.
*Real world:* a 51 % attack, a smart-contract exploit, a phishing campaign.

**51 % attack** — when one actor controls most of the block production and can rewrite
recent history.
*In the game:* represented by the concentration measure in the health score.
*Real world:* small PoW chains have suffered these.

---

## Solana and NFTs

**Solana** — a high-throughput blockchain with sub-second block times and very low fees.
*In the game:* the chain used (on Devnet) for optional achievement attestations.
*Real world:* `solana.com`.

**Devnet** — a public Solana test network where tokens have no value.
*In the game:* the only network we ever touch.
*Real world:* the place to break things safely.

**Wallet** — software that holds the keys to an account.
*In the game:* the player pastes a **public** address; we never ask for a private key.
*Real world:* Phantom, Solflare.

**Public key / address** — a shareable identifier for an account. Safe to post.
*In the game:* what the player provides to receive an achievement NFT.
*Real world:* `7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`.

**Private key** — the secret that controls an account. Never share it, ever.
*In the game:* never requested, never stored, never logged.
*Real world:* the 12/24-word seed phrase.

**NFT** — a unique token that proves ownership of a specific asset.
*In the game:* an optional collectible badge for an achievement.
*Real world:* digital art, game items, event tickets.

**Metaplex Core** — a modern Solana NFT standard that stores an asset in a single account.
*In the game:* the planned post-MVP mint target (~0.003 SOL per asset on Devnet).
*Real world:* the recommended standard for new Solana NFT projects.

**Attestation** — a signed statement recorded on-chain, without minting a token.
*In the game:* the MVP's cheap "proof of achievement" — a memo transaction.
*Real world:* timestamping a document's hash.

**Memo** — a small piece of text attached to a Solana transaction.
*In the game:* carries the achievement id and config hash.
*Real world:* a payment reference note.

---

## Learning methods

**Similarity score** — a weighted measure of how close two configurations are.
*In the game:* the Discovery Mode score, 0 to 1, with a per-parameter breakdown.
*Real world:* recommender systems, clustering, fingerprint matching.

**Confidence (in a reference)** — how sure historians are about a historical parameter.
*In the game:* low-confidence parameters count for less in the score.
*Real world:* estimating Bitcoin's early transaction counts is genuinely uncertain.
