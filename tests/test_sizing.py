"""Phase 2 tests: the bottom-up sizing math and its input checks.

Every expected number can be checked by hand:

            customers  price  buys/yr   TAM         sam_share  SAM         som_share  SOM
    low     10,000     $40    1         $400,000    0.20       $80,000     0.05       $4,000
    base    20,000     $50    2         $2,000,000  0.25       $500,000    0.10       $50,000
    high    40,000     $60    3         $7,200,000  0.50       $3,600,000  0.20       $720,000

TAM = customers x price x purchases_per_year, SAM = TAM x sam_share, SOM = SAM x som_share.
"""

import copy

import pytest

from copilot.sizing import (
    SizingError,
    load_assumptions,
    mark_unverified_as_assumptions,
    size_market,
)


def sample_data():
    """A fresh copy of the hand-checkable assumptions in the table above."""
    return {
        "customers": {
            "low": 10000, "base": 20000, "high": 40000,
            "unit": "small dental clinics in the US",
            "status": "sourced", "source_ids": ["S1"],
        },
        "sam_share": {
            "low": 0.20, "base": 0.25, "high": 0.50,
            "unit": "fraction of customers who could buy",
            "status": "assumption", "source_ids": [],
        },
        "som_share": {
            "low": 0.05, "base": 0.10, "high": 0.20,
            "unit": "fraction of SAM we could win in 3 years",
            "status": "assumption", "source_ids": [],
        },
        "price": {
            "low": 40, "base": 50, "high": 60,
            "unit": "US dollars per purchase",
            "status": "sourced", "source_ids": ["S2"],
        },
        "purchases_per_year": {
            "low": 1, "base": 2, "high": 3,
            "unit": "purchases per customer per year",
            "status": "assumption", "source_ids": [],
        },
    }


def scenarios_by_name(data):
    return {s.name: s for s in size_market(load_assumptions(data))}


# --- The math ---------------------------------------------------------------


def test_base_scenario_matches_hand_math():
    base = scenarios_by_name(sample_data())["base"]
    # 20,000 x $50 x 2 = $2,000,000; x 0.25 = $500,000; x 0.10 = $50,000
    assert base.tam == pytest.approx(2_000_000)
    assert base.sam == pytest.approx(500_000)
    assert base.som == pytest.approx(50_000)


def test_low_and_high_scenarios_in_order():
    scenarios = size_market(load_assumptions(sample_data()))
    assert [s.name for s in scenarios] == ["low", "base", "high"]

    low, _, high = scenarios
    # 10,000 x $40 x 1 = $400,000; x 0.20 = $80,000; x 0.05 = $4,000
    assert (low.tam, low.sam, low.som) == pytest.approx((400_000, 80_000, 4_000))
    # 40,000 x $60 x 3 = $7,200,000; x 0.50 = $3,600,000; x 0.20 = $720,000
    assert (high.tam, high.sam, high.som) == pytest.approx((7_200_000, 3_600_000, 720_000))


def test_zero_customers_gives_zero_everywhere():
    data = sample_data()
    data["customers"].update(low=0, base=0, high=0)
    for scenario in size_market(load_assumptions(data)):
        assert (scenario.tam, scenario.sam, scenario.som) == (0, 0, 0)


def test_zero_som_share_keeps_tam_and_sam():
    data = sample_data()
    data["som_share"].update(low=0, base=0, high=0)
    base = scenarios_by_name(data)["base"]
    assert base.tam == pytest.approx(2_000_000)
    assert base.sam == pytest.approx(500_000)
    assert base.som == 0


# --- Missing values ---------------------------------------------------------


def test_missing_assumption_is_named():
    data = sample_data()
    del data["price"]
    with pytest.raises(SizingError, match="price"):
        load_assumptions(data)


def test_all_missing_assumptions_reported_together():
    data = sample_data()
    del data["price"]
    del data["som_share"]
    with pytest.raises(SizingError) as error:
        load_assumptions(data)
    assert "price" in str(error.value)
    assert "som_share" in str(error.value)


def test_missing_base_value_is_an_error_not_zero():
    data = sample_data()
    del data["customers"]["base"]
    with pytest.raises(SizingError, match="customers"):
        load_assumptions(data)


def test_null_base_value_is_an_error_not_zero():
    data = sample_data()
    data["customers"]["base"] = None
    with pytest.raises(SizingError, match="customers"):
        load_assumptions(data)


# --- Bad values -------------------------------------------------------------


@pytest.mark.parametrize("bad_value", ["20000", True])
def test_value_must_be_a_number(bad_value):
    data = sample_data()
    data["customers"]["base"] = bad_value
    with pytest.raises(SizingError, match="number"):
        load_assumptions(data)


def test_negative_value_rejected():
    data = sample_data()
    data["price"]["low"] = -5
    with pytest.raises(SizingError, match="negative"):
        load_assumptions(data)


def test_share_above_one_rejected():
    data = sample_data()
    data["sam_share"]["high"] = 1.5
    with pytest.raises(SizingError, match="sam_share"):
        load_assumptions(data)


def test_low_above_base_rejected():
    data = sample_data()
    data["price"]["low"] = 55  # base is 50
    with pytest.raises(SizingError, match="low <= base <= high"):
        load_assumptions(data)


def test_unknown_status_rejected():
    data = sample_data()
    data["price"]["status"] = "verified"  # check.py decides that, not the brief
    with pytest.raises(SizingError, match="status"):
        load_assumptions(data)


def test_sourced_assumption_needs_a_source_id():
    data = sample_data()
    data["price"]["source_ids"] = []
    with pytest.raises(SizingError, match="source"):
        load_assumptions(data)


# --- Unverified sources -----------------------------------------------------


def test_unverified_source_becomes_assumption():
    data = sample_data()
    data["price"]["source_ids"] = ["S1", "S2"]
    assumptions = load_assumptions(data)
    original = copy.deepcopy(assumptions)

    # S1 checked out; S2 did not (page did not load, or quote not found).
    marked = mark_unverified_as_assumptions(assumptions, verified_ids={"S1"})

    assert marked["customers"].status == "sourced"  # cites only S1
    assert marked["price"].status == "assumption"  # cites S2
    assert marked["price"].base == 50  # the number is kept, only the label changes
    assert assumptions == original  # the input is not changed
