# PROWRAP CalcBatch v1.2 Linked Corrosion Defect Design

**Date:** 2026-08-20

**Status:** Approved in conversation for specification and planning

**Target:** New `Iso24817CalcBatch-v1.2` repository and application

**Batch source baseline:** current CalcBatch commit
`cb4526fc474bfa510205e8b28eebe26cf3a1e951`

**Calculation source baseline:** verified `Iso24817Calcv1.2` commit
`91b68d64508a4786934f0e17f2aea0dbebf745a7`

## 1. Objective

Create a separate Excel upload/download batch calculator that exposes the
three verified v1.2 external-corrosion defect-length modes while preserving
one main result row for each continuous composite repair:

1. `Actual defect length`;
2. `Independent defects`;
3. `Enter manually`.

Manual individual defects are stored in a normalized `Individual Defects`
worksheet and linked to one main repair row through a user-entered, stable
`Repair Group ID`. The calculation may assess several B31G candidates, but
repair length, material quantities, cost, price, and final status remain one
set of results per continuous repair.

## 2. Isolation and release boundary

The current CalcBatch repository, GitHub repository, Streamlit application,
URL, workbook contract, and calculation behavior shall remain unchanged. The
existing v1.1 and v1.2 single-calculation applications shall also remain
unchanged.

All work shall occur only in the new `Iso24817CalcBatch-v1.2` repository. Its
product title is `PROWRAP CalcBatch v1.2`. It shall have a separate GitHub
repository and, if later approved, a separate Streamlit application and URL.
It shall never deploy over the current CalcBatch application.

Creating and verifying the repository does not authorize Streamlit
deployment. Deployment is a later, separately approved release action.

## 3. Source and calculation integrity

The new project starts from the tracked current CalcBatch baseline so it
retains the existing guided template/upload/preview/calculate/download flow,
status model, warning register, cost sheet, workbook controls, file limits,
and batch-only safety behavior.

The v1.2 corrosion model shall be ported from the verified calculation source,
including paired manual defects, the 10 mm independent-defect B31G length,
stable governing selection, actual B31G method reporting, and separate repair
zone versus B31G lengths.

The port shall retain intentional current batch behavior, including:

- Tg and qualified product temperature basis of 110 degC;
- high-temperature results becoming `REVIEW REQUIRED` in the batch route;
- approved 300 mm and 500 mm cloth configurations;
- batch warning codes and separate `Warnings` sheet;
- `Dent w/crack` and `Dent no-crack` behavior;
- zero-pressure and optional Type A / Class 3 batch handling;
- formula-free input templates and the controlled processed-workbook cost
  formulas.

`ENGINE_SOURCE.md` shall identify both source revisions and document every
intentional batch-only difference from the v1.2 source.

## 4. Workbook structure

The controlled CalcBatch-v1.2 workbook contains these eight sheets in this
exact order:

1. `Batch Information`;
2. `Batch Input & Results`;
3. `Individual Defects`;
4. `Cost Calculation`;
5. `Warnings`;
6. `Summary`;
7. `Instructions`;
8. `Lists` (hidden).

The current common fields remain on `Batch Information` and apply to every
main repair row:

- Customer;
- Project Location;
- Report No.

Pipe OD remains an input in each `Batch Input & Results` row.

### 4.1 Main input table

The main table remains one row per continuous repair. Insert these inputs
immediately after `Defect Length [mm]`:

1. `Defect Length Basis`;
2. `Repair Group ID`;
3. existing `Remaining Wall [mm]`.

`Defect Length Basis` has the exact choices:

- `Actual defect length`;
- `Independent defects`;
- `Enter manually`.

For external corrosion, the basis is required. For other mechanisms and
locations it shall be blank and the existing route is used.

`Repair Group ID` is required only for external corrosion using
`Enter manually`. It must be unique among populated main manual-mode rows. It
shall be blank for the other two modes and for noneligible mechanisms.

`Remaining Wall [mm]` is required for `Actual defect length` and
`Independent defects`. It shall be blank for `Enter manually`, because the
individual values come from the linked detail table.

### 4.2 Individual Defects table

The new sheet is a controlled table with up to 2,000 detail rows. Its unlocked
input columns are:

| Input column | Requirement |
|---|---|
| Repair Group ID | required; must link to exactly one populated manual-mode main row |
| Defect ID | required and unique within the Repair Group ID |
| Individual longitudinal length [mm] | finite number greater than zero and no greater than the linked repair-zone span |
| Remaining wall [mm] | finite number from zero through the linked nominal wall |
| Separation exceeds 3t | exact `Yes` confirmation required |

The detail table has protected result columns:

| Result column | Meaning |
|---|---|
| Source Excel Row | original row number on `Individual Defects` |
| Calculation Status | `OK` or `INPUT ERROR` for this detail row |
| Error Code | stable row-level code |
| Error Message | user-actionable correction |
| B31G Method | actual method returned by the assessment |
| B31G Applicable | whether B31G pressure credit is eligible |
| B31G Acceptable | whether the pipe alone is acceptable at design pressure |
| Credited Safe Pressure [bar] | pressure credited to this candidate, or zero when inapplicable |
| Governing Defect | `Yes` only for the first lowest credited candidate |
| Assessment Warning Codes | warning references resolved on `Warnings` |

Completely blank detail rows are ignored. Partially populated detail rows are
input errors. An orphan detail row is marked `INPUT ERROR` without preventing
unrelated valid main rows from calculating.

### 4.3 Main output additions

Add protected result columns to `Batch Input & Results` for:

- `Repair Zone Length [mm]`;
- `3t Interaction Threshold [mm]`;
- `B31G Candidate Count`;
- `Governing Defect ID`;
- `Governing B31G Length [mm]`;
- `Governing B31G Remaining Wall [mm]`.

The existing `B31G Detail` diagnostic output retains the complete individual
assessment collection for auditability. Long explanations remain in
`Instructions` and `Warnings`, not in the visually compact main table.

## 5. Calculation behavior

The three modes apply only when `Mechanism = Corrosion` and
`Defect Location = External`. All other rows retain the current batch route.

### 5.1 Actual defect length

- B31G length = main-row `Defect Length [mm]`;
- B31G remaining wall = main-row `Remaining Wall [mm]`;
- repair-zone span = main-row `Defect Length [mm]`;
- candidate count = one.

This is the explicit compatibility default and shall reproduce the current
batch numerical result.

### 5.2 Independent defects

- representative B31G length = 10 mm;
- representative circumferential width assumption = 10 mm;
- B31G remaining wall = main-row `Remaining Wall [mm]`;
- every defect is assumed separated from every other defect by more than
  `3t`, where `t` is nominal pipe wall;
- repair-zone span = main-row `Defect Length [mm]`;
- candidate count = one;
- governing ID = `Independent 10x10 mm defects`.

Selecting this mode is the user's affirmative confirmation of the permanent
10 x 10 mm and greater-than-3t assumptions. The assumptions are shown in
`Instructions` and the processed result, but they are not compliance warnings
by themselves.

### 5.3 Enter manually

The processor joins detail rows to the main row by exact trimmed
`Repair Group ID`. Each complete linked row becomes one paired B31G candidate;
length from one defect shall never be combined with remaining wall from
another.

Every candidate is assessed independently using the verified v1.2 B31G
method, safety factor, high-SMYS Original B31G fallback, and applicability
rules. Credited pressure is the calculated safe pressure when eligible and
zero when inapplicable or when remaining wall is below 1 mm.

The governing candidate is the first candidate in worksheet order having the
lowest credited pressure. Its credited pressure controls the existing ISO
24817 substrate load-sharing calculation. The overall minimum linked
remaining wall is retained for wall-loss, no-substrate-capacity, and optional
Type A / Class 3 supporting checks.

### 5.4 Continuous repair and commercial results

For every mode:

```text
total repair length
  = complete main-row repair-zone span
  + 2 x required terminal overlap
  + 2 x taper length
```

The complete main-row repair-zone span controls band count, procurement axial
length, fabric area, epoxy mass, cost, and price. A 10 mm independent B31G
length or an individual manual B31G length shall never shorten the continuous
repair coverage.

The `Cost Calculation` sheet remains one row per main repair row and maps
fields by semantic header name rather than fixed column letter, so the new
main inputs and outputs do not corrupt cost formulas.

## 6. Validation and status behavior

The existing row-continuation statuses remain:

- `OK`;
- `REVIEW REQUIRED`;
- `NOT REPAIRABLE`;
- `INPUT ERROR`;
- `SYSTEM ERROR`.

A manual main row becomes `INPUT ERROR` when its group is missing, duplicated,
has no complete detail rows, or contains any invalid linked detail row.
Unrelated valid rows continue to calculate.

The processor rejects or marks safely:

- missing basis for eligible external corrosion;
- a basis entered on an ineligible mechanism/location;
- independent repair-zone span below 10 mm;
- missing or stray Repair Group IDs;
- duplicate manual main Repair Group IDs;
- orphan detail Repair Group IDs;
- duplicate or blank Defect IDs within a group;
- blank, false, or non-`Yes` separation confirmations;
- nonnumeric, nonfinite, zero, negative, or over-span lengths;
- remaining wall below zero or above linked nominal wall;
- partial detail rows;
- formulas or formula objects in controlled user-input cells.

Only structural workbook failures stop the entire batch. User data problems
remain localized to the affected main/detail rows whenever an unambiguous row
association exists.

## 7. Legacy workbook upgrade

CalcBatch-v1.2 accepts the exact current seven-sheet CalcBatch workbook as a
legacy input. It shall not make the current CalcBatch application accept the
new format.

On upload, the v1.2 processor rebuilds the result from its trusted eight-sheet
template and copies legacy data by exact header name. For every populated
legacy external-corrosion row it sets:

- `Defect Length Basis = Actual defect length`;
- blank `Repair Group ID`;
- no individual-detail rows.

Other legacy mechanisms keep a blank basis. Legacy rows must reproduce their
current calculation outputs, statuses, warnings, costs, and prices. The
processed download is always the current eight-sheet CalcBatch-v1.2 format.

Current processed seven-sheet workbooks with the controlled cost formulas are
also accepted and upgraded through the same trusted-template boundary. No
uploaded formula is copied into the new output.

## 8. Streamlit workflow

The existing user-friendly workflow remains:

1. enter common batch information once;
2. download the controlled blank template;
3. fill one main row per repair and, when required, linked individual defects;
4. upload and inspect recognized, missing, and unexpected columns;
5. preview row counts and input problems;
6. calculate valid rows while preserving row-level errors;
7. download the processed workbook.

The upload preview adds:

- count of populated main repair rows;
- count of populated individual-defect rows;
- count of manual repair groups;
- recognized/missing/unexpected headings for both controlled input tables.

No customer workbook is sent to an external service by the application.

## 9. Instructions and usability

The workbook instructions shall contain a compact mode table explaining:

- when each defect-length basis applies;
- that `t` means nominal wall thickness;
- that `Defect Length [mm]` remains the outer-to-outer continuous repair-zone
  span for Independent and Manual modes;
- that the main Remaining Wall is blank in Manual mode;
- how Repair Group IDs link the two tables;
- that greater-than-3t separation is an engineering confirmation, not a value
  inferred by the calculator;
- that interacting defects must instead be combined and entered under
  `Actual defect length`.

Input cells remain visibly highlighted, unlocked, selectable, filterable, and
validated. Output cells remain protected. The first data row stays frozen in
both tables. Long instruction text shall be rendered and visually checked for
clipping.

## 10. Test and acceptance requirements

Automated tests shall cover at least:

1. exact current CalcBatch numerical parity under `Actual defect length`;
2. Independent mode parity with a direct 10 mm v1.2 B31G candidate;
3. Independent mode retaining the complete repair span in length and material
   quantities;
4. Manual mode preserving each length/wall pair and selecting the first lowest
   credited pressure;
5. Manual mode not combining the longest defect with the lowest wall from
   another defect;
6. a nonapplicable manual candidate governing with zero substrate credit;
7. detail results mapping back to the correct Excel rows;
8. missing, duplicate, orphan, partial, out-of-range, and unconfirmed links;
9. row-local continuation when another repair group is invalid;
10. nonexternal-corrosion and dent routes remaining unchanged;
11. optional Type A / Class 3 receiving governing pressure and conservative
    minimum remaining wall;
12. exact eight-sheet order, controls, table/filter ranges, dropdowns, and
    hidden `Lists` state;
13. exact legacy seven-sheet upgrade with `Actual defect length` default;
14. formula-free blank template and controlled processed cost formulas only;
15. semantic cost mapping after the new columns;
16. processed-workbook re-upload producing identical calculations;
17. maximum 500 main rows and maximum 2,000 detail rows;
18. Streamlit upload, preview, calculate, and download behavior;
19. engine-source/provenance snapshot checks;
20. the complete inherited and new regression suite.

The acceptance workbook shall contain representative rows for Actual,
Independent, and Manual external corrosion using the same pipe and overall
repair span so their B31G and ply results can be compared while continuous
repair coverage stays unchanged. It shall also include at least one invalid
manual group, one unchanged dent route, and one 500 mm cloth case.

Final acceptance requires:

- a fresh complete green test suite;
- a generated blank template and processed acceptance workbook;
- formula and control inspection;
- numerical reconciliation against direct v1.2 engine calls;
- clean processed-workbook re-upload;
- visual inspection of all eight sheets;
- proof that the current CalcBatch and v1.1 repositories were not modified.

## 11. Publishing boundary

After acceptance, the repository may be published as a new private GitHub
repository through GitHub Desktop only after the user approves that release
action. A pull request may be created separately if requested. Streamlit
deployment remains a distinct action requiring a new application and URL and
shall not occur without explicit approval.
