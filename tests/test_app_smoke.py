from pathlib import Path
from io import BytesIO

from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

import app as batch_app
from tests.helpers import valid_row_values, workbook_bytes_with_rows


def test_source_identity_binds_bytes_and_exact_filename():
    """Catch either workbook bytes or the exact upload name being omitted from identity."""
    first = batch_app._source_identity(b'workbook-bytes', 'first.xlsx')

    assert first == 'e6b4a86d252ab928b43095ab4d409b1057eba46ce0ed4aafdebc1fe2c7ec2d58'
    assert batch_app._source_identity(b'changed-bytes', 'first.xlsx') != first
    assert batch_app._source_identity(b'workbook-bytes', 'renamed.xlsx') != first


def test_app_starts_with_template_and_upload_actions():
    """Catch a regression that removes the visible first two workflow stages."""
    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()

    assert not app.exception
    assert any('PROWRAP Batch Repair Calculator' in title.value for title in app.title)
    assert any(
        'Download Excel Template' in button.label for button in app.download_button
    )
    assert any('Upload workbook' in heading.value for heading in app.subheader)


def test_uploader_help_distinguishes_rejected_and_controlled_formulas():
    """Catch guidance that incorrectly says every formula-bearing workbook is rejected."""
    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()
    help_text = app.file_uploader[0].help

    assert 'Macros and uncontrolled formulas are rejected.' in help_text
    assert (
        'Exact controlled Cost and Price formulas in previously processed workbooks are accepted.'
        in help_text
    )


def test_valid_workbook_structure_keeps_calculation_available_with_row_errors():
    """Catch a regression that treats empty or bad data rows as workbook-level errors."""
    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()
    app.file_uploader[0].upload(
        'batch.xlsx',
        workbook_bytes_with_rows([
            valid_row_values(**{'Remaining Wall [mm]': 12.0}),
        ]),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ).run()

    calculate_button = next(button for button in app.button if button.label == 'Calculate Batch')
    assert not calculate_button.proto.disabled


def test_new_upload_clears_a_previous_processed_download():
    """Catch a regression that offers results belonging to a different upload."""
    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()
    app.file_uploader[0].upload(
        'first.xlsx',
        workbook_bytes_with_rows([valid_row_values()]),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ).run()
    next(button for button in app.button if button.label == 'Calculate Batch').click().run()

    assert any(
        button.label == 'Download Processed Workbook' for button in app.download_button
    )

    app.file_uploader[0].upload(
        'second.xlsx',
        workbook_bytes_with_rows([valid_row_values(**{'Pipe OD [mm]': 508.0})]),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ).run()

    assert not any(
        button.label == 'Download Processed Workbook' for button in app.download_button
    )


def test_renamed_identical_upload_clears_old_result_and_records_new_source_name():
    """Catch bytes-only identity reusing results generated under an earlier filename."""
    source = workbook_bytes_with_rows([valid_row_values()])
    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()
    app.file_uploader[0].upload(
        'first.xlsx',
        source,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ).run()
    next(button for button in app.button if button.label == 'Calculate Batch').click().run()

    assert any(
        button.label == 'Download Processed Workbook' for button in app.download_button
    )

    app.file_uploader[0].upload(
        'renamed-second.xlsx',
        source,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ).run()

    assert not any(
        button.label == 'Download Processed Workbook' for button in app.download_button
    )

    next(button for button in app.button if button.label == 'Calculate Batch').click().run()
    processed = load_workbook(BytesIO(app.session_state['processed_workbook_bytes']))

    assert processed['Summary']['B7'].value == 'renamed-second.xlsx'


def test_header_mismatch_shows_recognized_missing_and_unexpected_columns():
    """Catch a generic upload error that does not tell users how to fix headings."""
    source = workbook_bytes_with_rows([valid_row_values()])
    workbook = load_workbook(BytesIO(source))
    workbook['Batch Input & Results']['A1'] = 'Outside Diameter [mm]'
    changed = BytesIO()
    workbook.save(changed)

    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()
    app.file_uploader[0].upload(
        'changed-heading.xlsx',
        changed.getvalue(),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ).run()

    rendered = '\n'.join(markdown.value for markdown in app.markdown)
    assert 'Recognized input columns (17)' in rendered
    assert 'Missing input columns: Pipe OD [mm]' in rendered
    assert 'Unexpected headings: Outside Diameter [mm]' in rendered
