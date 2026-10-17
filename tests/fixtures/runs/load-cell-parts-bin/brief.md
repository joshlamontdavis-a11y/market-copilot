# Market brief: A load-cell parts bin that weighs its contents and alerts when stock runs low

Research date: 2026-10-16. Prices and competitors change, so check the links before relying on them.

Target customer: Parts departments at franchised car dealerships. Geography: United States. Depth: quick.

This brief prepares you for customer interviews. It does not show that anyone will buy.

Verified means the quoted text is on the cited page. Read each quote to judge whether it supports the claim.

## 1. Summary

Checked by check.py: 13 verified, 11 assumptions, 0 unverified.

### What we found

- **[Verified]** NADA counts 16,991 franchised light-vehicle dealers in the US (mid-year 2026). (S1)
- **[Verified]** In the first half of 2026, dealerships wrote more than 136 million repair orders, with service and parts sales of nearly $83 billion. (S2)
- **[Verified]** Weight-based bins that trigger restocks already exist from industrial suppliers: Fastenal's scale FASTBin restocks when quantity falls below the item's min level. (S3)
- **[Verified]** eTurns SensorBins hardware costs around $96 per item, on top of the Optimize plan subscription. (S8, S9)
- **[Verified]** A dealer consultant describes min/max levels in the business management software that tell staff when it is time to reorder. (S10)
- **[Verified]** The same consultant writes that non-parts people entering the parts department are generally the reason counts are off. (S11)
- **[Assumption]** The existing weight-bin products found are sold into manufacturing and MRO, not dealership parts departments, so a dealership-focused version could be an open niche.
- **[Assumption]** Because the dealer management system already flags reorder points, the bin's value would come from catching miscounts (shrink, unrecorded pulls), not from the alert itself.

### What we still don't know

- How many bins or fast-moving part numbers a typical dealership parts department would put on scales.
- Whether the parts manager, fixed-ops director, or dealer principal approves a purchase like this.
- Whether the bins must integrate with the dealer management system (CDK, Reynolds, etc.) to be useful, and whether those vendors allow it.
- How often dealership parts departments actually run out of fast-moving bin parts, and what a stockout costs them.
- Public pricing for Fastenal FASTBin scales, SupplyPro SmartBin, and TeDaLoS sensors (none found).
- The consultant article cited is written for outdoor power equipment dealers; no car-dealership-specific source on bin-level inventory practice was read.

## 2. Riskiest assumptions

1. **Dealership parts departments lose meaningful money or time to stockouts of small bin parts that a scale would catch.**
   - Why it's risky: The DMS already flags reorder points; if counts are mostly accurate, the bin adds little. No dealership-specific stockout data was found.
   - How to test it: Ask five parts managers to walk through the last time a bin part ran out unexpectedly, and what it cost (lost RO time, emergency order, freight).
2. **A parts manager will pay about $80 per bin without needing DMS integration.**
   - Why it's risky: Alerts that don't update the DMS on-hand count may be seen as one more screen to watch; integration may be required and hard to get.
   - How to test it: Ask parts managers how they acted on the last reorder alert they received and which system it came from.
3. **Dealerships would buy from a new hardware vendor rather than from Fastenal, Würth, or an OEM-endorsed supplier they already use.**
   - Why it's risky: Industrial distributors bundle bins with supply contracts; dealers may get similar tech free with a consumables program.
   - How to test it: Ask who supplies their shop consumables today and whether that supplier has ever offered managed bins.
4. **A typical dealership would put around 50 bins on scales.**
   - Why it's risky: This number drives the market size; it is a pure guess.
   - How to test it: Ask parts managers to count how many part numbers they would describe as fast-moving small parts kept in open bins.

## 3. Interview script

Thanks for your time. I'm learning how dealership parts departments keep track of small, fast-moving parts. I'm not selling anything today.

1. Tell me about the last time a part you normally stock ran out before you noticed.
   - Listen for: Which parts, how it was discovered, what it cost (tech downtime, emergency order, freight, lost sale).
2. How do you decide when to reorder small bin parts today?
   - Listen for: DMS min/max, visual checks, distributor reps, subscriptions; how much manual work it takes.
3. Walk me through your last cycle count. What did you find?
   - Listen for: How far off counts were, causes (techs pulling parts, unrecorded usage), time spent.
4. Who supplies your shop consumables and fasteners today, and how does restocking work with them?
   - Listen for: Fastenal, Würth, OEM programs, vendor-managed bins; whether a supplier already restocks for them.
5. What have you tried in the past to keep better track of parts on the shelf?
   - Listen for: Past tools or processes, why they stuck or were dropped, who approved the spend.
6. When you last bought equipment or software for the parts department, who signed off and how long did it take?
   - Listen for: Decision maker, budget size, approval process.

## 4. Competitors

### Fastenal FASTBin (scale)

Link: https://blueprint.fastenal.com/10-common-questions-about-fastbin.html

- What it does: **[Verified]** Scale-based bins that trigger a restock when quantity falls below the item's min level, alerting the local Fastenal branch. (S3, S4)
- Price: **[Assumption]** No public price found; bins appear to be bundled with a Fastenal supply program.

### eTurns TrackStock SensorBins

Link: https://eturns.com/products/features/sensorbins

- What it does: **[Verified]** Weight sensors under bins work with TrackStock IoT cloud software for automated replenishment. (S7)
- Price: **[Verified]** Hardware around $96 per item, available to Optimize Plan customers at an additional hardware cost. (S8, S9)

### SupplyPro SmartBin

Link: https://supplypro.com/products/smartbin

- What it does: **[Verified]** A cabinet storage system with weight-based sensing and a standard RFID badge reader to identify employee access. (S5, S6)
- Price: **[Assumption]** No public price found.

### TeDaLoS universal sensor

Link: https://fastenerandfixing.com/management-systems/smart-bins-in-small-part-warehouses

- What it does: **[Verified]** Sensor units continuously measure the content weight of the container and are wireless and fully mobile. (S13)
- Price: **[Assumption]** No public price found.

### Status quo: DMS min/max plus supplier subscriptions

Link: https://www.rurallifestyledealer.com/articles/5580

- What it does: **[Verified]** Business management software alerts staff when a part reaches its minimum level; Würth USA offers automatic weekly or monthly reorders of frequently used products. (S10, S12)
- Price: **[Assumption]** Included in software and supply contracts dealerships already pay for, so no extra cost.

## 5. Market size

Computed by sizing.py from the assumptions below, not stated by the model. TAM = customers x units per customer x price x purchases per year. SAM = TAM x share who could buy. SOM = SAM x share we could win in about 3 years.

| Assumption | Low | Base | High | Unit | Check |
|---|---|---|---|---|---|
| Customers | 12,000 (guess) | 16,991 | 16,991 | franchised light-vehicle dealers in the US | **[Verified]** (S1) Low is a guess, not from the source. |
| Units per customer | 20 | 50 | 200 | bins per dealership parts department | **[Assumption]** |
| Price per purchase | $60 | $80 | $96 | US dollars per bin, one-time | **[Assumption]** |
| Purchases per year | 0.20 | 0.25 | 0.33 | bin replacements per year (one every 3-5 years) | **[Assumption]** |
| Share who could buy (SAM) | 20% | 30% | 50% | fraction of dealerships that could buy | **[Assumption]** |
| Share we could win in ~3 years (SOM) | 2% | 5% | 10% | fraction of SAM we could win in 3 years | **[Assumption]** |

Price covers: The one-time hardware price per bin only. Any subscription or service fee is left out. purchases_per_year spreads that one-time price over the bin's replacement cycle.

| Scenario | TAM | SAM | SOM |
|---|---|---|---|
| Low | $2,880,000 | $576,000 | $11,520 |
| Base | $16,991,000 | $5,097,300 | $254,865 |
| High | $107,654,976 | $53,827,488 | $5,382,749 |

Low uses every low value, base every base value, high every high value.

## Sources

| Id | Source | Quote | Accessed | Check |
|---|---|---|---|---|
| S1 | [NADA Data \| NADA](https://www.nada.org/nadadata/) | "The nation’s 16,991 franchised light-vehicle dealers sold 7.9 million light-duty vehicles." | 2026-10-16 | Verified |
| S2 | [NADA Data \| NADA](https://www.nada.org/nadadata/) | "Dealerships wrote more than 136 million repair orders, with service and parts sales of nearly $83 billion." | 2026-10-16 | Verified |
| S3 | [10 Common Questions About FASTBin - THE BLUE PRINT](https://blueprint.fastenal.com/10-common-questions-about-fastbin.html) | "When the quantity falls below that item’s min level, a restock is triggered." | 2026-10-16 | Verified |
| S4 | [10 Common Questions About FASTBin - THE BLUE PRINT](https://blueprint.fastenal.com/10-common-questions-about-fastbin.html) | "If an item is below min, the ping alerts your Fastenal branch to generate a restock." | 2026-10-16 | Verified |
| S5 | [SmartBin - SupplyPro](https://supplypro.com/products/smartbin) | "Cabinet Storage System with weight-based sensing for" | 2026-10-16 | Verified |
| S6 | [SmartBin - SupplyPro](https://supplypro.com/products/smartbin) | "SmartBin comes standard with an RFID badge reader to identify employee access to cabinet." | 2026-10-16 | Verified |
| S7 | [SensorBins: IoT Weight Sensors for Auto-Replenishment \| eTurns](https://eturns.com/products/features/sensorbins) | "Weight sensors under bins of supplies work together with TrackStock IoT cloud software for fully automated replenishment." | 2026-10-16 | Verified |
| S8 | [Choose Your TrackStock Demo \| eTurns](https://www.eturns.com/solutions) | "If you'd like to do hands-free usage tracking with SensorBins then it costs around $96/item for the hardware." | 2026-10-16 | Verified |
| S9 | [SensorBins: IoT Weight Sensors for Auto-Replenishment \| eTurns](https://eturns.com/products/features/sensorbins) | "SensorBins are able to be used by customers of the Optimize Plan and are available at an additional hardware cost." | 2026-10-16 | Verified |
| S10 | [Handling Special & Emergency Parts Orders: Part 1](https://www.rurallifestyledealer.com/articles/5580) | "Once the level reaches 6, your software will automatically let you know that it’s time to reorder." | 2026-10-16 | Verified |
| S11 | [Handling Special & Emergency Parts Orders: Part 1](https://www.rurallifestyledealer.com/articles/5580) | "those who are not parts people — are generally the reason your counts are off." | 2026-10-16 | Verified |
| S12 | [Würth USA Subscription Service Automates Frequent Orders \| Fender Bender](https://fenderbender.com/55321446) | "Automotive shops and other businesses can automatically reorder frequently used products on a weekly or monthly schedule, ensuring essential supplies are always on hand." | 2026-10-16 | Verified |
| S13 | [Smart bins in small part warehouses \| Fastener + Fixing Magazine](https://fastenerandfixing.com/management-systems/smart-bins-in-small-part-warehouses) | "The sensor units also continuously measure the content weight of the container but are wireless and fully mobile." | 2026-10-16 | Verified |
