"""Lane B: fact flattening and the grounding rules of ghosts.verify (offline)."""
import json
from pathlib import Path

import pytest

from ghosts.verify import FactIndex, check_sentence, flatten, split_sentences, dates_in_text

FIX = Path(__file__).parent / "fixtures" / "b"
SB = "0x2af47a65da8cd66729b4209c22017d6a5c2d2400"
KOTE = "0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0"


def load(a):
    return json.loads((FIX / a / "facts.json").read_text())


@pytest.fixture(scope="module")
def sb():
    return FactIndex.build(facts=load(SB), derived={"age_years": 10.9, "age_years_whole": 10})


@pytest.fixture(scope="module")
def kote():
    return FactIndex.build(facts=load(KOTE), derived={"silent_years": 10.7})


def ok(ix, s):
    return check_sentence(s, ix).ok


def test_flatten_paths_and_skips_empty():
    leaves = dict(flatten({"a": {"b": [1, {"c": "x"}], "d": None, "e": ""}}, "facts"))
    assert leaves == {"facts.a.b[0]": 1, "facts.a.b[1].c": "x"}


def test_index_collects_numbers_dates_and_text(sb):
    nums = {v for v, _ in sb.numbers}
    assert 19461 in nums and 83.001304 in nums and 2017 in nums
    assert (2017, 12, 18) in sb.dates            # birth timestamp
    assert (2017, 9, 23) in sb.dates             # Wayback 14-digit first_capture
    assert 12 in sb.months
    assert "bounties.network" in sb.text


def test_rounding_to_shown_precision(sb):
    assert ok(sb, "It still holds 83.0 ETH.")
    assert ok(sb, "It still holds about 83 ETH.")
    assert ok(sb, "It still holds 83.001 ETH.")
    assert not ok(sb, "It still holds 84 ETH.")
    assert not ok(sb, "It still holds 83.1 ETH.")


def test_eth_amounts_checked_even_single_digit(sb):
    assert not ok(sb, "Someone sent it 5 ETH.")


def test_significant_digits_and_scale_words(sb):
    assert ok(sb, "It answered 19,461 transactions.")
    assert ok(sb, "It answered nearly 19,000 transactions.")   # two significant digits shown
    assert not ok(sb, "It answered 20,000 transactions.")      # one significant digit: exact only
    assert ok(sb, "It burned about 2.4 billion units of gas.")
    assert not ok(sb, "It burned about 3.4 billion units of gas.")


def test_floor_of_whole_numbers(sb):
    assert ok(sb, "It has been waiting for 10 years.")      # 10.9 -> 10 (floor)
    assert ok(sb, "It has been waiting for 11 years.")      # 10.9 -> 11 (round)
    assert not ok(sb, "It has been waiting for 12 years.")


def test_number_words(sb):
    assert ok(sb, "It has waited ten years.")
    assert not ok(sb, "It has waited twenty-one years.")
    assert ok(sb, "One small program, two old websites.")   # single digits are free


def test_years_exact(sb):
    assert ok(sb, "It was born in 2017.")
    assert not ok(sb, "It was born in 2013.")


def test_dates_and_months(kote):
    assert ok(kote, "It was born on February 6, 2016.")
    assert ok(kote, "It was born on 6 February 2016.")
    assert ok(kote, "It was born in February 2016.")
    assert ok(kote, "It went quiet on Feb 19, 2016.")
    assert not ok(kote, "It went quiet on February 20, 2016.")
    assert not ok(kote, "It went quiet in July 2016.")
    assert ok(kote, "It went quiet in February.")
    assert not ok(kote, "It went quiet in November.")


def test_month_names_from_free_text():
    full, ym, months = dates_in_text("deployed on February 6, 2016 during the 'Turbulent Age' (Feb 6–8, 2016)")
    assert (2016, 2, 6) in full and (2016, 2, 8) in full and 2 in months


def test_names(kote):
    assert ok(kote, "Kieran Elby deployed it.")
    assert ok(kote, "Then Kieran Elby deployed it.")
    assert ok(kote, "The King of the Ether Throne waited.")
    assert not ok(kote, "Vitalik Buterin deployed it.")
    assert not ok(kote, "It was loved by The DAO.")            # acronym after a starter word
    assert ok(kote, "Because I was broken, I waited.")         # pronoun is not a name
    assert ok(kote, "On the Day of the Dead, we remember it.")  # storyteller frame is allowed


def test_quotes_identifiers_hex_versions(kote):
    assert ok(kote, "It lived through the 'Turbulent Age' of the throne.")
    assert not ok(kote, "It lived through the 'Golden Age' of the throne.")
    assert ok(kote, "Its last breath was a call to sweepCommission.")
    assert not ok(kote, "Its last breath was a call to withdrawAll.")
    assert ok(kote, "It lives at 0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0.")
    assert not ok(kote, "It lives at 0xdeadbeef00.")
    assert ok(kote, "This was version v0.4.0 of the throne.")
    assert not ok(kote, "This was version v0.9.1 of the throne.")


def test_cited_paths_prefer_exact_leaves(sb):
    c = check_sentence("It answered 19,461 transactions and holds 83.0 ETH.", sb)
    assert "facts.life.tx_count" in c.cited and "facts.life.balance_eth" in c.cited


def test_split_sentences():
    assert split_sentences('It was born on Feb. 6, 2016. It died. "Why?" he asked. Then v0.4.0 rose.') == [
        "It was born on Feb. 6, 2016.", "It died.", '"Why?" he asked.', "Then v0.4.0 rose."]


def test_sentence_initial_word_is_not_part_of_the_name(kote):
    assert ok(kote, "During the Turbulent Age, it lost ether.")
    assert not ok(kote, "During the Golden Age, it lost ether.")


def test_short_scale_suffix_and_known_single_names():
    ix = FactIndex.build(facts={"note": "Atzei et al. say about $60M came under control.", "language": "Solidity"})
    assert ok(ix, "Others say $60 million fell under the attacker's control.")
    assert not ok(ix, "Others say $70 million fell under the attacker's control.")
    assert ok(ix, "Modern Solidity heals this wound.")
    assert not ok(ix, "Vitalik Buterin heals this wound.")


def test_short_hex_forms(kote):
    assert ok(kote, "The wallet 0xb2af…8de3 brought it into the world.")
    assert ok(kote, "The wallet 0xb2afec...28de3 brought it into the world.")
    assert not ok(kote, "The wallet 0xb2af…9999 brought it into the world.")
    assert not ok(kote, "The wallet 0xdead…8de3 brought it into the world.")


def test_address_ends_as_numbers(sb):
    assert ok(sb, "A wallet ending in 7645 brought it into the world.")
    assert not ok(sb, "A wallet ending in 7646 brought it into the world.")


def test_parentheses_split_names_and_hex_tails_are_not_numbers():
    ix = FactIndex.build(facts={"incident": {"name": "Multichain (Anyswap)"}, "deployer": "0x1111111111111111111111111111111111d324c5"})
    assert ok(ix, "My address sits in the record of the Multichain (Anyswap) incident.")
    # a lone capitalized word ("Sushiswap") is not checked: the documented single-word limit
    assert ok(ix, "A wallet ending in 24c5 brought it into the world.")
