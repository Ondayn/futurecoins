"""The single source of truth for educational text.

Four surfaces read from this module: widget tooltips, metric info popovers, the
searchable glossary page, and the "why did this happen?" panel. Writing the
text once is the only way to stop the four surfaces from disagreeing.

Every entry has the same shape:

    term         the technical word, shown first (we explain, we do not rename)
    short        one sentence, for a hover tooltip
    explanation  two or three sentences, plain language
    in_game      what this means inside FutureCoins
    real_world   a concrete example from a real network
    link         optional, always paired with link_label
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    short: str
    explanation: str
    in_game: str
    real_world: str
    category: str
    link: str = ""
    link_label: str = ""


GLOSSARY: tuple[GlossaryEntry, ...] = (
    # -- Foundations --------------------------------------------------------
    GlossaryEntry(
        term="Blockchain",
        short="A shared list of records that many computers keep in agreement.",
        explanation=(
            "A blockchain is an append-only list of blocks. Each block points to the one "
            "before it, so changing an old record would break every later link. Copies are "
            "kept by many participants, which is why no single person can quietly rewrite it."
        ),
        in_game="FutureCoins does not build a real chain. It simulates the *economics* of one: "
        "who produces blocks, what they earn, and what happens when participation falls.",
        real_world="Bitcoin's chain has run continuously since January 2009.",
        category="Foundations",
        link="https://bitcoin.org/bitcoin.pdf",
        link_label="Read the 9-page Bitcoin whitepaper — the original description of a chain.",
    ),
    GlossaryEntry(
        term="Cryptocurrency",
        short="A digital asset whose ownership and issuance are governed by protocol rules.",
        explanation=(
            "A cryptocurrency is not a file you own. It is an entry in a shared ledger, and "
            "the rules for changing that ledger are enforced by software that many people run."
        ),
        in_game="Each run is a currency with rules you choose. The grid shows the people "
        "living under those rules.",
        real_world="Ether, bitcoin and SOL are cryptocurrencies; each has different issuance rules.",
        category="Foundations",
        link="https://ethereum.org/en/what-is-ethereum/",
        link_label="Ethereum's plain-language introduction to cryptocurrencies and smart contracts.",
    ),
    GlossaryEntry(
        term="Protocol",
        short="The set of rules every participant agrees to follow.",
        explanation=(
            "A protocol is code plus social agreement. The code says what is valid; the "
            "community decides which code to run. Changing either one is hard on purpose."
        ),
        in_game="Your configuration *is* the protocol for this run: block time, rewards, "
        "caps, fees, and how many agents exist.",
        real_world="Bitcoin's 21 million cap is a protocol rule; changing it would require "
        "convincing almost everyone to run different software.",
        category="Foundations",
    ),
    GlossaryEntry(
        term="Agent-based model",
        short="A simulation built from many individual decision-makers.",
        explanation=(
            "Instead of writing one equation for the whole economy, you give each agent a "
            "few rules and let aggregate behaviour emerge. Surprises are the point: the "
            "whole can behave very differently from any single agent."
        ),
        in_game="Every emoji on the grid is an agent. The dashboard numbers are the sum of "
        "thousands of small decisions.",
        real_world="Epidemiologists, traffic engineers and central banks all use agent-based "
        "models to study systems where averages hide the interesting behaviour.",
        category="Foundations",
    ),
    GlossaryEntry(
        term="Deterministic simulation",
        short="Same rules plus same random seed gives the same run, every time.",
        explanation=(
            "Randomness in a simulation comes from a seeded generator. If you know the seed, "
            "you can replay the run exactly. This is what makes a result debuggable and an "
            "achievement verifiable."
        ),
        in_game="The seed is shown in the sidebar. Two runs with the same configuration and "
        "seed produce identical histories.",
        real_world="Games use seeded randomness so that a level can be replayed and a bug can "
        "be reproduced.",
        category="Foundations",
    ),
    GlossaryEntry(
        term="Seed",
        short="The number that makes a run reproducible.",
        explanation=(
            "A pseudorandom generator is a deterministic machine: feed it the same seed and "
            "it produces the same sequence. Change the seed and you get a different story "
            "with the same rules."
        ),
        in_game="Every preset has its own seed (Bitcoin 2009 uses 2009). Change it to explore "
        "how much of an outcome was luck versus structure.",
        real_world="Minecraft world generation is driven by a seed; the same seed rebuilds the "
        "same terrain.",
        category="Foundations",
    ),
    # -- Consensus ----------------------------------------------------------
    GlossaryEntry(
        term="Consensus mechanism",
        short="How a network agrees on the next block without a central authority.",
        explanation=(
            "Someone has to decide which transactions are in the next block. Proof of Work "
            "and Proof of Stake are two ways to make that decision expensive to corrupt and "
            "cheap to verify."
        ),
        in_game="Choose PoW or PoS. It changes who produces blocks, what resource they spend, "
        "and how the network reacts to shocks.",
        real_world="Bitcoin uses Proof of Work; Ethereum and Solana use Proof of Stake.",
        category="Consensus",
        link="https://ethereum.org/en/developers/docs/consensus-mechanisms/",
        link_label="Compare PoW and PoS side by side in Ethereum's documentation.",
    ),
    GlossaryEntry(
        term="Proof of Work (PoW)",
        short="Producers spend computing power to earn the right to make a block.",
        explanation=(
            "Miners repeatedly hash a candidate block until they find a rare result. The work "
            "is wasted if they lie, which is what makes attacking the chain expensive. Rewards "
            "pay for the hardware and electricity."
        ),
        in_game="Miners earn a share of block rewards proportional to their hashrate. They "
        "leave when rewards stop covering their operating cost.",
        real_world="Bitcoin's miners collectively perform more hashing than the world's top "
        "supercomputers, by an enormous margin.",
        category="Consensus",
        link="https://ethereum.org/en/developers/docs/consensus-mechanisms/pow/",
        link_label="How Proof of Work turns electricity into security.",
    ),
    GlossaryEntry(
        term="Proof of Stake (PoS)",
        short="Producers lock tokens as collateral instead of spending electricity.",
        explanation=(
            "Validators put capital at risk. If they behave badly, they can lose part of it. "
            "The cost of attacking the network is therefore the cost of acquiring stake, not "
            "the cost of buying hardware."
        ),
        in_game="Validators earn a share of rewards proportional to their stake. If too little "
        "stake is online, block production slows down.",
        real_world="Ethereum moved to Proof of Stake in 2022, cutting its energy use by roughly "
        "99.95 %.",
        category="Consensus",
        link="https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/",
        link_label="Ethereum's explanation of staking, validators and slashing.",
    ),
    GlossaryEntry(
        term="Miner",
        short="A PoW participant that spends computing power to produce blocks.",
        explanation=(
            "A miner's income is probabilistic in reality and proportional to hashrate on "
            "average. Costs are continuous: electricity is paid whether or not a block is found."
        ),
        in_game="Each miner has a hashrate and a cost per tick. Unprofitable miners go offline "
        "after a few bad ticks, then return when rewards recover.",
        real_world="During price crashes, miners switch off older machines first — exactly the "
        "weakest-first exit this simulation models.",
        category="Consensus",
    ),
    GlossaryEntry(
        term="Validator",
        short="A PoS participant that stakes tokens to produce blocks.",
        explanation=(
            "Validators are chosen to propose and attest to blocks in proportion to their "
            "stake. Their capital is locked, and misbehaviour can be punished by slashing."
        ),
        in_game="Validators exist only under PoS. Their stake sets their share of rewards and "
        "the network's security margin.",
        real_world="Ethereum requires 32 ETH per validator; Solana validators compete on stake "
        "delegated by token holders.",
        category="Consensus",
    ),
    GlossaryEntry(
        term="Hashrate",
        short="How many hash attempts a miner can make per second.",
        explanation=(
            "Hashrate is a rate of guessing. More guesses mean a higher chance of finding the "
            "next block, which is why reward share follows hashrate share."
        ),
        in_game="A miner's capacity is its hashrate. Total hashrate sets each miner's share of "
        "the tick's rewards.",
        real_world="Bitcoin's network hashrate is measured in exahashes per second (EH/s).",
        category="Consensus",
    ),
    GlossaryEntry(
        term="Stake",
        short="Tokens locked as collateral by a validator.",
        explanation=(
            "Stake is a bond. It makes a validator's promise credible: if they break the rules, "
            "they lose money. The larger the total stake, the more capital an attacker needs."
        ),
        in_game="Validator stake sets reward share and the availability factor. Low total stake "
        "means slow, fragile block production.",
        real_world="A Proof-of-Stake chain with a small staked supply is cheap to attack, even "
        "if its token price is high.",
        category="Consensus",
    ),
    GlossaryEntry(
        term="Availability",
        short="The fraction of target block production the network can actually achieve.",
        explanation=(
            "If half the expected producers are offline, blocks arrive about half as often. "
            "In this simulation, availability multiplies blocks per tick."
        ),
        in_game="PoS availability falls when total stake is below the target fraction. Events "
        "that force producers offline also lower it.",
        real_world="A chain that loses a large share of its validators can stall or finalise "
        "blocks much more slowly.",
        category="Consensus",
    ),
    GlossaryEntry(
        term="Concentration (Herfindahl index)",
        short="A number that rises when production is controlled by fewer participants.",
        explanation=(
            "The Herfindahl index is the sum of squared market shares. One producer with 100 % "
            "gives 1.0; a thousand equal producers give 0.001. Squaring punishes dominance."
        ),
        in_game="The health score uses 1 - concentration as its decentralization component.",
        real_world="Regulators use the same index to measure market concentration in banking "
        "and telecoms.",
        category="Consensus",
    ),
    GlossaryEntry(
        term="51 % attack",
        short="Control of a majority of production capacity lets an attacker rewrite recent history.",
        explanation=(
            "If one actor controls more than half of hashrate or stake, they can exclude "
            "transactions and reverse recent blocks. They cannot steal coins from arbitrary "
            "addresses, but they can double-spend their own."
        ),
        in_game="Attackers never perform a real attack here. They raise the invalid-transaction "
        "rate and drain confidence — an abstraction, clearly labelled.",
        real_world="Small Proof-of-Work chains have suffered 51 % attacks; the cost of renting "
        "hashpower was lower than the profit from double-spending.",
        category="Consensus",
    ),
    GlossaryEntry(
        term="Sybil attack",
        short="Creating many fake identities to gain influence.",
        explanation=(
            "One person pretending to be a thousand is cheap unless identity costs something. "
            "PoW makes each identity cost hardware; PoS makes each identity cost stake."
        ),
        in_game="The number of agents is not a security measure. What matters is the resource "
        "they control.",
        real_world="Airdrop farmers create thousands of wallets for exactly this reason.",
        category="Consensus",
    ),
    # -- Money --------------------------------------------------------------
    GlossaryEntry(
        term="Block",
        short="A batch of transactions plus a reward for the producer.",
        explanation=(
            "A block is the unit of commitment. It contains transactions, a reference to the "
            "previous block, and usually a payment to whoever produced it."
        ),
        in_game="Blocks per tick = 86400 / block time. A 600-second block time gives 144 blocks "
        "per simulated day.",
        real_world="Bitcoin blocks are limited to about 1 MB of data in the original rules.",
        category="Money",
        link="https://en.bitcoin.it/wiki/Block",
        link_label="The anatomy of a Bitcoin block, field by field.",
    ),
    GlossaryEntry(
        term="Block time",
        short="The target number of seconds between blocks.",
        explanation=(
            "Block time is a protocol target, not a guarantee. If producers go offline, actual "
            "blocks arrive more slowly. Short block times feel fast but demand more bandwidth."
        ),
        in_game="Set the target block time. The dashboard shows the *actual* interval, which "
        "rises when availability falls.",
        real_world="Bitcoin targets 10 minutes; Ethereum targets 12 seconds; Solana targets "
        "about 400 milliseconds.",
        category="Money",
    ),
    GlossaryEntry(
        term="Block reward",
        short="New tokens paid to the producer of a block.",
        explanation=(
            "The block reward is how new supply enters the system. It is also the incentive "
            "that pays for security. If it is too low, producers leave; if it is too high, "
            "holders are diluted quickly."
        ),
        in_game="Initial block reward is a slider. Rewards are split by hashrate or stake share.",
        real_world="Bitcoin started at 50 BTC per block and halves every 210,000 blocks.",
        category="Money",
    ),
    GlossaryEntry(
        term="Halving",
        short="A scheduled cut of the block reward, usually by half.",
        explanation=(
            "A halving reduces new issuance on a fixed schedule. It is predictable, which is "
            "the point: nobody has to trust a committee to decide when inflation falls."
        ),
        in_game="The reward halves every N blocks, counted in blocks rather than ticks so the "
        "schedule is a property of the currency, not of our clock.",
        real_world="Bitcoin halvings occurred in 2012, 2016, 2020 and 2024.",
        category="Money",
        link="https://en.bitcoin.it/wiki/Controlled_supply",
        link_label="The exact Bitcoin issuance schedule, including the geometric series.",
    ),
    GlossaryEntry(
        term="Supply cap",
        short="A maximum number of tokens that can ever exist.",
        explanation=(
            "A cap can be written directly into the rules, or it can emerge from a halving "
            "schedule. Those are different designs: one is a constant, the other is a "
            "consequence."
        ),
        in_game="Bitcoin 2009 has no cap parameter. Its 21 million limit is the sum of the "
        "halving series. This is the central teaching moment of Discovery Mode.",
        real_world="Bitcoin's cap is emergent: 210,000 × 50 × 2 = 21,000,000.",
        category="Money",
    ),
    GlossaryEntry(
        term="Initial supply",
        short="Tokens that exist at the moment the network launches.",
        explanation=(
            "An initial supply is a premine: someone already owns coins before any work is "
            "done. It can fund development, but it also concentrates ownership."
        ),
        in_game="Bitcoin 2009 starts at zero. Every coin in that run is created by a block "
        "reward, which is why early fees are tiny and early balances are empty.",
        real_world="Bitcoin had no premine; many later projects allocated a share to founders "
        "or a foundation.",
        category="Money",
    ),
    GlossaryEntry(
        term="Premine",
        short="Tokens allocated to insiders before the public can earn any.",
        explanation=(
            "A premine is not automatically bad, but it is a transfer of future value to "
            "whoever receives it. The size and the vesting schedule are what matter."
        ),
        in_game="Initial supply plus treasury fraction are this run's premine.",
        real_world="Some projects premine 10–50 % for a foundation; others start at zero.",
        category="Money",
    ),
    GlossaryEntry(
        term="Total supply",
        short="Everything ever minted, minus everything destroyed.",
        explanation=(
            "Total supply = initial supply + all issuance - all burns. It includes tokens held "
            "by the protocol treasury and tokens that are staked."
        ),
        in_game="The dashboard shows total and circulating supply side by side, because the "
        "difference is easy to miss.",
        real_world="Bitcoin's total supply approaches 21 million; Ethereum's changes with "
        "issuance and burns.",
        category="Money",
    ),
    GlossaryEntry(
        term="Circulating supply",
        short="Tokens that are not held by the protocol itself.",
        explanation=(
            "Circulating supply excludes the treasury but includes staked tokens: staking "
            "locks tokens, it does not destroy them. Definitions differ between projects, "
            "which is why the label must be explicit."
        ),
        in_game="Circulating = total supply - protocol treasury.",
        real_world="CoinMarketCap and projects often disagree on circulating supply, which "
        "changes market-cap figures.",
        category="Money",
    ),
    GlossaryEntry(
        term="Treasury",
        short="Tokens controlled by the protocol or its governing body.",
        explanation=(
            "A treasury pays for development, grants and audits. It is a form of centralized "
            "control unless spending is governed transparently."
        ),
        in_game="The treasury fraction is taken from the initial supply and never spends in "
        "this MVP.",
        real_world="Many DAOs hold billions in treasury tokens and argue endlessly about how "
        "to spend them.",
        category="Money",
    ),
    GlossaryEntry(
        term="Inflation rate",
        short="New tokens as a percentage of existing supply, per year.",
        explanation=(
            "Inflation dilutes holders unless they receive a share of the new tokens. A high "
            "rate can pay for security, but it transfers value from savers to producers."
        ),
        in_game="Annualised from this tick's issuance: issuance × 365 / total supply.",
        real_world="Bitcoin's inflation rate falls below 1 % after several halvings; some "
        "Proof-of-Stake chains target 5–10 %.",
        category="Money",
    ),
    GlossaryEntry(
        term="Burn",
        short="Tokens destroyed permanently, reducing total supply.",
        explanation=(
            "A burn sends tokens to an address nobody can spend from. It is deflationary: the "
            "remaining tokens represent a larger share of the network."
        ),
        in_game="Burn rate is the share of transaction fees destroyed instead of paid to "
        "producers. Bitcoin burns nothing; some PoS chains burn a lot.",
        real_world="Ethereum's EIP-1559 burns a base fee with every transaction.",
        category="Money",
    ),
    GlossaryEntry(
        term="Fee",
        short="A payment to have a transaction included in a block.",
        explanation=(
            "Fees ration scarce blockspace. When demand exceeds capacity, the fee rises until "
            "enough users decide the transaction is not worth it."
        ),
        in_game="Fees are capped by what users can actually pay. A network with no coins in "
        "circulation collects almost nothing — historically accurate for early Bitcoin.",
        real_world="Bitcoin fees spike during bull markets; Ethereum's gas price is visible "
        "before you sign.",
        category="Money",
        link="https://ethereum.org/en/developers/docs/gas/",
        link_label="How gas and base fees price Ethereum blockspace.",
    ),
    # -- Network ------------------------------------------------------------
    GlossaryEntry(
        term="Mempool",
        short="The queue of transactions waiting to be included.",
        explanation=(
            "The mempool is not a single place; it is every node's local set of unconfirmed "
            "transactions. Miners pick the highest-fee ones first."
        ),
        in_game="Each tick, demand enters the mempool, gets priced, and either fits in a block "
        "or is dropped.",
        real_world="Mempool.space shows Bitcoin's queue and the fee needed to jump it.",
        category="Network",
    ),
    GlossaryEntry(
        term="Congestion",
        short="Demand for blockspace exceeding the supply of blockspace.",
        explanation=(
            "Congestion is a ratio, not a feeling. When demand is twice capacity, half the "
            "transactions cannot fit, and the fee mechanism decides who stays."
        ),
        in_game="Congestion = demand / capacity. It raises fees and can trigger the Network "
        "Congestion event.",
        real_world="NFT mints and airdrops have congested Ethereum for hours.",
        category="Network",
    ),
    GlossaryEntry(
        term="Throughput (TPS)",
        short="Transactions included per second.",
        explanation=(
            "TPS is capacity multiplied by block frequency, not block frequency alone. A chain "
            "with slow blocks and large blocks can beat one with fast, tiny blocks."
        ),
        in_game="TPS = included transactions per tick / 3,600.",
        real_world="Visa handles thousands of TPS; Bitcoin handles a handful; Solana advertises "
        "tens of thousands under ideal conditions.",
        category="Network",
    ),
    GlossaryEntry(
        term="Reliability",
        short="The share of attempted transactions that actually get included.",
        explanation=(
            "A fast network that drops half your transactions is not fast. Reliability is the "
            "ratio of included to attempted, after fees and capacity are applied."
        ),
        in_game="Low reliability pushes users' confidence down, and churning users reduce "
        "demand — a negative feedback loop.",
        real_world="Users abandon chains that fail transactions repeatedly, even if the "
        "theoretical TPS is high.",
        category="Network",
    ),
    GlossaryEntry(
        term="Network health",
        short="A weighted 0–100 score combining five signals.",
        explanation=(
            "An undefined health score is a vibe. This one is explicit: participation 30 %, "
            "decentralization 20 %, reliability 25 %, security 15 %, sentiment 10 %."
        ),
        in_game="Every weight is visible in the dashboard's breakdown, so you can argue with "
        "the formula instead of guessing.",
        real_world="No standard health score exists; dashboards invent their own and rarely "
        "show the weights.",
        category="Network",
    ),
    GlossaryEntry(
        term="Participation",
        short="The share of agents currently active.",
        explanation=(
            "Registered users are not the same as active users. The gap between the two is "
            "often the most interesting number in a network."
        ),
        in_game="Active nodes / total nodes, shown as two numbers in one card.",
        real_world="A blockchain with a million addresses may have only a few thousand daily "
        "active wallets.",
        category="Network",
    ),
    GlossaryEntry(
        term="Security margin",
        short="A crude proxy for how expensive it would be to capture the network.",
        explanation=(
            "The margin rises with active producers under PoW and with staked supply under "
            "PoS. It is a teaching proxy, not an audit."
        ),
        in_game="Security is 15 % of the health score. Attackers reduce confidence, not the "
        "margin directly.",
        real_world="Security is usually estimated from the cost of renting enough hashpower or "
        "acquiring enough stake.",
        category="Network",
    ),
    GlossaryEntry(
        term="Hysteresis",
        short="A system that remembers its recent past instead of reacting instantly.",
        explanation=(
            "Without hysteresis, agents flip on and off every tick and the screen strobes. A "
            "few ticks of patience make behaviour readable and realistic."
        ),
        in_game="Producers need three bad ticks to leave and five good ticks to return. Users "
        "behave the same way.",
        real_world="Miners do not unplug a rig because one block was unlucky; they wait to see "
        "whether the trend is real.",
        category="Behaviour",
    ),
    # -- Market -------------------------------------------------------------
    GlossaryEntry(
        term="Liquidity",
        short="How much buying or selling it takes to move the price.",
        explanation=(
            "A deep market absorbs large orders with little price change. A thin market moves "
            "violently on small flows. Liquidity is a property of the market, not the coin."
        ),
        in_game="Liquidity is a configuration parameter; it damps or amplifies the price index.",
        real_world="A small-cap token can lose 30 % on a single large sell order.",
        category="Market",
    ),
    GlossaryEntry(
        term="Price index",
        short="A simulated price level, starting at 100.",
        explanation=(
            "This is a formula output, not a market price. It starts at 100 so that changes "
            "are easy to read as percentages. The UI labels it 'model output' everywhere."
        ),
        in_game="The index moves with net demand, sentiment, inflation pressure and noise, "
            "clamped to [1, 100,000].",
        real_world="A real price is whatever a buyer and seller agree on at a moment in time.",
        category="Market",
    ),
    GlossaryEntry(
        term="Volatility",
        short="How large recent price moves have been.",
        explanation=(
            "Volatility is an exponentially weighted average of absolute log returns. It "
            "measures movement, not direction: a crash and a rally both raise it."
        ),
        in_game="High volatility makes the market feel unstable but does not directly change "
        "the health score.",
        real_world="Bitcoin's annualised volatility is typically several times that of major "
        "stock indices.",
        category="Market",
    ),
    GlossaryEntry(
        term="Sentiment",
        short="The market's mood, on a scale from 0 to 1.",
        explanation=(
            "Sentiment is a social signal. It responds to health, media coverage and recent "
            "events, and it feeds back into demand and price."
        ),
        in_game="Sentiment chases a target set by network health plus event shocks; adaptivity "
        "controls how fast it catches up.",
        real_world="Fear and Greed indices aggregate social media, volatility and survey data.",
        category="Market",
    ),
    GlossaryEntry(
        term="Reflexivity",
        short="When the market's reaction changes the thing it is reacting to.",
        explanation=(
            "A price fall scares holders, who sell, which pushes the price down further. The "
            "loop is real but damped: eventually sellers run out or buyers see value."
        ),
        in_game="A market crash lowers sentiment, which lowers demand and raises sell pressure, "
        "which lowers the price index again.",
        real_world="Bank runs and crypto liquidation cascades are reflexive loops.",
        category="Market",
    ),
    GlossaryEntry(
        term="Adoption",
        short="How many people use the network, relative to a baseline.",
        explanation=(
            "Adoption is a multiplier on demand. It grows when the network is useful and "
            "reliable, and shrinks when it is expensive or disappointing."
        ),
        in_game="Adoption follows utilisation and sentiment, with a slow adaptivity so it "
        "cannot jump overnight.",
        real_world="Metcalfe's law argues a network's value grows with the square of its users.",
        category="Market",
    ),
    GlossaryEntry(
        term="Trader pressure",
        short="Extra buying or selling from momentum traders.",
        explanation=(
            "Traders do not create tokens. They move the price by changing how much others "
            "want to hold at the current level."
        ),
        in_game="Traders amplify the previous tick's move. More traders and higher "
        "aggressiveness mean noisier prices.",
        real_world="Momentum strategies amplify both rallies and crashes.",
        category="Market",
    ),
    GlossaryEntry(
        term="Model output",
        short="A number produced by this simulation's formulas, not measured from reality.",
        explanation=(
            "Labelling matters. A simulated price index is not a forecast, and a health score "
            "is not an audit. The badge is there to stop a player from mistaking one for the "
            "other."
        ),
        in_game="Price, volatility, sentiment, health and security carry the 'model' badge.",
        real_world="Even real dashboards mix measured data with estimates; the honest ones say "
        "which is which.",
        category="Meta",
    ),
    GlossaryEntry(
        term="Cohort",
        short="Several agents represented by one grid cell.",
        explanation=(
            "When the population is larger than the grid, each cell stands for a group. The "
            "cell shows the dominant role and its opacity shows how many are active."
        ),
        in_game="Population is always printed separately from cell count, so 800 cells never "
        "gets mistaken for 800 agents.",
        real_world="Maps use the same trick: one dot can represent a city or a million people.",
        category="Meta",
    ),
    GlossaryEntry(
        term="Tokenomics",
        short="The rules that decide who gets tokens, when, and how many.",
        explanation=(
            "Tokenomics is supply, issuance, allocation and incentives taken together. Two "
            "coins with the same technology can behave completely differently because their "
            "tokenomics differ."
        ),
        in_game="Every slider in the monetary section is a tokenomics decision.",
        real_world="A vesting schedule that unlocks 20 % of supply in one month can crash a "
        "price without any change in technology.",
        category="Money",
    ),
    GlossaryEntry(
        term="Governance",
        short="Who gets to change the rules, and how.",
        explanation=(
            "Governance can be on-chain voting, a foundation, a small team, or a rough "
            "consensus. The more centralized it is, the faster changes happen and the more "
            "trust they require."
        ),
        in_game="Decentralization is a global force: it feeds the health score and softens "
        "event severity.",
        real_world="Bitcoin changes very slowly by rough consensus; some DAOs vote weekly.",
        category="Meta",
    ),
    GlossaryEntry(
        term="Institutions",
        short="Large organizations that participate in a market.",
        explanation=(
            "Institutions add liquidity and legitimacy, but they also concentrate influence. "
            "Their participation is a trade-off, not a pure win."
        ),
        in_game="Institutional participation is a global force that adds market depth.",
        real_world="Spot Bitcoin ETFs changed who holds bitcoin and how it trades.",
        category="Meta",
    ),
    GlossaryEntry(
        term="Media",
        short="The narrative layer that shapes public confidence.",
        explanation=(
            "Coverage does not change the protocol, but it changes who trusts it. Narrative is "
            "an economic force because demand depends on belief."
        ),
        in_game="Media bias shifts the sentiment target; negative coverage is a random event.",
        real_world="A single critical article can move a small token's price more than a "
        "protocol upgrade.",
        category="Meta",
    ),
)


# Fast lookup by lower-case term.
BY_TERM: dict[str, GlossaryEntry] = {entry.term.lower(): entry for entry in GLOSSARY}


def get(term: str) -> GlossaryEntry | None:
    """Look up one term, case-insensitively."""
    return BY_TERM.get(term.strip().lower())


def short(term: str) -> str:
    """One-sentence tooltip text, safe to pass to a Streamlit ``help=``."""
    entry = get(term)
    return entry.short if entry else ""


def categories() -> list[str]:
    """Every category, in a stable, readable order."""
    preferred = [
        "Foundations",
        "Consensus",
        "Money",
        "Network",
        "Market",
        "Behaviour",
        "Meta",
    ]
    present = {entry.category for entry in GLOSSARY}
    ordered = [c for c in preferred if c in present]
    ordered.extend(sorted(present - set(ordered)))
    return ordered


def search(query: str = "", category: str | None = None) -> list[GlossaryEntry]:
    """Filter the glossary by free text and/or category.

    Matches the term, the short sentence and the explanation. A player who
    remembers "the thing about fees" should find the fee entry.
    """
    needle = query.strip().lower()
    results: list[GlossaryEntry] = []
    for entry in GLOSSARY:
        if category and entry.category != category:
            continue
        if needle:
            haystack = (
                f"{entry.term} {entry.short} {entry.explanation} "
                f"{entry.in_game} {entry.real_world}"
            ).lower()
            if needle not in haystack:
                continue
        results.append(entry)
    return results


__all__ = ["BY_TERM", "GLOSSARY", "GlossaryEntry", "categories", "get", "search", "short"]
