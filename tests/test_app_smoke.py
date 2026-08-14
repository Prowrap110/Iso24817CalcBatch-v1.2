from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.helpers import valid_row_values, workbook_bytes_with_rows


def test_app_starts_with_template_and_upload_actions():
    """Catch a regression that removes the visible first two workflow stages."""
    app = AppTest.from_file(Path(__file__).parents[1] / 'app.py').run()

    assert not app.exception
    assert any('PROWRAP Batch Repair Calculator' in title.value for title in app.title)
    assert any(
        'Download Excel Template' in button.label for button in app.download_button
    )
    assert any('Upload workbook' in heading.value for heading in app.subheader)


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
