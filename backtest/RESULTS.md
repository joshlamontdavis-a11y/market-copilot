# Backtest results

What each brief found, next to what really happened. The cases and commands are in
[README.md](README.md).

**This is not a blind test.** Web search can find the real companies, and each description
matches a real product, so a brief may find the very company it describes.

How the columns are filled:

- Top competitors are the first three each brief lists, with the price text from brief.json
  and the check result check.py gave that price. Riskiest assumptions are copied from
  brief.json.
- The base market size is copied from each run's check_report.json, where sizing.py computed
  it from the assumptions in the brief. No number here is typed in by the model.
- The check.py counts are verified, assumption, and unverified items.
- "What actually happened" is filled in by hand from public sources.

| Case | Run folder | Top competitors found | Riskiest assumptions | Base market size (TAM / SAM / SOM, from sizing.py) | check.py counts | What actually happened |
|---|---|---|---|---|---|---|
| 1. Infant vital-signs sock | `2026-10-27-infant-sleep-sock` | Owlet Dream Sock: $299.99, including the sensor; HSA/FSA eligible with Affirm payment plans as low as $26/mo. (Verified)<br>Masimo Stork: Not confirmed. Masimo's own pages and a retailer listing did not load, so the current US price is unknown. (Assumption)<br>eufy Smart Sock S340: Deal price $329.99 on a VentureBeat Deals listing. (Verified) | 1. Parents have a problem with existing smart socks (false alarms, fit, price, trust) strong enough to switch to a new brand.<br>2. The product can get FDA clearance for oxygen readings and alerts at a cost and timeline the business can survive.<br>3. Pediatricians will not steer parents away from the product.<br>4. Around 25% of new-parent households could afford and would consider a $300 vitals monitor. | $1,088,680,200 / $272,170,050 / $13,608,502 | 18 verified, 12 assumptions, 0 unverified | |
| 2. Smart sprinkler controller | `2026-10-27-smart-sprinkler-controller` | Rachio 3: 8-zone model on sale at Home Depot for $154.42, normally $199. (Verified)<br>Orbit B-hyve: Controller for 6 zones: $90-$115; 12 zones: $105-$120. (Verified)<br>Rain Bird ST8: The Rain Bird ST8 is $160. (Verified) | 1. Homeowners will pay $200 for a new brand when Rachio and B-hyve already do weather-based watering at the same price or less.<br>2. Homeowners with clock-based timers feel enough pain to replace a working timer.<br>3. The homeowner, not a landscaper or irrigation contractor, chooses and installs the controller.<br>4. A one-time price with no subscription can fund ongoing weather data and app costs. | $560,000,000 / $196,000,000 / $980,000 | 17 verified, 12 assumptions, 0 unverified | |
| 3. Beehive mite sensor | `2026-10-28-varroa-hive-sensor` | BroodMinder (T2 temperature sensor + hub): T2 sensor: $47.99 USD at one US retailer (hub sold separately). (Verified)<br>BeeRight: No published price found; US availability unknown. (Assumption)<br>ApisProtect: $3 per hive monthly, according to a third-party blog. (Verified) | 1. A sensor sitting in the hive can estimate varroa levels reliably enough to replace or reduce manual mite tests.<br>2. Hobbyists will pay $150 per hive when a reusable mite test jar costs tens of dollars.<br>3. Beekeepers lose colonies because they miss when mites rise, not because they don't treat or treat badly.<br>4. Small commercial beekeepers will put a sensor in every hive rather than a few per yard. | $29,700,000 / $5,940,000 / $297,000 | 15 verified, 11 assumptions, 0 unverified | |

All three runs used the default quick depth, with research dates of 2026-10-27 (cases 1 and 2)
and 2026-10-28 (case 3). Every ledger source passed check.py, and no run had warnings.

## What each base market size rests on

In every run, only the customer count is sourced. The other five inputs are the brief's
assumptions, which the viewer lets you change. Base values, copied from each run's
check_report.json:

- **1. Infant vital-signs sock:** customers 3,628,934 (US births per year (one new baby, one potential purchase); sourced, Verified); units per customer 1 (systems per baby; assumption); price per purchase $300 (US dollars, one-time; assumption); purchases per year 1 (purchases per new baby per year; assumption); Share who could buy (SAM) 25% (fraction of new-baby households who could afford and would consider a vitals monitor; assumption); Share we could win in ~3 years (SOM) 5% (fraction of SAM we could win in 3 years against Owlet and Masimo; assumption).
- **2. Smart sprinkler controller:** customers 28,000,000 (US homes with in-ground sprinkler systems; sourced, Verified); units per customer 1 (controllers per home; assumption); price per purchase $200 (US dollars per controller, one-time; assumption); purchases per year 0.10 (controller purchases per home per year (one every 7-14 years); assumption); Share who could buy (SAM) 35% (fraction of homes that would buy a smart controller and choose it themselves; assumption); Share we could win in ~3 years (SOM) 0.5% (fraction of SAM we could win in 3 years; assumption).
- **3. Beehive mite sensor:** customers 150,000 (hobby beekeepers in the US (sideliners not counted separately); sourced, Verified); units per customer 4 (hives per beekeeper fitted with a sensor; assumption); price per purchase $150 (US dollars per hive, one-time; assumption); purchases per year 0.33 (sensor purchases per hive per year (replaced every 2-5 years); assumption); Share who could buy (SAM) 20% (fraction of beekeepers who would buy an in-hive gadget; assumption); Share we could win in ~3 years (SOM) 5% (fraction of SAM we could win in 3 years; assumption).
