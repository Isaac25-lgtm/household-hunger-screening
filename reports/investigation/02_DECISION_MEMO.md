# Decision memo: how to make the hunger-screening paper stronger

*27 October 2026, for the study team.*

## The question

Can the Malawi and Liberia household hunger paper make a materially stronger contribution? Or should we publish the careful applied paper we already have?

## What we found

1. **The earlier results hold up.** An independent re-computation from the raw files reproduces them exactly. The interview dates confirm that households were called every two months, in either odd or even months.

2. **A second Malawi dataset points the same way.** It is the World Bank's national phone survey, 2020–2024: 1,729 households, 15 rounds with food-security questions. In both datasets, one contact in January–March missed fewer of the hungry households than a contact at a random time. That held in every year where those months were observed. The size of the gap varies:

   | Dataset | One January–March contact | One contact at a random time |
   |---|---|---|
   | Aggarwal Malawi panel (HHS) | missed 18–38% | missed 55–60% |
   | World Bank panel | missed 12–26% | missed 22–41% |

   The two surveys use different questions, so the results are not pooled or directly compared.

3. **Picking the month from last year's data can backfire.** In the World Bank survey, the 2020 data start at the pandemic onset (late May 2020), and that was also the first interview. Choosing "the best month" from 2020 picked June. June was then worse than random in 2021 and again in 2023–24. Fixing the month in advance from the known hunger season (January–March) would have worked every time it could be checked.

4. **The result survives any pattern of missing interviews, but not much worst-case answer error.** In the most unfavourable case, errors in 0.5–2.5% of recorded answers could erase the timing advantage. The paper must state that assumption plainly.

5. **Timing seems to matter most for poorer and rural households.** For the richest fifth of households, timing barely mattered. This was not planned in advance, so treat it as a lead to confirm.

6. **A second contact helps less than a well-timed first one, and it can be targeted simply.**
   - One well-timed contact identifies 49–67 of every 100 households. A second contact adds about 9–12.
   - Re-contacting households that answered "yes" to a milder hunger question finds 14–19 more hungry households per 100 calls than re-contacting at random.
   - A statistical model trained on earlier data did no better than simply counting those "yes" answers. No machine learning is needed.

## What we could not do

- **No blind test.** Every dataset had been partly looked at before this investigation.
- **The World Bank questions are not the Household Hunger Scale.** They are related food-insecurity questions.
- **Two important datasets are not public.** The monthly HHS data from CRS and Cornell (MIRA) and the Malawi monitoring system (RFMS) are not available.
- **Myanmar was not downloaded.** It needs a registration form in your name.
- **No measure of costs or of programme benefit.**
- **Prior work covers the direction.** Field guidance already recommends lean-season data collection. Zhu et al. (2026) and Wollburg et al. (2025, an unpublished draft) already show that single surveys miss many food-insecure households. Our contribution is to quantify and test the timing advice, not to discover it.

## Recommendation

1. **Now:** write the applied paper on both Malawi panels, with Liberia in the supplement. Make timing at a fixed number of contacts the main question, not frequency. Report the backfire result and the error tipping points openly.
   - Good fit: *Food Security*, *Global Food Security*, *Public Health Nutrition*, *PLOS ONE*.
   - This describes fit, not chances of acceptance.
2. **Stretch (Food Policy-type journals):** only if we add a genuinely untouched test. The cheapest route is a locked protocol on other World Bank phone-survey countries (Burkina Faso, Ethiopia, Nigeria, Tanzania, Uganda). Write the protocol first, then download, and judge the result as it falls. A data request for MIRA's monthly hunger-scale data would be the best route on measurement.
3. **If neither works out,** publish the applied paper. It is a solid, honest contribution as it stands.

## Decisions needed from you

1. Approve or reject the locked-protocol multi-country test. It needs your World Bank login.
2. Decide whether to contact CRS and Cornell about MIRA. I have sent nothing.
3. Choose the manuscript framing. Options are in `06_MANUSCRIPT_OPTIONS.md`.
4. Confirm author details and the ethics route.
5. Decide whether to merge this branch into `main`. Nothing has been merged.
