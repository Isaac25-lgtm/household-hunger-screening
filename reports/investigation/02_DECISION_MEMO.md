# Decision memo: how to make the hunger-screening paper stronger

*27 October 2026, for the study team. Updated after the locked multi-country test.*

## The question

Can the Malawi and Liberia household hunger paper make a materially stronger contribution? Or should we publish the careful applied paper we already have?

## What we found

1. **The earlier results hold up.** An independent re-computation from the raw files reproduces them exactly. The interview dates confirm that households were called every two months.

2. **In Malawi, timing helps.** In two different Malawi panels, one contact in January–March missed fewer of the households reporting hunger at any contact than a contact at a random time. That held in every Malawi year where those months were observed.

3. **That Malawi result does not travel as a general lean-season rule.** I wrote the test plan and locked it before downloading data for five other countries, then ran it as written. The rule was "contact households once in the lean season shown on FEWS NET's typical-year calendar". It did *not* beat a randomly timed contact:

   | Horizon | Lean-season contact versus random |
   |---|---|
   | Burkina Faso 2020–21 | missed **11 points more** |
   | Uganda 2020–21 | no clear difference |

   By the pre-set rule, the hypothesis is **contradicted**. The likely reason, found afterwards and not part of the locked test, is that in 2020–21 reported hunger fell round after round. That may be pandemic recovery or people getting used to the survey, and it outweighed any seasonal pattern. In the calmer 2022–23 Burkina Faso data, lean-season contacts did much better than random, by about 32 points.

4. **Picking the month from last year's data can also backfire** (World Bank Malawi survey, after a pandemic-onset first round).

5. **The second-contact rule did replicate.** Re-contacting households that answered "yes" to a milder hunger question at the first contact found more hungry households than random re-contact:
   - in all 3 testable horizons of the locked test (Burkina Faso, Uganda);
   - in Malawi.

   A statistical model did no better than simply counting those "yes" answers.

6. **The Malawi timing result has limits.** No pattern of missing interviews can erase it, but worst-case errors in 0.5–2.5% of recorded answers could.

## What this means

The strongest honest paper now has a clearer and more credible message:

- **When to screen is a local, year-specific question.** It is not a calendar you can copy. Programmes should check seasonal timing against their own recent data, and be wary when a shock or a new survey distorts the pattern.
- **A simple, portable improvement exists.** Re-contact the households that showed early warning signs. It replicated across countries.

The locked test is now the paper's main strength. It includes a pre-specified hypothesis that failed, which reviewers rarely see and tend to trust.

## What we could not do

- **Nigeria and Tanzania:** too few food-security rounds per year to test anything.
- **Ethiopia:** no single national lean season, so it was excluded from the calendar test by design.
- **Tanzania round 9:** the published Stata file is damaged.
- **Monthly hunger-scale data from CRS/Cornell:** not obtained.
- **Not measured:** costs and programme benefit.

## Recommendation

1. **Write the paper around both results.**
   - Malawi timing evidence, with its limits.
   - The locked five-country test, where the calendar rule failed and the second-contact rule held.

   Working title: *"When to ask about hunger: seasonal timing helps in Malawi but does not transfer as a calendar rule, while a simple second-contact rule does."*
2. **Journals:** *Global Food Security* or *Food Security* are good fits. *Food Policy* is now a realistic stretch because of the locked test. This describes fit, not chances of acceptance.
3. **Before submission:**
   - confirm the design facts;
   - finish the literature work;
   - get a statistician to review the methods;
   - get an ethics decision;
   - optionally, re-check Tanzania with its CSV release.

## Decisions needed from you

1. Approve this framing.
2. Whether to request the CRS/Cornell monthly hunger-scale data.
3. Your author details and the ethics route.
4. Whether to push or merge the branch. Nothing has been pushed.
5. Rotate your World Bank password, as you planned.
