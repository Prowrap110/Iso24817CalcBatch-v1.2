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

All other batch orchestration, workbook validation, status handling, and user
interface code is batch-repository-only. The source repository remains
read-only.
