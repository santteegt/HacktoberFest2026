"""Ethereum mainnet ages by block number, so every ghost gets an era even when the archive has none."""
HARDFORKS = [  # (first block, name)
    (0, "Frontier"), (200_000, "Frontier Thawing"), (1_150_000, "Homestead"), (1_920_000, "DAO Fork"),
    (2_463_000, "Tangerine Whistle"), (2_675_000, "Spurious Dragon"), (4_370_000, "Byzantium"),
    (7_280_000, "Constantinople"), (9_069_000, "Istanbul"), (9_200_000, "Muir Glacier"),
    (12_244_000, "Berlin"), (12_965_000, "London"), (13_773_000, "Arrow Glacier"), (15_050_000, "Gray Glacier"),
    (15_537_394, "Paris (the Merge)"), (17_034_870, "Shanghai"), (19_426_587, "Cancun"), (22_431_084, "Prague"),
]


def age_of(block_number: int) -> str:
    name = HARDFORKS[0][1]
    for start, n in HARDFORKS:
        if block_number >= start:
            name = n
    return name
