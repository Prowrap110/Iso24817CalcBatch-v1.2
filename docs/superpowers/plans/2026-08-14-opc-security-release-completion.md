# PROWRAP Batch OPC Security Release Completion Implementation Plan

> **Superseded:** The user confirmed that this is a trusted personal workbook workflow. Continue with `2026-08-14-trusted-workbook-release.md`; do not execute further tasks from this plan.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the blocked OPC worksheet resolver, fix filename-sensitive Streamlit result identity, regenerate the controlled acceptance workbook, and publish a verified batch-only Streamlit release.

**Architecture:** A new `opc_package.py` module owns bounded OPC content-type resolution and worksheet-cell counting before openpyxl is called. `workbook_processor.py` converts its safe exceptions into workbook validation issues, while `app.py` keys processed results by both uploaded bytes and exact filename. Acceptance and live deployment remain separate release gates.

**Tech Stack:** Python 3.11, Streamlit 1.x, openpyxl 3.1.x, pytest, OOXML/OPC ZIP packages, `@oai/artifact-tool`, LibreOffice headless, GitHub, Streamlit Community Cloud.

## Global Constraints

- Modify only `Prowrap110/Iso24817CalcBatch`; never modify or redeploy the existing v1.1 repository or application.
- The aggregate worksheet-cell ceiling is exactly 100,000 cells; 100,000 passes and 100,001 fails before openpyxl.
- Recognize both Transitional `http://schemas.openxmlformats.org/spreadsheetml/2006/main` and ISO Strict `http://purl.oclc.org/ooxml/spreadsheetml/main` worksheet namespaces.
- Resolve OPC content types with ASCII-case-insensitive part and extension comparison, rightmost-dot Default extension extraction, and part-specific Override precedence.
- Reject case-insensitive duplicate ZIP part names as ambiguous.
- Only effective worksheet content types enter worksheet XML scanning; foreign and binary parts are not worksheet-parsed.
- Keep the exact seven-sheet current output, five-/six-sheet upgrade compatibility, controlled formula allowlist, 500-row limit, warning separation, 500 mm cloth behavior, and Tg 110 degC behavior unchanged.
- Streamlit result identity includes both the uploaded XLSX bytes and exact uploaded filename.
- Keep unexpected exception text and customer/input values out of server logs.
- Pin openpyxl to `>=3.1,<3.2`.
- Publish only after the full suite, acceptance artifact review, whole-branch review, and live batch URL test are clean.

---

## File Responsibility Map

- Create `opc_package.py`: OPC manifest resolution, archive-name canonicalization, worksheet selection, XML namespace verification, and bounded cell counting.
- Create `tests/opc_fixtures.py`: reusable test-only OPC package builders and controlled-workbook relocation helper.
- Create `tests/test_opc_package.py`: pure package-policy conformance and boundary tests.
- Modify `workbook_processor.py`: call `opc_package.enforce_worksheet_cell_limit` before openpyxl and remove the superseded inline manifest resolver.
- Modify `tests/test_workbook_processor.py`: public pre-openpyxl integration and controlled-workbook regressions.
- Modify `app.py`: filename-sensitive upload/result identity and accurate formula-upload help.
- Modify `tests/test_app_smoke.py`: identical-bytes/different-name result invalidation and source-name traceability.
- Modify `workbook_template.py`: retained-value wording and integer display formats.
- Modify `tests/test_workbook_template.py`: exact guidance and display-format assertions.
- Modify `requirements.txt`: tested openpyxl boundary.
- Regenerate `/Users/can/Documents/Codex/2026-08-14/i/outputs/PROWRAP_Batch_Cost_Calculation_Acceptance.xlsx` only after the last workbook or processor commit.

---

### Task 1: Standards-Compliant OPC Package Policy

**Files:**
- Create: `opc_package.py`
- Create: `tests/opc_fixtures.py`
- Create: `tests/test_opc_package.py`

**Interfaces:**
- Produces: `class OpcPackageError(ValueError)` containing only safe generic messages.
- Produces: `worksheet_part_names(archive: zipfile.ZipFile) -> frozenset[str]` returning exact archive spellings.
- Produces: `enforce_worksheet_cell_limit(archive: zipfile.ZipFile, *, max_cells: int) -> int` returning the accepted aggregate cell count or raising `OpcPackageError`.
- Consumes later: Task 2 imports `OpcPackageError` and `enforce_worksheet_cell_limit`.

- [ ] **Step 1: Add deterministic OPC fixture utilities**

Create test-only helpers in `tests/opc_fixtures.py` with these exact contracts:

```python
def package_bytes(parts: dict[str, bytes]) -> bytes:
    """Write exact ZIP member names and bytes into one in-memory package."""

def content_types_xml(
    *, defaults: Sequence[tuple[str, str]] = (),
    overrides: Sequence[tuple[str, str]] = (),
) -> bytes:
    """Return a valid OPC Types manifest in the package content-types namespace."""

def worksheet_xml(cell_count: int, namespace: str) -> bytes:
    """Return one worksheet root with exactly cell_count same-namespace c elements."""

def relocated_controlled_workbook(
    source: bytes,
    *,
    source_part: str,
    destination_part: str,
    worksheet_bytes: bytes,
    default_declarations: Sequence[tuple[str, str]] = (),
    override_declarations: Sequence[tuple[str, str]] = (),
) -> bytes:
    """Move one relationship-valid worksheet, update its target and content types, and return XLSX bytes."""

def dense_controlled_variant(source: bytes, variant: str, cell_count: int) -> bytes:
    """Return one of the four named relationship-valid dense worksheet variants used by Task 2."""

def controlled_package_with_duplicate_parts(source: bytes, first: str, second: str) -> bytes:
    """Add two case-colliding package parts while preserving the controlled workbook."""

def controlled_package_with_custom_part(
    source: bytes,
    *,
    part_name: str,
    part_bytes: bytes,
    default_declarations: Sequence[tuple[str, str]] = (),
    override_declarations: Sequence[tuple[str, str]] = (),
) -> bytes:
    """Add one unreferenced custom package part and its content-type declarations."""
```

`dense_controlled_variant` uses these exact mappings and removes the superseded original worksheet Override before adding the new declaration:

| Variant | Destination | Namespace | Declaration |
|---|---|---|---|
| `case_variant_override` | `xl/custom/dense.data` | Transitional | Override `/XL/CUSTOM/DENSE.DATA` = worksheet |
| `dot_prefixed_default` | `xl/custom/.data` | Transitional | Default `DATA` = worksheet |
| `non_xml_suffix_override` | `xl/custom/dense.data` | Transitional | Override `/xl/custom/dense.data` = worksheet |
| `strict_namespace_override` | `xl/custom/dense.strictdata` | ISO Strict | Override `/xl/custom/dense.strictdata` = worksheet |

All relocation helpers rewrite the workbook relationship target relative to `xl/workbook.xml`, remove the old ZIP member, preserve every unrelated member byte-for-byte, and update `[Content_Types].xml` in its package namespace.

Use literal content types:

```python
WORKSHEET = 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'
BINARY = 'application/octet-stream'
TRANSITIONAL = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
STRICT = 'http://purl.oclc.org/ooxml/spreadsheetml/main'
```

- [ ] **Step 2: Write failing content-type resolution tests**

Add a parameterized test whose literal cases are:

```python
@pytest.mark.parametrize(('part_name', 'defaults', 'overrides', 'selected'), [
    ('xl/custom/dense.data', (), (('/XL/CUSTOM/DENSE.DATA', WORKSHEET),), True),
    ('xl/custom/.data', (('DATA', WORKSHEET),), (), True),
    ('xl/custom/blob.data', (('data', WORKSHEET),),
        (('/xl/custom/blob.data', BINARY),), False),
    ('xl/custom/blob.data', (('data', BINARY),),
        (('/XL/CUSTOM/BLOB.DATA', WORKSHEET),), True),
])
def test_effective_content_type_obeys_case_extension_and_override_precedence(
    part_name, defaults, overrides, selected,
):
    data = package_bytes({
        '[Content_Types].xml': content_types_xml(
            defaults=defaults,
            overrides=overrides,
        ),
        part_name: worksheet_xml(1, TRANSITIONAL),
    })
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = worksheet_part_names(archive)
    assert (part_name in names) is selected
```

Add separate failing tests proving:

```python
def test_case_insensitive_duplicate_archive_parts_are_rejected():
    data = package_bytes({
        '[Content_Types].xml': content_types_xml(
            overrides=(('/xl/custom/a.data', WORKSHEET),),
        ),
        'xl/custom/A.data': worksheet_xml(1, TRANSITIONAL),
        'xl/custom/a.data': worksheet_xml(1, TRANSITIONAL),
    })
    with zipfile.ZipFile(BytesIO(data)) as archive:
        with pytest.raises(OpcPackageError, match='ambiguous'):
            worksheet_part_names(archive)

@pytest.mark.parametrize('manifest', [
    content_types_xml(defaults=(('data', WORKSHEET), ('DATA', BINARY))),
    content_types_xml(overrides=(
        ('/xl/custom/a.data', WORKSHEET),
        ('/XL/CUSTOM/A.DATA', BINARY),
    )),
])
def test_duplicate_default_or_override_declarations_are_rejected(manifest):
    data = package_bytes({
        '[Content_Types].xml': manifest,
        'xl/custom/a.data': worksheet_xml(1, TRANSITIONAL),
    })
    with zipfile.ZipFile(BytesIO(data)) as archive:
        with pytest.raises(OpcPackageError, match='ambiguous'):
            worksheet_part_names(archive)

@pytest.mark.parametrize('parts', [
    {'xl/custom/a.data': worksheet_xml(1, TRANSITIONAL)},
    {'[Content_Types].xml': b'<Types>',
     'xl/custom/a.data': worksheet_xml(1, TRANSITIONAL)},
])
def test_missing_or_malformed_content_types_manifest_is_rejected(parts):
    with zipfile.ZipFile(BytesIO(package_bytes(parts))) as archive:
        with pytest.raises(OpcPackageError, match='content type'):
            worksheet_part_names(archive)
```

Each test asserts either the exact selected archive spelling or a safe `OpcPackageError` without package/customer content.

- [ ] **Step 3: Run the resolution tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_opc_package.py -k 'content_type or duplicate or manifest'
```

Expected: collection or assertion failures because `opc_package.py` and its interfaces do not exist.

- [ ] **Step 4: Implement canonical OPC content-type resolution**

Implement these private rules in `opc_package.py`:

```python
_ASCII_UPPER = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')

def _ascii_lower(value: str) -> str:
    return value.translate(_ASCII_UPPER)

def _part_key(value: str) -> str:
    return _ascii_lower(value.removeprefix('/'))

def _extension(part_name: str) -> str:
    head, separator, tail = part_name.rpartition('.')
    return _ascii_lower(tail) if separator else ''
```

Parse `[Content_Types].xml` only in
`http://schemas.openxmlformats.org/package/2006/content-types`. Build unique Default and Override maps. Build a unique case-insensitive entry index while preserving exact spellings. For each non-directory entry, choose Override first; otherwise choose Default by `_extension`. Return only exact names whose effective type is `WORKSHEET_CONTENT_TYPE`.

Reject missing manifests, encrypted manifests, namespace/root mismatches, duplicate declarations, missing worksheet Override targets, and case-insensitive duplicate entries with generic `OpcPackageError` messages.

- [ ] **Step 5: Run the resolution tests to GREEN**

Run the Step 3 command.

Expected: every selected resolution test passes.

- [ ] **Step 6: Write failing worksheet scanning and boundary tests**

Add literal tests for:

```python
def test_exact_worksheet_cell_boundary_accepts_100000_and_rejects_100001():
    accepted = package_bytes({
        '[Content_Types].xml': content_types_xml(
            overrides=(('/xl/custom/a.data', WORKSHEET),),
        ),
        'xl/custom/a.data': worksheet_xml(100_000, TRANSITIONAL),
    })
    rejected = package_bytes({
        '[Content_Types].xml': content_types_xml(
            overrides=(('/xl/custom/a.data', WORKSHEET),),
        ),
        'xl/custom/a.data': worksheet_xml(100_001, TRANSITIONAL),
    })
    with zipfile.ZipFile(BytesIO(accepted)) as archive:
        assert enforce_worksheet_cell_limit(archive, max_cells=100_000) == 100_000
    with zipfile.ZipFile(BytesIO(rejected)) as archive:
        with pytest.raises(OpcPackageError, match='too many worksheet cells'):
            enforce_worksheet_cell_limit(archive, max_cells=100_000)

@pytest.mark.parametrize('namespace', [TRANSITIONAL, STRICT])
def test_both_spreadsheetml_namespaces_are_counted(namespace):
    data = package_bytes({
        '[Content_Types].xml': content_types_xml(
            overrides=(('/xl/custom/a.data', WORKSHEET),),
        ),
        'xl/custom/a.data': worksheet_xml(7, namespace),
    })
    with zipfile.ZipFile(BytesIO(data)) as archive:
        assert enforce_worksheet_cell_limit(archive, max_cells=100_000) == 7

def test_foreign_root_and_foreign_nested_c_elements_do_not_count():
    real = (
        f'<worksheet xmlns="{TRANSITIONAL}" xmlns:f="urn:foreign">'
        '<sheetData><row><c r="A1"><v>1</v></c></row></sheetData>'
        '<extLst><ext uri="foreign"><f:c/><f:c/></ext></extLst>'
        '</worksheet>'
    ).encode()
    data = package_bytes({
        '[Content_Types].xml': content_types_xml(
            defaults=(('custom', 'application/xml'),),
            overrides=(('/xl/custom/a.data', WORKSHEET),),
        ),
        'xl/custom/a.data': real,
        'customXml/foreign.custom': b'<worksheet xmlns="urn:foreign"><c/><c/></worksheet>',
    })
    with zipfile.ZipFile(BytesIO(data)) as archive:
        assert enforce_worksheet_cell_limit(archive, max_cells=100_000) == 1

def test_unrelated_binary_part_is_never_xml_parsed(monkeypatch):
    data = package_bytes({
        '[Content_Types].xml': content_types_xml(
            defaults=(('data', BINARY),),
            overrides=(('/xl/custom/a.sheet', WORKSHEET),),
        ),
        'xl/custom/a.sheet': worksheet_xml(1, TRANSITIONAL),
        'custom/blob.data': b'\x00\xff\x00not-xml',
    })
    real_iterparse = opc_package.iterparse
    def guarded_iterparse(source, *args, **kwargs):
        assert getattr(source, 'name', '') != 'custom/blob.data'
        return real_iterparse(source, *args, **kwargs)
    monkeypatch.setattr(opc_package, 'iterparse', guarded_iterparse)
    with zipfile.ZipFile(BytesIO(data)) as archive:
        assert enforce_worksheet_cell_limit(archive, max_cells=100_000) == 1

def test_malformed_declared_worksheet_is_rejected():
    data = package_bytes({
        '[Content_Types].xml': content_types_xml(
            overrides=(('/xl/custom/a.data', WORKSHEET),),
        ),
        'xl/custom/a.data': f'<worksheet xmlns="{TRANSITIONAL}">'.encode(),
    })
    with zipfile.ZipFile(BytesIO(data)) as archive:
        with pytest.raises(OpcPackageError, match='malformed worksheet'):
            enforce_worksheet_cell_limit(archive, max_cells=100_000)
```

For the binary test, monkeypatch `xml.etree.ElementTree.iterparse` through the module boundary and fail if the binary entry stream is passed to it. For boundary tests, use one worksheet part selected by a valid Override.

- [ ] **Step 7: Run scanning tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_opc_package.py -k 'cell_boundary or spreadsheetml or foreign or binary or malformed_declared'
```

Expected: failures because cell scanning is not implemented.

- [ ] **Step 8: Implement bounded worksheet XML scanning**

For each selected exact archive entry:

```python
with archive.open(part_name) as stream:
    events = iterparse(stream, events=('start', 'end'))
```

Require the first start element to be `worksheet` in Transitional or Strict SpreadsheetML. Count only end events whose expanded name is `{root_namespace}c`, clear every completed element, and return immediately with `OpcPackageError('The uploaded workbook contains too many worksheet cells.')` when the aggregate exceeds `max_cells`.

Do not parse any unselected entry. Convert empty or malformed selected parts into `OpcPackageError('The uploaded workbook contains malformed worksheet data.')` without including part names.

- [ ] **Step 9: Run all Task 1 tests and regressions**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_opc_package.py
```

Expected: all Task 1 tests pass with clean output.

- [ ] **Step 10: Commit Task 1**

```bash
git add opc_package.py tests/opc_fixtures.py tests/test_opc_package.py
git commit -m "fix: resolve OPC worksheet parts safely"
```

---

### Task 2: Integrate OPC Limits Before openpyxl

**Files:**
- Modify: `workbook_processor.py`
- Modify: `tests/test_workbook_processor.py`

**Interfaces:**
- Consumes: `enforce_worksheet_cell_limit(archive, max_cells=100_000)` and `OpcPackageError` from Task 1.
- Preserves: `inspect_workbook(data: bytes) -> WorkbookInspection` and `process_workbook(data: bytes, processed_at: datetime | None = None, source_name: str | None = None) -> ProcessedBatch` public behavior.
- Produces: deterministic `UNREADABLE_WORKBOOK` issues before `load_workbook` for OPC/cell-policy failures.

- [ ] **Step 1: Write failing public pre-loader regressions**

Import `relocated_controlled_workbook`, `worksheet_xml`, `WORKSHEET`, `BINARY`, `TRANSITIONAL`, and `STRICT` from `tests.opc_fixtures`. Add a local fixture factory that starts from `workbook_bytes_with_rows([valid_row_values()])`, moves `xl/worksheets/sheet2.xml`, and returns a dense controlled package for each literal variant. Cover:

```python
@pytest.mark.parametrize('variant', [
    'case_variant_override',
    'dot_prefixed_default',
    'non_xml_suffix_override',
    'strict_namespace_override',
])
def test_dense_opc_variants_are_rejected_before_openpyxl(monkeypatch, variant):
    source = dense_controlled_variant(variant, cell_count=100_001)
    monkeypatch.setattr(
        workbook_processor,
        'load_workbook',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('openpyxl reached')),
    )
    inspection = inspect_workbook(source)
    assert [issue.code for issue in inspection.workbook_errors] == ['UNREADABLE_WORKBOOK']

def test_override_binary_suppresses_worksheet_default_without_false_rejection():
    source = controlled_package_with_custom_part(
        workbook_bytes_with_rows([valid_row_values()]),
        part_name='xl/custom/blob.data',
        part_bytes=b'\x00\xffbinary-custom-data',
        default_declarations=(('data', WORKSHEET),),
        override_declarations=(('/xl/custom/blob.data', BINARY),),
    )
    inspection = inspect_workbook(source)
    assert inspection.workbook_errors == ()

def test_case_insensitive_duplicate_zip_parts_are_rejected_before_openpyxl(monkeypatch):
    source = controlled_package_with_duplicate_parts('xl/custom/A.data', 'xl/custom/a.data')
    monkeypatch.setattr(
        workbook_processor,
        'load_workbook',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('openpyxl reached')),
    )
    inspection = inspect_workbook(source)
    assert [issue.code for issue in inspection.workbook_errors] == ['UNREADABLE_WORKBOOK']
```

For every dense case, monkeypatch `workbook_processor.load_workbook` with a function that raises `AssertionError('openpyxl reached')`. Assert the returned inspection contains exactly `UNREADABLE_WORKBOOK` and the assertion is never raised.

- [ ] **Step 2: Run public integration tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_workbook_processor.py \
  -k 'dense_opc_variants or override_binary or duplicate_zip_parts'
```

Expected: at least the three OPC edge variants reach the loader or select the wrong part under the superseded resolver.

- [ ] **Step 3: Replace the inline resolver with the Task 1 module**

In `_zip_safety_errors` keep the existing entry-count, expanded-byte, per-entry, and compression-ratio checks. Then call:

```python
try:
    enforce_worksheet_cell_limit(archive, max_cells=_MAX_WORKBOOK_CELLS)
except OpcPackageError as error:
    return (_issue('UNREADABLE_WORKBOOK', str(error)),)
```

Delete `_worksheet_part_names`, `_xml_expanded_name`, and resolver-only constants/imports from `workbook_processor.py`. Do not change formula, sparse-row, commercial, engineering, or logging behavior.

- [ ] **Step 4: Run public integration tests to GREEN**

Run the Step 2 command.

Expected: all selected tests pass.

- [ ] **Step 5: Run security and controlled-boundary regressions**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_opc_package.py tests/test_workbook_processor.py tests/test_cost_calculation.py
```

Then run the exact controlled boundary tests for 500 rows, sparse far cells, formula priority, ZIP expansion, logging redaction, legacy upgrades, and processed re-upload.

Expected: all tests pass; exact 500-row workbooks remain accepted.

- [ ] **Step 6: Commit Task 2**

```bash
git add workbook_processor.py tests/test_workbook_processor.py
git commit -m "fix: enforce OPC limits before workbook loading"
```

---

### Task 3: Filename-Sensitive Results and Final Workbook Guidance

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_smoke.py`
- Modify: `workbook_template.py`
- Modify: `tests/test_workbook_template.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `_source_identity(data: bytes, filename: str) -> str` in `app.py`.
- Preserves: current Streamlit stage layout and session-local workbook bytes.
- Produces: source-result cache invalidation when either content or filename changes.

- [ ] **Step 1: Write failing identity and AppTest regressions**

Add:

```python
def test_source_identity_changes_for_bytes_or_exact_filename():
    assert _source_identity(b'one', 'a.xlsx') != _source_identity(b'two', 'a.xlsx')
    assert _source_identity(b'one', 'a.xlsx') != _source_identity(b'one', 'b.xlsx')

def test_same_bytes_under_new_filename_clear_and_rebuild_source_traceability():
    source = workbook_bytes_with_rows([valid_row_values()])
    app = AppTest.from_file(APP_PATH).run()
    app.file_uploader[0].upload('first.xlsx', source, XLSX_MIME).run()
    calculate(app).click().run()
    assert processed_download_is_visible(app)

    app.file_uploader[0].upload('renamed-second.xlsx', source, XLSX_MIME).run()
    assert not processed_download_is_visible(app)

    calculate(app).click().run()
    processed = load_workbook(BytesIO(app.session_state['processed_workbook_bytes']))
    assert processed['Summary']['B7'].value == 'renamed-second.xlsx'
```

Use small local test helpers for the repeated button lookup; do not add helpers to production code.

- [ ] **Step 2: Run identity tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_app_smoke.py \
  -k 'source_identity or same_bytes_under_new_filename'
```

Expected: missing `_source_identity` or the old processed download remains visible.

- [ ] **Step 3: Implement filename-sensitive identity**

Add:

```python
def _source_identity(data: bytes, filename: str) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    digest.update(b'\0')
    digest.update(filename.encode('utf-8', errors='surrogatepass'))
    return digest.hexdigest()
```

Replace the bytes-only source hash with this identity everywhere session state compares or stores the current upload. Keep `_PROCESSED_HASH_KEY` for backward internal naming or rename both keys consistently in the same commit.

- [ ] **Step 4: Run identity tests to GREEN**

Run the Step 2 command.

Expected: both tests pass and the new source name is stored in the rebuilt workbook.

- [ ] **Step 5: Write failing guidance, format, and dependency assertions**

Add tests requiring:

```python
assert 'uncontrolled formulas' in upload_help.lower()
assert 'processed cost and price formulas' in upload_help.lower()
assert 'may be blank' in instructions['A10'].value.lower()
assert cost['J6'].number_format == '#,##0'
assert cost['O6'].number_format == '#,##0'
assert cost['Q6'].number_format == '#,##0'
```

Add a small requirements test or deployment assertion that reads `requirements.txt` and requires exactly one openpyxl constraint line equal to `openpyxl>=3.1,<3.2`.

- [ ] **Step 6: Run guidance tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_app_smoke.py tests/test_workbook_template.py
```

Expected: old help/guidance, two-decimal integer formats, and `<4` dependency fail their new assertions.

- [ ] **Step 7: Apply the exact user-facing and dependency corrections**

- Set uploader help to: `Upload one controlled .xlsx workbook, up to 10 MB. Macros and uncontrolled formulas are rejected; exact processed Cost and Price formulas are accepted on re-upload.`
- Change Instructions to say `B3, E3, and H3 may be blank or may retain values from a previously processed workbook.`
- Apply `#,##0` to Cost Calculation columns J, O, and Q for controlled data rows; keep stored numeric values unchanged.
- Change the openpyxl requirement to `openpyxl>=3.1,<3.2`.

- [ ] **Step 8: Run Task 3 and app/workbook regressions**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_app_smoke.py tests/test_workbook_template.py \
  tests/test_full_batch_acceptance.py
```

Expected: all tests pass.

- [ ] **Step 9: Commit Task 3**

```bash
git add app.py tests/test_app_smoke.py workbook_template.py \
  tests/test_workbook_template.py requirements.txt
git commit -m "fix: bind batch results to source filename"
```

---

### Task 4: Full Regression and Acceptance Workbook Rebuild

**Files:**
- Create output: `/Users/can/Documents/Codex/2026-08-14/i/outputs/PROWRAP_Batch_Cost_Calculation_Acceptance.xlsx`
- Modify only if a verified defect is found: production file plus its focused test.

**Interfaces:**
- Consumes: complete implementation from Tasks 1-3.
- Produces: final approved acceptance workbook, render evidence, artifact hash, and full-suite report.

- [ ] **Step 1: Run the complete suite from a clean worktree**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
git diff --check
git status --short --branch
```

Expected: zero failures, clean diff check, and no uncommitted tracked changes.

- [ ] **Step 2: Generate the controlled processed acceptance workbook**

Use `scripts/create_acceptance_workbook.py` for the six-row controlled input, run it through real `process_workbook`, and write processed bytes to the exact output path. The six statuses remain:

```text
OK, REVIEW REQUIRED, NOT REPAIRABLE, INPUT ERROR, REVIEW REQUIRED, OK
```

- [ ] **Step 3: Mark and perform the one artifact-tool edit**

Immediately before the first artifact-tool edit/export command, run exactly once:

```bash
/Users/can/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  container_tools/mark_artifact_operation_started.mjs \
  --operation-kind edit --expected-output-count 1 --output-format xlsx
```

Import the workbook with `@oai/artifact-tool`, set `B3=50.00`, `E3=20.00`, and `H3=1.50`, export once, then pass the exported workbook through `process_workbook` so controlled protection, hidden state, filters, and formula allowlisting are rebuilt from the trusted template.

- [ ] **Step 4: Inspect calculations and workbook controls**

Using artifact-tool read-only inspection plus openpyxl, verify:

- seven-sheet order and hidden Lists;
- main and Cost sheets allow unlocked-cell selection and filtering under protection;
- Cost inputs are pale yellow, unlocked, validated, and retain `50/20/1.5`;
- `CostRows.ref == CostRows.autoFilter.ref == A5:V11`;
- all 120 source-to-cost mappings match;
- exactly twelve formulas exist, only in `U6:V11`;
- row 6 Cost is `191.319976674671` and Price is `286.979965012006` after recalculation;
- unavailable-material rows remain blank;
- 500 mm cloth row has no width warning and contains valid material quantities;
- `Summary!B7` records the acceptance source filename;
- `calcMode='auto'`, `fullCalcOnLoad=True`, and `forceFullCalc=True`;
- no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A` appears.

- [ ] **Step 5: Recalculate a temporary copy and render all sheets**

Use LibreOffice headless only on a temporary verification copy. Compare recalculated Cost/Price values to the literal results above; do not use a LibreOffice-resaved file as the controlled final artifact.

Render all seven controlled sheets and a focused `Cost Calculation!A1:V12` preview with artifact-tool. Confirm titles, inputs, headers, formulas/results, warning register, Summary disclaimer, Instructions, and hidden Lists state are legible and unclipped.

- [ ] **Step 6: Fix only a demonstrated defect test-first**

If verification fails, add one focused failing regression, demonstrate RED, make the smallest production correction, run the focused test to GREEN, rerun the complete suite, regenerate the artifact after that commit, and repeat Steps 4-5.

- [ ] **Step 7: Record release evidence**

Write the exact final file size, SHA-256, test count, render paths, formula count, mapping count, and workbook-control results into the task implementer report. Do not commit the output XLSX into the repository.

---

### Task 5: Whole-Branch Review, GitHub Publication, and Live Streamlit Verification

**Files:**
- Modify repository files only if the one permitted final-review fix wave requires it.
- Publish branch and PR in `Prowrap110/Iso24817CalcBatch` only.

**Interfaces:**
- Consumes: approved Tasks 1-4 and final acceptance artifact.
- Produces: merged GitHub batch release and verified live batch Streamlit workflow.

- [ ] **Step 1: Run one independent whole-branch review**

Generate one cumulative review package from merge base `ae99865` to HEAD. A fresh most-capable reviewer reads the approved spec, this plan, task reports, cumulative diff, and final artifact. It must independently probe OPC case/default/override behavior, cell boundaries, formula security, app source identity, workbook usability, privacy, and v1.1 isolation.

Expected verdict: no Critical or Important findings and `Ready to publish: Yes`.

- [ ] **Step 2: Apply at most one final-review fix wave**

If the reviewer reports Critical or Important findings, dispatch one fresh fixer with the complete list, require test-first corrections and a single commit, regenerate the artifact if any workbook/processor/app output changes, and run one scoped re-review. Any residual load-bearing finding stops publication.

- [ ] **Step 3: Verify local Streamlit startup**

Run the batch app headlessly on an unused local port and verify its health endpoint plus template download workflow. Stop only that local process after the check.

- [ ] **Step 4: Publish through the GitHub app**

Use `github:yeet` to confirm the cumulative scope, push `feature/cost-calculation-sheet`, and create a draft PR into the batch repository default branch. Confirm the PR targets `Prowrap110/Iso24817CalcBatch`, includes all tests/artifact evidence, and contains no v1.1 files. Review checks, mark ready, and merge only when clean.

- [ ] **Step 5: Verify the batch Streamlit deployment**

Open `https://prowrap-batch-calculator.streamlit.app/` using the authenticated Chrome/browser workflow. Confirm the deployed revision reflects the merged commit. Download the new template and verify the seven-sheet order plus formula-free template.

- [ ] **Step 6: Run a live representative batch workflow**

Upload a non-sensitive controlled test workbook, calculate, download the processed workbook, and inspect:

- source filename in `Summary!B7`;
- Cost Calculation sheet and editable inputs;
- exact Cost/Price formulas;
- separate Warnings sheet;
- successful processed-workbook re-upload;
- same bytes under a renamed test filename clear the prior result.

- [ ] **Step 7: Verify v1.1 isolation**

Open `https://iso24817calc-prowrapv11.streamlit.app/` read-only and confirm it remains available. Do not upload, edit settings, redeploy, or change its repository.

- [ ] **Step 8: Final handoff**

Report the merged commit/PR, live batch URL, final test count, final artifact hash, live checks, and explicit v1.1 unchanged status. Link the final acceptance workbook exactly once as the delivered spreadsheet output.
