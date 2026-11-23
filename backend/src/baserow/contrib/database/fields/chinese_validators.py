"""Validation helpers for Chinese identity numbers.

Both validators are used by the corresponding Baserow field types and must
stay in sync with the frontend implementations in
``web-frontend/modules/core/utils/string.js``.
"""

import random
from datetime import datetime

from django.core.exceptions import ValidationError

ID_CARD_WEIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
ID_CARD_CHECK_DIGITS = "10X98765432"
USCC_CHARSET = "0123456789ABCDEFGHJKLMNPQRTUWXY"
USCC_WEIGHTS = (1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28)

ID_CARD_ERROR = "Enter a valid 18-digit Chinese ID card number."
USCC_ERROR = "Enter a valid 18-character unified social credit code."


def id_card_check_digit(body: str) -> str:
    total = sum(int(digit) * weight for digit, weight in zip(body, ID_CARD_WEIGHTS))
    return ID_CARD_CHECK_DIGITS[total % 11]


def validate_id_card(value) -> str:
    """Validate a mainland Chinese resident ID card number (GB 11643)."""

    card = str(value or "").strip().upper()
    if len(card) != 18 or not card[:17].isdigit() or card[17] not in "0123456789X":
        raise ValidationError(ID_CARD_ERROR)

    try:
        datetime.strptime(card[6:14], "%Y%m%d")
    except ValueError:
        raise ValidationError(ID_CARD_ERROR) from None

    if card[17] != id_card_check_digit(card[:17]):
        raise ValidationError(ID_CARD_ERROR)

    return card


def uscc_check_char(body: str) -> str:
    total = sum(
        USCC_CHARSET.index(char) * weight for char, weight in zip(body, USCC_WEIGHTS)
    )
    return USCC_CHARSET[(31 - total % 31) % 31]


def validate_unified_social_credit_code(value) -> str:
    """Validate a unified social credit code (GB 32100)."""

    code = str(value or "").strip().upper()
    if len(code) != 18 or any(char not in USCC_CHARSET for char in code):
        raise ValidationError(USCC_ERROR)

    if code[17] != uscc_check_char(code[:17]):
        raise ValidationError(USCC_ERROR)

    return code


class IdCardValidator:
    """Picklable validator instance used by Django model/serializer fields."""

    def __call__(self, value) -> None:
        validate_id_card(value)


class UnifiedSocialCreditCodeValidator:
    def __call__(self, value) -> None:
        validate_unified_social_credit_code(value)


ID_CARD_VALIDATOR = IdCardValidator()
USCC_VALIDATOR = UnifiedSocialCreditCodeValidator()


def generate_id_card() -> str:
    body = f"11010119900101{random.randint(0, 999):03d}"
    return body + id_card_check_digit(body)


def generate_unified_social_credit_code() -> str:
    body = random.choice("123456789") + "".join(
        random.choice(USCC_CHARSET) for _ in range(16)
    )
    return body + uscc_check_char(body)
