"""Curated external resources, mapped to moments in the game.

Rule from the GDD: no link is presented without saying what the player will
learn from it. A bare URL is homework; a labelled link is a next step.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    title: str
    url: str
    topic: str
    what_you_learn: str
    level: str = "beginner"


RESOURCES: tuple[Resource, ...] = (
    Resource(
        title="Bitcoin: A Peer-to-Peer Electronic Cash System",
        url="https://bitcoin.org/bitcoin.pdf",
        topic="Foundations",
        what_you_learn="The original 9-page design: blocks, proof of work, and why double-spending is hard.",
        level="beginner",
    ),
    Resource(
        title="Ethereum — What is Ethereum?",
        url="https://ethereum.org/en/what-is-ethereum/",
        topic="Foundations",
        what_you_learn="How a blockchain can run programs, and what 'ether' is for.",
        level="beginner",
    ),
    Resource(
        title="Ethereum — Proof of Stake",
        url="https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/",
        topic="Consensus",
        what_you_learn="Validators, staking, slashing, and why Ethereum switched away from mining.",
        level="intermediate",
    ),
    Resource(
        title="Ethereum — Proof of Work",
        url="https://ethereum.org/en/developers/docs/consensus-mechanisms/pow/",
        topic="Consensus",
        what_you_learn="How hashing turns electricity into security, and what mining actually computes.",
        level="intermediate",
    ),
    Resource(
        title="Bitcoin Wiki — Controlled Supply",
        url="https://en.bitcoin.it/wiki/Controlled_supply",
        topic="Money",
        what_you_learn="The exact halving schedule, and why the 21 million cap is a sum rather than a constant.",
        level="beginner",
    ),
    Resource(
        title="Bitcoin Wiki — Transaction Fees",
        url="https://en.bitcoin.it/wiki/Transaction_fees",
        topic="Network",
        what_you_learn="Why fees exist, how they are estimated, and what happens when blocks are full.",
        level="intermediate",
    ),
    Resource(
        title="Ethereum — Gas and Fees",
        url="https://ethereum.org/en/developers/docs/gas/",
        topic="Network",
        what_you_learn="How blockspace is priced, and what the base fee actually does.",
        level="intermediate",
    ),
    Resource(
        title="Solana — Documentation",
        url="https://solana.com/docs",
        topic="Foundations",
        what_you_learn="A different design: proof of history, parallel execution, and very short block times.",
        level="intermediate",
    ),
    Resource(
        title="Metaplex Core",
        url="https://developers.metaplex.com/core",
        topic="Build",
        what_you_learn="The current standard for NFTs on Solana, and why it is cheaper than the old Token Metadata program.",
        level="advanced",
    ),
    Resource(
        title="Streamlit — st.fragment",
        url="https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment",
        topic="Build",
        what_you_learn="How this app animates one part of the page without rerunning the whole script.",
        level="intermediate",
    ),
    Resource(
        title="Major League Hacking",
        url="https://mlh.io",
        topic="Community",
        what_you_learn="Hackathon rules, the Code of Conduct, and the events you can join next.",
        level="beginner",
    ),
    Resource(
        title="DEV Community",
        url="https://dev.to",
        topic="Community",
        what_you_learn="Where developers write up what they built and what broke along the way.",
        level="beginner",
    ),
)


def by_topic(topic: str | None = None) -> list[Resource]:
    """Resources for one topic, or all of them."""
    if topic is None:
        return list(RESOURCES)
    return [resource for resource in RESOURCES if resource.topic == topic]


def topics() -> list[str]:
    """Stable topic order."""
    preferred = ["Foundations", "Consensus", "Money", "Network", "Build", "Community"]
    present = {resource.topic for resource in RESOURCES}
    ordered = [topic for topic in preferred if topic in present]
    ordered.extend(sorted(present - set(ordered)))
    return ordered


__all__ = ["RESOURCES", "Resource", "by_topic", "topics"]
