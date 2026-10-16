# brief.json and ledger.json format

The brief skill writes two files into the run folder, then runs `check.py` on that folder.
`check.py` refuses to run (and lists every problem) if either file breaks the rules below.
Fix the problems and run it again.

## ledger.json: the sources

A JSON list. One entry per quote you copied from a page:

| Field | Meaning |
|---|---|
| `id` | `S1`, `S2`, `S3`, ... Each id is used once. |
| `url` | The page the quote came from (http or https). |
| `title` | The page title. |
| `quote` | Exact text copied from the page, **25 words or fewer**. Copy it from the output of `sources.py fetch <url>`, never from memory or a search snippet. |
| `accessed` | The date you read the page, like `2026-10-16`. |

Two entries may share a URL (two quotes from one page). Each page is downloaded once.

## brief.json: the brief

### Claims

Every factual statement is a **claim**:

```
{"text": "...", "status": "sourced" | "assumption", "source_ids": ["S1"]}
```

- `"sourced"`: the text is backed by the quotes of the listed sources. Must cite at least one id.
- `"assumption"`: your estimate or guess. `source_ids` may be empty.
- Never write "verified". `check.py` decides that, not you. A sourced claim is Verified only if
  every id it cites is in the ledger, the page loads, the quote is on the page, and the quote is
  25 words or fewer. Otherwise it is Unverified, with the reason, and it stays in the brief.

### Fields

| Field | Meaning |
|---|---|
| `idea` | The product idea, in one line. |
| `research_date` | Today's date, like `2026-10-16`. |
| `depth` | `"quick"` or `"deep"`. |
| `target_customer`, `geography` | Who and where. |
| `currency` | Optional, default `"USD"`. |
| `summary.found` | List of claims: the main things the research found. |
| `summary.unknowns` | List of text: what we still don't know. |
| `riskiest_assumptions` | List of `{assumption, why_risky, how_to_test}`, riskiest first. |
| `interview_script` | `{intro, questions: [{question, listening_for}]}`. |
| `competitors` | List of `{name, url, description: claim, price: claim}`. |
| `market_size` | The five sizing assumptions below. |

### Interview questions

Ask about past behavior, never hypotheticals: "Tell me about the last time...", "What did you
try...", "How do you handle ... today?". Not "Would you buy...", "Will you...", "If we built...".
`check.py` warns about questions that sound hypothetical, and brief.md marks them for rewriting.

### Market size

Never state a market size. Give the five inputs and `sizing.py` does the math:

    TAM = customers x price x purchases_per_year
    SAM = TAM x sam_share     (share of customers who could buy)
    SOM = SAM x som_share     (share we could win in about 3 years)

Each input has `low`, `base`, and `high` numbers (low <= base <= high, none negative), a `unit`,
a `status`, and `source_ids`. Shares are fractions from 0 to 1 (0.25 means 25%). A sourced input
whose source is Unverified is used in the math as an assumption.

## Example

A made-up example. Both blocks below are checked by the tests, so they always pass `check.py`.

ledger.json:

```json
[
  {
    "id": "S1",
    "url": "https://example.com/pricing",
    "title": "Pricing | Example Booking",
    "quote": "Starter: $29 per month for one location",
    "accessed": "2026-10-16"
  },
  {
    "id": "S2",
    "url": "https://example.org/clinic-census",
    "title": "Clinic Census 2025",
    "quote": "The census counted 20,000 small dental clinics in the United States.",
    "accessed": "2026-10-16"
  }
]
```

brief.json:

```json
{
  "idea": "Online booking and reminder texts for small dental clinics",
  "research_date": "2026-10-16",
  "depth": "quick",
  "target_customer": "Office managers at dental clinics with one to five chairs",
  "geography": "United States",
  "currency": "USD",
  "summary": {
    "found": [
      {"text": "There are about 20,000 small dental clinics in the US.",
       "status": "sourced", "source_ids": ["S2"]}
    ],
    "unknowns": ["Whether office managers or dentists choose the booking tool."]
  },
  "riskiest_assumptions": [
    {"assumption": "Missed appointments are a top-three problem for office managers.",
     "why_risky": "No independent evidence yet.",
     "how_to_test": "Ask five office managers to walk through their last no-show."}
  ],
  "interview_script": {
    "intro": "Thanks for talking with me. I'm learning how small clinics handle appointments.",
    "questions": [
      {"question": "Tell me about the last time a patient missed an appointment.",
       "listening_for": "What it cost them and what they did afterward."}
    ]
  },
  "competitors": [
    {"name": "Example Booking",
     "url": "https://example.com",
     "description": {"text": "Online booking for small clinics.",
                     "status": "assumption", "source_ids": []},
     "price": {"text": "$29 per month for one location.",
               "status": "sourced", "source_ids": ["S1"]}}
  ],
  "market_size": {
    "customers": {"low": 10000, "base": 20000, "high": 40000,
                  "unit": "small dental clinics in the US",
                  "status": "sourced", "source_ids": ["S2"]},
    "price": {"low": 29, "base": 50, "high": 79, "unit": "US dollars per month",
              "status": "assumption", "source_ids": []},
    "purchases_per_year": {"low": 12, "base": 12, "high": 12, "unit": "months billed per year",
                           "status": "assumption", "source_ids": []},
    "sam_share": {"low": 0.2, "base": 0.25, "high": 0.5,
                  "unit": "fraction of clinics who could buy",
                  "status": "assumption", "source_ids": []},
    "som_share": {"low": 0.05, "base": 0.1, "high": 0.2,
                  "unit": "fraction of SAM we could win in 3 years",
                  "status": "assumption", "source_ids": []}
  }
}
```
