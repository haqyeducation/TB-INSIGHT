# TB-INSIGHT — corrected methods v0.9

The study uses a complete ecological province-month panel covering 38 Indonesian
provinces from January 2024 through December 2025 (912 observations). The primary
outcome is the monthly number of patients starting drug-susceptible TB treatment
in SITB. It must not be described as TB incidence. Mid-year BPS population is
used as the model offset and to calculate treatment starts per 100,000.

Temperature, relative humidity, and precipitation come from NASA POWER. Grid
cells were aggregated to repaired BIG province polygons using cosine-latitude
weights; small provinces without a contained grid centre use the nearest grid
cell and are flagged. Province-calendar-month anomalies are standardized against
1991–2020 normals. Individual lag 0–3 and a lag-0–2 mean are available.

BPS population, density, sanitation, and poverty retain their official reference
period. Annual values are repeated only for joining to monthly rows; they are not
presented as monthly measurements. Poverty extraction uses province-row boundaries
to handle omitted PDF placeholders and is range-checked from 0 to 100 percent.

Count models use Poisson pseudo-maximum likelihood with log link, a log-population
offset, province and period fixed effects, and province-clustered standard errors.
The primary climate window inherited from S2 is the lag-0–2 mean. Twelve individual
lag models (three climate families × lag 0–3) and nine separate climate × social
interaction models are sensitivity/exploratory analyses; no lag is selected by its
p-value and interaction p-values are not multiplicity-adjusted.

Spatial analysis uses a canonical 38-province BIG boundary. The primary graph
starts with queen contiguity and adds the shortest polygon-to-polygon bridge across
disconnected components until connected. Every bridge is explicitly labelled as
an analytical cross-water link. Monthly Local Moran statistics use row-standardized
weights, 999 complete-label permutations, a fixed seed, and Benjamini–Hochberg FDR
within each month. KNN-3 weights are retained for sensitivity analysis.

Because only 24 months are observed, all model and LISA results are ecological and
exploratory. They do not identify causal climate effects or establish a long-term
seasonal cycle. The 2025 outcome fields are additionally affected by cohort maturity.

