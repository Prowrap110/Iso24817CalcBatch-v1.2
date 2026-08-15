# PROWRAP Dent Mechanism Split Design

**Status:** Approved by Mehmet Can Erden on 2026-08-15.

**Date:** 2026-08-15

## Goal

Replace the single `Dent` mechanism with two explicit mechanisms in the
existing v1.1 calculator and the separate Calcbatch application:

- `Dent w/crack` retains the current conservative full-pressure laminate
  calculation.
- `Dent no-crack` uses Type A component-pipe substrate load sharing for an
  external defect.

The two applications remain separate repositories and separate Streamlit
deployments. The v1.1 change is implemented and verified first; Calcbatch is
then updated to use the same approved engineering behavior.

## Repositories and deployment boundaries

- v1.1 repository: `Prowrap110/Iso24817Calcv1.1`
- v1.1 application: `https://iso24817calc-prowrapv11.streamlit.app`
- Calcbatch repository: `Prowrap110/Iso24817CalcBatch`
- Calcbatch application: `https://prowrap-batch-calculator.streamlit.app`

No release may copy batch workbook code into v1.1, deploy v1.1 code over the
batch application, or redirect either existing URL. Each repository receives
its own tested commit and independent deployment verification.

## User-facing mechanism names

New v1.1 forms and new Calcbatch templates show these exact choices, in this
order:

1. `Corrosion`
2. `Dent w/crack`
3. `Dent no-crack`
4. `Leak`
5. `Crack`

The generic `Dent` choice is removed from new selection lists.

### Backward compatibility

Previously downloaded controlled Calcbatch workbooks that contain `Dent` are
still accepted. On processing, the legacy value is normalized to
`Dent w/crack`, calculated using the existing full-pressure approach, and
written as `Dent w/crack` in the regenerated result and Cost Calculation
sheet. This migration is intentionally conservative: no old `Dent` row gains
substrate credit without the user explicitly selecting `Dent no-crack` in a
current template.

Matching is exact after trimming surrounding whitespace. Unsupported spellings
remain row-level input errors; the applications do not guess whether an
ambiguous value means cracked or uncracked.

## Calculation routing

### Route matrix

| Mechanism | Location | Remaining wall | Route | Substrate pressure credit |
| --- | --- | --- | --- | --- |
| Dent w/crack | External | at least 1 mm | Type A full-pressure laminate | `0 MPa` |
| Dent no-crack | External | at least 1 mm | Type A substrate load sharing | Component-pipe allowable pressure below |
| Either dent mechanism | Internal | any valid value | Existing Type B route | `0 MPa` |
| Either dent mechanism | External | below 1 mm | Existing Type B route | `0 MPa` |

Corrosion, Leak, and Crack routing remains unchanged. B31G remains limited to
blunt metal loss and is not used to determine a dent's substrate capacity.

### Dent w/crack

`Dent w/crack` is the renamed current dent route. For an external dent with at
least 1 mm remaining wall:

- `p_s = 0 MPa`.
- The laminate carries the full design pressure.
- The current Formula 4, Formula 5, Formula 10, Formula 11, Formula 25,
  Table 12 component factor, Formula 33 tee cap, 7.5.14 minimum-thickness
  floor, and Formulae 18/20/21 axial-extent rules remain unchanged.
- Current numerical results must be reproduced exactly for the same inputs,
  apart from the displayed mechanism and calculation-basis text.

The displayed basis is:

`Dent w/crack - full-pressure laminate`

### Dent no-crack component-pipe allowable pressure

For an external `Dent no-crack` with remaining wall at least 1 mm, derive the
component-pipe allowable stress and pressure solely from existing inputs:

```text
S_allow = SMYS * Design Factor
p_s = 2 * S_allow * t_remaining / OD
```

where:

- `S_allow` is in MPa.
- `SMYS` is the entered pipe yield strength in MPa.
- `Design Factor` is the entered dimensionless factor.
- `t_remaining` is the entered remaining wall thickness in mm.
- `OD` is the entered pipe outside diameter in mm.
- `p_s` is in MPa.

The calculated `p_s` is non-negative. The composite pressure deficit shown in
the report is:

```text
p_composite = max(0, p_design - p_s)
```

The Type A Formula 5 hoop calculation receives `p_s` as the substrate
allowable-pressure term. Formula 4 axial end thrust, Formula 10 allowable axial
strain, Formula 11 performance-data hoop strain, Formula 25 cyclic derating,
Table 12 component factors, Formula 33, and the minimum-thickness and overlap
rules remain active. If `p_s` covers the pressure load, the hoop requirement
may be zero, but the axial requirement, component requirements, and ISO
minimum-thickness floor still apply.

The displayed basis is:

`Dent no-crack - substrate load sharing`

### Representative acceptance vector

For OD 457.2 mm, nominal and remaining wall 9.53 mm, SMYS 359 MPa,
Design Factor 0.72, design pressure 50 bar, temperature 40 degC, design life
20 years, straight pipe, cyclic factor 1.0, and restrained axial case 0:

- `Dent w/crack` retains `p_s = 0 MPa` and the current nine-ply result.
- `Dent no-crack` calculates
  `S_allow = 359 * 0.72 = 258.48 MPa` and
  `p_s = 2 * 258.48 * 9.53 / 457.2`, which exceeds 5 MPa design pressure.
  The hoop deficit is therefore zero and the ISO minimum-thickness floor
  governs unless another active check requires more thickness.

Automated tests compare exact unrounded values; user-facing reports may round
only for display.

## v1.1 application changes

- Replace `Dent` in the mechanism selector with the two approved values.
- Normalize the mechanism once before routing so every downstream calculation,
  report, and test uses the canonical value.
- Add a focused component-pipe allowable-pressure helper whose inputs and units
  are explicit.
- Pass zero substrate credit for `Dent w/crack` and the calculated `p_s` for
  external `Dent no-crack` into both the baseline Type A calculation and the
  optional Type A / Class 3 cross-check.
- Update the Engineering Analysis and generated report to state the mechanism,
  substrate-credit basis, allowable pipe stress, and calculated `p_s`.
- Remove the current misleading caption that implies every external dent
  automatically receives effective-pipe-capacity credit.
- Preserve the current default state of the optional Type A / Class 3 checkbox.
- Retain Tg = 110 degC and its derived 90 degC design limit unchanged.

## Calcbatch changes

- Update the controlled template dropdown and instructions with the two new
  mechanism names.
- Keep the existing workbook columns and seven-sheet order; no new input column
  is added.
- Accept legacy `Dent` only as an upgrade alias for `Dent w/crack`.
- Normalize mechanism values before engine invocation and before regenerating
  `Batch Input & Results` and `Cost Calculation`.
- Port the approved v1.1 calculation helper and routing change into the isolated
  batch engine, recording the source revision in `ENGINE_SOURCE.md`.
- Preserve Cost Calculation formulas, warning codes, 300/500 mm cloth behavior,
  Tg = 110 degC, editable commercial inputs, controlled-formula rules, and
  protected workbook structure.
- Update application text, README, Instructions, acceptance generator, and
  deployment checks to use the new names.
- Previously downloaded controlled five-, six-, and seven-sheet workbooks remain
  upgradeable subject to their existing structural validation rules.

## Output data and auditability

Both calculators expose enough information to distinguish the two routes:

- canonical mechanism name;
- calculation method/basis;
- allowable steel stress `S_allow` where applicable;
- substrate allowable pressure `p_s`;
- composite pressure deficit;
- governing hoop, axial, component, or minimum-thickness result.

For `Dent w/crack`, `S_allow` may be omitted or blank because no component-pipe
credit is claimed, while `p_s` is explicitly zero. For `Dent no-crack`, the
calculated values are reported even when the minimum-thickness floor controls.

## Validation and error handling

- Existing OD, wall, remaining-wall, SMYS, design-factor, temperature, pressure,
  and design-life validation remains in force.
- Internal dent selections and external dent rows below 1 mm remaining wall
  follow Type B without attempting the component-pipe formula.
- A legacy `Dent` value is never interpreted as `Dent no-crack`.
- Unsupported mechanism strings remain actionable input errors.
- Unexpected processing failures remain isolated to their source row in
  Calcbatch and must not expose customer input values in logs.

## Test strategy

Implementation follows test-driven development in each repository.

### v1.1 tests

- New selector values and removal of generic `Dent`.
- Legacy normalization helper behavior where used by shared engine tests.
- `Dent w/crack` numerical parity with the current generic dent vector.
- `Dent no-crack` exact `S_allow` and `p_s` calculations.
- Full-pressure versus load-sharing Formula 5 behavior.
- `p_s >= p_design` still applies minimum and active axial/component checks.
- Internal and below-1-mm dent routes remain Type B.
- Optional Type A / Class 3 check receives the same route-specific `p_s`.
- Report wording and displayed calculation basis.
- Complete existing v1.1 regression suite.

### Calcbatch tests

- Controlled template dropdown contains the two new names and not generic
  `Dent`.
- New rows validate and reach the engine with canonical mechanisms.
- Legacy `Dent` uploads calculate as `Dent w/crack` and regenerate with the new
  name.
- Batch result, Cost Calculation mapping, Summary, and acceptance workbook use
  normalized values consistently.
- Representative rows demonstrate both dent routes and the existing statuses.
- Safe re-upload of a processed seven-sheet workbook retains the mechanism and
  commercial assumptions.
- Complete existing Calcbatch regression suite and a live download/upload test.

## Release sequence

1. Implement the approved v1.1 change on a dedicated branch from its current
   main revision.
2. Run focused red/green tests, the complete v1.1 suite, and a local Streamlit
   smoke test.
3. Publish and verify the v1.1 deployment independently.
4. Port the approved engine change into a dedicated Calcbatch branch.
5. Regenerate and inspect the controlled template and processed acceptance
   workbook, including the Cost Calculation sheet.
6. Run the complete Calcbatch suite and local Streamlit smoke test.
7. Publish and verify the Calcbatch deployment independently.
8. Confirm both URLs still load their own calculators and that neither release
   altered the other application's repository or configuration.

## Out of scope

This change does not add a dedicated dent-integrity assessment. Dent depth,
percentage of OD, local dent strain, ovalization, fatigue cycles, weld/gouge
interaction, and dent acceptance criteria remain outside the calculator. The
new mechanism names select the approved composite-repair load-sharing basis;
they do not by themselves establish that a dent is acceptable for repair.
