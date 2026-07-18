from ..errors import ValidationError


def positive_int(
    number: str,
    *,
    not_a_number_msg: str = "not a number",
    must_be_positive_msg: str = "number must be greater than 0",
) -> int:
    try:
        parsed = int(number)
    except ValueError:
        raise ValidationError(not_a_number_msg)
    if parsed <= 0:
        raise ValidationError(must_be_positive_msg)
    return parsed


def positive_float(
    number: str,
    *,
    not_a_number_msg: str = "not a number",
    must_be_positive_msg: str = "number must be greater than 0",
) -> float:
    try:
        parsed = float(number)
    except ValueError:
        raise ValidationError(not_a_number_msg)
    if parsed <= 0:
        raise ValidationError(must_be_positive_msg)
    return parsed


def any_float(
    number: str,
    *,
    not_a_number_msg: str = "not a number",
) -> float:
    try:
        return float(number)
    except ValueError:
        raise ValidationError(not_a_number_msg)


def identity(string: str) -> str:
    return string
