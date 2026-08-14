from batch_status import CalculationStatus, classify_result


def test_not_repairable_has_priority_over_review_warning():
    result = {
        'type_b_details': {'repairable_formula12': False},
        'compliance_warnings': ['outside validity'],
    }

    assert classify_result(result, ()) is CalculationStatus.NOT_REPAIRABLE


def test_warning_produces_review_required():
    result = {
        'type_b_details': None,
        'compliance_warnings': ['check required'],
    }

    assert classify_result(result, ()) is CalculationStatus.REVIEW_REQUIRED


def test_adapter_warning_produces_review_required():
    result = {'type_b_details': None, 'compliance_warnings': []}

    assert classify_result(result, ('Confirm product approval.',)) is CalculationStatus.REVIEW_REQUIRED


def test_clean_result_is_ok():
    result = {'type_b_details': None, 'compliance_warnings': []}

    assert classify_result(result, ()) is CalculationStatus.OK
