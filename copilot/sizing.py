"""Bottom-up market sizing from explicit assumptions (Rule 3: the model never states a size).

    TAM = customers x units_per_customer x price x purchases_per_year
    SAM = TAM x sam_share     (share of customers who could buy)
    SOM = SAM x som_share     (share we could realistically win in about 3 years)

units_per_customer is how many units one customer pays for (bins per dealership, seats per
office). Each input is one number from a source or one guess, never a number the model worked
out from other numbers, so this file does all of the multiplying (Rule 3).

Each assumption has low, base, and high values, so there are three scenarios: all low,
all base, and all high. Shares are fractions from 0 to 1 (0.25 means 25%).

Input shape, one entry per assumption name (this is what brief.json holds):

    "customers": {"low": 10000, "base": 20000, "high": 40000,
                  "unit": "small dental clinics in the US",
                  "status": "sourced", "source_ids": ["S3"]}

Zero is a valid value. A missing value is always an error, never treated as zero.
"""

from dataclasses import dataclass, replace

ASSUMPTION_NAMES = (
    "customers", "units_per_customer", "price", "purchases_per_year", "sam_share", "som_share",
)
SHARE_NAMES = ("sam_share", "som_share")
SCENARIOS = ("low", "base", "high")
STATUSES = ("sourced", "assumption")


class SizingError(ValueError):
    """An assumption is missing or invalid. The message says which one and why."""


@dataclass(frozen=True)
class Assumption:
    name: str
    low: float
    base: float
    high: float
    unit: str
    status: str  # "sourced" or "assumption"
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class Scenario:
    name: str  # "low", "base", or "high"
    tam: float
    sam: float
    som: float


def assumption_from_dict(name: str, data: dict) -> Assumption:
    """Build one Assumption from brief.json data, rejecting anything we can't do math on."""
    values = {}
    for scenario in SCENARIOS:
        value = data.get(scenario)
        if value is None:
            raise SizingError(f"{name}: missing the {scenario} value")
        # bool is a subclass of int in Python, so rule it out explicitly.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SizingError(f"{name}: {scenario} value must be a number, got {value!r}")
        if value < 0:
            raise SizingError(f"{name}: {scenario} value cannot be negative ({value})")
        if name in SHARE_NAMES and value > 1:
            raise SizingError(
                f"{name}: {scenario} value must be a fraction from 0 to 1, got {value}"
            )
        values[scenario] = value

    if not values["low"] <= values["base"] <= values["high"]:
        raise SizingError(
            f"{name}: values must satisfy low <= base <= high, got "
            f"{values['low']}, {values['base']}, {values['high']}"
        )

    status = data.get("status")
    if status not in STATUSES:
        raise SizingError(f"{name}: status must be 'sourced' or 'assumption', got {status!r}")

    source_ids = tuple(data.get("source_ids") or [])
    if status == "sourced" and not source_ids:
        raise SizingError(f"{name}: marked sourced but cites no source ids")

    return Assumption(
        name=name,
        low=values["low"],
        base=values["base"],
        high=values["high"],
        unit=data.get("unit", ""),
        status=status,
        source_ids=source_ids,
    )


def load_assumptions(data: dict) -> dict[str, Assumption]:
    """Build all six assumptions. Lists every missing name at once so one fix is enough."""
    missing = [name for name in ASSUMPTION_NAMES if name not in data]
    if missing:
        raise SizingError("Missing assumptions: " + ", ".join(missing))
    return {name: assumption_from_dict(name, data[name]) for name in ASSUMPTION_NAMES}


def mark_unverified_as_assumptions(
    assumptions: dict[str, Assumption], verified_ids: set[str]
) -> dict[str, Assumption]:
    """Relabel any sourced assumption that cites an unverified source as an assumption.

    An unverified figure never counts as evidence (SPEC.md). The number stays the same so the
    user can still see and edit it; only its label changes. Returns new objects.
    """
    marked = {}
    for name, assumption in assumptions.items():
        all_verified = all(sid in verified_ids for sid in assumption.source_ids)
        if assumption.status == "sourced" and not all_verified:
            assumption = replace(assumption, status="assumption")
        marked[name] = assumption
    return marked


def compute_scenario(scenario: str, assumptions: dict[str, Assumption]) -> Scenario:
    """TAM, SAM, and SOM using the low, base, or high value of every assumption."""
    def value(name):
        return getattr(assumptions[name], scenario)

    tam = (value("customers") * value("units_per_customer") * value("price")
           * value("purchases_per_year"))
    sam = tam * value("sam_share")
    som = sam * value("som_share")
    return Scenario(name=scenario, tam=tam, sam=sam, som=som)


def size_market(assumptions: dict[str, Assumption]) -> list[Scenario]:
    """The three scenarios, in order: low, base, high."""
    return [compute_scenario(scenario, assumptions) for scenario in SCENARIOS]
