# Backtest: three past products

This folder checks what a market brief finds for three product ideas whose real outcomes are
public. Each idea is described generically, with no company names. Josh runs each brief with
the plugin, saves the run here, and compares what the brief found with what really happened
in [RESULTS.md](RESULTS.md).

**This is not a blind test.** Web search can find the real companies, and each description
matches a real product, so a brief may well find the very company it describes. What this
backtest shows is what a brief surfaces (competitors, prices, risks to test) and how its
market size, computed by sizing.py from visible assumptions, compares with what the market
turned out to be. It does not show that the brief could predict an unknown market.

## The cases

Every command names the target customer, the geography, and a price guess, so the brief has
nothing to ask. All three run at the default quick depth.

### 1. Infant vital-signs sock

A sock that tracks an infant's heart rate and blood oxygen while they sleep and alerts the
parents' phones. Target customer: new parents of babies up to 18 months old. Geography: United
States. Price guess: $300 one-time for the sock and base station.

```
/market-copilot:brief "A sock that tracks an infant's heart rate and blood oxygen while they sleep and alerts the parents' phones. Target customer: new parents of babies up to 18 months old. Geography: United States. Price guess: $300 one-time for the sock and base station."
```

### 2. Smart sprinkler controller

A wireless smart sprinkler controller that replaces a home's irrigation timer and adjusts
watering to local weather, controlled from a phone app. Target customer: homeowners with
in-ground sprinkler systems. Geography: United States. Price guess: $200 one-time.

```
/market-copilot:brief "A wireless smart sprinkler controller that replaces a home's irrigation timer and adjusts watering to local weather, controlled from a phone app. Target customer: homeowners with in-ground sprinkler systems. Geography: United States. Price guess: $200 one-time."
```

### 3. Beehive mite sensor

A sensor that sits in a beehive and warns beekeepers when varroa mite levels are rising.
Target customer: hobbyist and small commercial beekeepers. Geography: United States. Price
guess: $150 per hive, one-time.

```
/market-copilot:brief "A sensor that sits in a beehive and warns beekeepers when varroa mite levels are rising. Target customer: hobbyist and small commercial beekeepers. Geography: United States. Price guess: $150 per hive, one-time."
```

## How to run them

1. Open a terminal in a scratch folder outside this repo and start Claude Code with the
   plugin: `claude --plugin-dir <path to this repo>`.
2. Run the three commands above, one at a time. Each saves a run folder under
   `market-briefs\<date>-<short-name>\` in the scratch folder.
3. Copy each run folder into `backtest\runs\` in this repo, for example in PowerShell:

   ```
   Copy-Item -Recurse "market-briefs\<date>-<short-name>" "<path to this repo>\backtest\runs\"
   ```

4. Open them in the viewer: `/market-copilot:view <path to this repo>\backtest\runs`.

`tests/test_backtest.py` checks that every run in `backtest/runs/` loads in the viewer with no
problems.
