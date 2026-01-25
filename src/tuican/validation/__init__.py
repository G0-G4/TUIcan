from ..errors import ValidationError


def positive_int(number: str) -> int:
    try:
        number = int(number)
    except ValueError:
        raise ValidationError("введено не число")
    if number < 0:
        raise ValidationError("число должно быть больше 0")
    return number

def positive_float(number: str) -> float:
    try:
        number = float(number)
    except ValueError:
        raise ValidationError("введено не число")
    if number < 0:
        raise ValidationError("число должно быть больше 0")
    return number


def identity(string: str) -> str:
    return string
