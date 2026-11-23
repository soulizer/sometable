import pytest
from django.core.exceptions import ValidationError

from baserow.contrib.database.fields.chinese_validators import (
    generate_id_card,
    generate_unified_social_credit_code,
    validate_id_card,
    validate_unified_social_credit_code,
)


@pytest.mark.parametrize(
    "value",
    [
        "110101199001010015",
        "11010119900101004x",
        generate_id_card(),
    ],
)
def test_valid_id_cards(value):
    assert validate_id_card(value).isupper()


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1101011990010100",
        "110101199001010014",
        "110101199013010015",
        "abcdefghijklmnopqr",
    ],
)
def test_invalid_id_cards(value):
    with pytest.raises(ValidationError):
        validate_id_card(value)


@pytest.mark.parametrize(
    "value",
    ["91350100M000100Y43", generate_unified_social_credit_code()],
)
def test_valid_unified_social_credit_codes(value):
    assert validate_unified_social_credit_code(value) == value.upper()


@pytest.mark.parametrize(
    "value",
    ["", "91350100M000100Y44", "91350100M000100Y4I", "91350100M000100Y4"],
)
def test_invalid_unified_social_credit_codes(value):
    with pytest.raises(ValidationError):
        validate_unified_social_credit_code(value)
