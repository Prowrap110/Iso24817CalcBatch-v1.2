# Pinned calculation-engine source

**Batch release version:** `1.2.0`

The calculation engine in this repository was copied from
[`Prowrap110/Iso24817Calcv1.1`](https://github.com/Prowrap110/Iso24817Calcv1.1)
at released merge commit `746f3b3d65d73a2836962126e76f880919c51d0d`
on 2026-08-15. That release commit contains the reviewed dent-split feature
head `7ca0e66ab4f8334fe07fda54b64599f54b1a1256`; the calculation modules ported
here use that approved source behavior. Processed workbooks record the short
released revision `746f3b3`.

The copied modules are:

- `b31g.py`
- `iso24817_typea_class3.py`
- `prowrap_calculations.py`
- `prowrap_materials.py`
- `prowrap_mechanisms.py`

## Approved dent mechanism split

The former generic `Dent` engine route is split into two canonical mechanisms:

- `Dent w/crack` retains the conservative full-pressure laminate design and
  receives zero substrate pressure credit.
- Eligible external `Dent no-crack` repairs with at least 1 mm remaining wall
  use component-pipe load sharing:

  ```text
  S_allow = SMYS * Design Factor
  p_s = 2 * S_allow * t_remaining / OD
  p_composite = max(0, p_design - p_s)
  ```

Internal dents and external dents below 1 mm remaining wall retain the Type B
full-replacement route and zero substrate credit. B31G remains corrosion-only.
Legacy `Dent` aliasing is deliberately not an engine formula: the batch upload
boundary maps that exact legacy value conservatively to `Dent w/crack` before
the canonical mechanism reaches the engine.

## Approved batch material-basis change

The user-approved PRW110 material basis in this batch release is Tg = 110 degC.
It derives the general qualified design limit as Tg - 20 = 90 degC and the
Class 3 Type B limit for service longer than two years as Tg - 30 = 80 degC.
This batch release does not change or redeploy the separate v1.1 calculator.

## Intentional batch-only corrections

The following corrections were made only in this separate batch repository.
They do not modify the source repository or the existing v1.1 deployment.

- Strictly reject unsupported defect mechanisms, defect locations, and axial
  load cases before calculation.
- Safely handle a zero-design-pressure Type B case without dereferencing absent
  Formula 12 detail; retain the impact-qualified three-ply minimum and require
  engineering review.
- Use the configured PRW110 Type B two-year service-life limit consistently,
  including zero-pressure Type B warnings.
- Keep the copied engine strict by default for design temperatures above the
  qualified Prowrap limit.  The batch adapter alone opts into numeric
  screening outputs through `allow_unqualified_temperature=True`, adds an
  explicit qualification warning, and returns `REVIEW REQUIRED`; non-batch
  callers retain the strict input rejection.
- Treat both 300 mm and 500 mm Prowrap CF cloth widths as approved batch
  configurations while retaining the fixed 50 mm stitching overlap.
- Keep unexpected row failures isolated as `SYSTEM ERROR` results while
  recording bounded exception type and traceback-frame diagnostics in server
  logs without exposing those internals in the processed workbook.

All batch orchestration, workbook validation, warning-register handling,
status handling, and batch user-interface code is batch-repository-only. The
existing v1.1 repository, application, URL, and deployment remain outside this
release scope.
