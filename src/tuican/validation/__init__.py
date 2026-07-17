from ..errors import ValidationError


def positive_int(number: str) -> int:
    try:
        parsed = int(number)
    except ValueError:
        raise ValidationError("введено не число")
    if parsed < 0:
        raise ValidationError("число должно быть больше 0")
    return parsed

def positive_float(number: str) -> float:
    try:
        parsed = float(number)
    except ValueError:
        raise ValidationError("введено не число")
    if parsed < 0:
        raise ValidationError("число должно быть больше 0")
    return parsed

def any_float(number: str) -> float:
    try:
        return float(number)
    except ValueError:
        raise ValidationError("введено не число")


def identity(string: str) -> str:
    return string
