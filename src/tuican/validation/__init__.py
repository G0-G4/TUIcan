from src.tuican.errors import ValidationError


def positive_int(number: str) -> int:
    try:
        age = int(number)
    except ValueError:
        raise ValidationError("введено не число")
    if age < 0:
        raise ValidationError("число должно быть больше 0")
    return age


def identity(string: str) -> str:
    return string
