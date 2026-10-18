# TB-INSIGHT — corrected results shell v0.6

## Data and QA

The final panel contains 912 unique province-month observations with no missing
required outcome, BPS, climate, or disaster fields. All outcome component balances
equal zero. Poverty ranges from 3.72% to 32.97% in 2024–2025; the previously reported
values above 100% were extraction errors and are superseded.

## Climate lag sensitivity

All twelve lag models converged. Eleven showed no nominal association at p<0.05.
Precipitation lag 1 had IRR 1.0057 (95% CI 1.0006–1.0107; p=0.027). This isolated
nominal result must not be promoted as the primary lag because twelve lag models
were inspected and p-values were not multiplicity-adjusted.

## Climate × social interactions

Nine interaction models were rerun after correcting BPS poverty. Nominal p<0.05
occurred for temperature × poverty, temperature × density, temperature × sanitation,
precipitation × poverty, precipitation × sanitation, humidity × density, and humidity
× sanitation. Humidity × poverty was borderline (p=0.052), while precipitation ×
density was not nominally significant. These are exploratory effect-modification
signals, not causal or confirmatory findings; they require multiplicity-aware and
leverage sensitivity analyses before inclusion as headline results.

## Spatial results

Across 912 monthly Local Moran tests, 87 province-month classifications were
significant at raw p<0.05 and one remained significant after within-month FDR.
Accordingly, the defensible conclusion is weak and unstable local spatial evidence
under strict correction, not a validated national "risk map." The raw layer may be
shown for exploration only when clearly distinguished from the FDR layer.

## Unsupported claims

This sprint does not produce incidence estimates, causal effects, a validated early
warning system, forecasting accuracy, or an ILP resource-allocation optimizer. Those
claims must remain outside the manuscript results unless separate validated outputs
are later delivered.
