# Pinned calculation-engine source

**Batch release version:** `1.0.0`

The calculation engine in this repository was copied from
[`Prowrap110/Iso24817Calcv1.1`](https://github.com/Prowrap110/Iso24817Calcv1.1)
at commit `68e5409` on 2026-08-14.

The copied modules are:

- `b31g.py`
- `iso24817_typea_class3.py`
- `prowrap_calculations.py`
- `prowrap_materials.py`

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
- Apply the user-approved PRW110 material basis of Tg = 110 degC. Derive the
  general qualified design limit as Tg - 20 = 90 degC and the Class 3 Type B
  limit for service longer than two years as Tg - 30 = 80 degC.
- Treat both 300 mm and 500 mm Prowrap CF cloth widths as approved batch
  configurations while retaining the fixed 50 mm stitching overlap.

All batch orchestration, workbook validation, warning-register handling,
status handling, and batch user-interface code is batch-repository-only. The
separately authorized v1.1 release receives only the Tg 110 degC material-basis
change and its derived temperature behavior.
