# CalcBatch v1.2 compact workbook release verification

## Scope

This release changes only the separate public **PROWRAP CalcBatch v1.2**
project. The v1.1 single-case calculator and the earlier CalcBatch project are
outside this release and remain unchanged.

The supported upload contract is the current 150/150 CalcBatch v1.2 template
and its processed-workbook re-upload path. Older 500/2,000-row templates are
not supported or guaranteed.

## Released workbook contract

- `Batch Input & Results` retains the 20 controlled inputs and has exactly nine
  outputs, in this order: Wall Loss [%], Required Structural Thickness [mm],
  Installed Plies, Total Repair Length [mm], Cloth Band Count, Procurement
  Axial Length [mm], Fabric Area [m2], Epoxy Mass [kg], and Repair Zone Length
  [mm]. The controlled table and filter range is `A1:AC151`.
- `Individual Defects` accepts at most 150 populated detail rows. Its table and
  filter range is `A1:X151`.
- `Cost Calculation` retains the semantic 20-field source mapping and ends with
  Cost, Price, Quantity, and Total Amount. Quantity is the highlighted,
  unlocked, blank-or-non-negative input in column W. Total Amount is the locked
  blank-safe formula `Price x Quantity` in column X.
- A maximum populated six-row acceptance output contains formulas only in Cost
  Calculation `U6:V11` and `X6:X11`. The downloaded blank input template has no
  formulas.
- No repair-design equation, engine constant, or status-classification rule
  changed in this release.

## Automated verification

The final implementation state before artifact generation passed:

```text
python3 -m pytest -q
316 passed in 72.04s
```

Task-level RED/GREEN evidence and independent reviews are recorded under
`.superpowers/sdd/2026-08-20-calcbatch-v12-compact-output-cost-150/`.

## Final workbook artifacts

The spreadsheet artifact-operation marker succeeded exactly once immediately
before production generation, with operation `create`, two expected outputs,
and format `xlsx`. It was not rerun.

Both files were generated through the production template/processor paths at
fixed UTC `2026-08-20T12:00:00Z`:

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `PROWRAP_CalcBatch_v1.2_Template.xlsx` | 49,430 | `924adfeed44f8bc3ee7922ea4ca3007e3521b4aceffc54d3294f567c9e032d68` |
| `PROWRAP_CalcBatch_v1.2_Processed.xlsx` | 52,956 | `66c1a9062f5c310585c6a17c54fe0a5dfca8dfecb3b877046829e3768a77e092` |

The representative processed workbook contains six main rows in this order:
Actual defect length, Independent defects, valid Enter manually, deliberately
invalid Enter manually, Dent no-crack, and Dent w/crack. Status counts are
three `REVIEW REQUIRED`, one `INPUT ERROR`, and two `OK`. The main sheet emits
only the nine released outputs; warning and status detail remain available in
Warnings, Summary, and Individual Defects.

## Structural, formula, and re-upload checks

- Exact eight-sheet order: Batch Information, Batch Input & Results,
  Individual Defects, Cost Calculation, Warnings, Summary, Instructions, Lists.
  Lists is hidden.
- Main/detail/Cost sheets are protected; editable inputs are unlocked and
  calculated outputs are locked. Main and detail filters remain usable.
- Main and detail table/filter pairs are exactly `A1:AC151` and `A1:X151`.
- Quantity validation covers `W6:W155`; processed acceptance Quantity values
  are blank in the delivered file.
- The input template has zero formulas. The processed acceptance workbook has
  exactly 18 formulas: six Cost, six Price, and six Total Amount formulas, with
  no formula-error cells.
- Processed-workbook re-upload retains valid commercial assumptions and
  Quantity inputs, while rebuilding all controlled sheets, formulas, results,
  warnings, and protections from the trusted current template.

## Commercial recalculation

A temporary non-delivered workbook used CF Cost / m2 = 25, Epoxy Cost / kg =
8, Price Multiplier = 1.4, and row quantities 1, 2, 0, 3, 1.5, and 4. It was
re-uploaded through the production processor and recalculated with LibreOffice.
All calculable Cost, Price, and Total Amount values matched direct arithmetic
within `1e-8`; the deliberately invalid engineering row remained blank.

Representative Total Amount results were 3,710.726594643066; 4,329.181027083579;
0; 156.546278211504; and 2,504.740451384072 for the five calculable rows.

## Visual inspection

Both workbooks were imported with the spreadsheet artifact runtime. Every one
of the eight sheets in each workbook was rendered and inspected. The compact
main header set, 150-row tables, highlighted common/commercial/Quantity inputs,
detail error wrapping, warning register, Summary, Instructions, and hidden list
content are readable and consistently formatted. No clipped critical label,
formula error, blank unintended sheet, or visual release defect was found.

The independent whole-branch review found one stale instruction that still
referred to a removed main warning-code column. A failing real-template
regression reproduced it. The Instructions sheet and README now direct users
to the Warnings register and app validation preview; both artifacts were
regenerated without rerunning the marker, rechecked structurally and
arithmetically, and the revised Instructions sheet was rendered again.

## Public release

The reviewed release implementation commit
`5a061ebac77c36a6629db5202555c83643ef55a7` was pushed to the public GitHub
repository with GitHub Desktop. A direct remote-branch check returned the exact
same SHA for `feature/linked-corrosion-v12`.

The Streamlit dashboard confirmed that only
`iso24817calcbatch-prowrapv12.streamlit.app` is configured from repository
`iso24817calcbatch-v1.2`, branch `feature/linked-corrosion-v12`, entry point
`app.py`. That app alone was rebooted. The separate v1.1 and earlier CalcBatch
deployments were not changed.

Live verification at
`https://iso24817calcbatch-prowrapv12.streamlit.app` confirmed the 150/150
guidance and Quantity/Total Amount contract. The public template download had
the exact `A1:AC151` compact main table, the exact nine outputs, the four-field
Cost/Price/Quantity/Total Amount tail, and zero formulas. A six-row controlled
workbook then uploaded successfully, calculated to two `OK`, three
`REVIEW REQUIRED`, one `INPUT ERROR`, zero `NOT REPAIRABLE`, and zero
`SYSTEM ERROR`, and downloaded a processed workbook. That live result retained
the exact nine outputs and contained exactly 18 controlled formulas in Cost
columns U, V, and X. Re-uploading the downloaded result was accepted and
recalculated to the same status counts.
