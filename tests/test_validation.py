import pytest

from tuican.validation import positive_int, positive_float, any_float, identity
from tuican.errors import ValidationError


class TestPositiveInt:
    def test_valid_positive(self):
        assert positive_int("42") == 42
        assert positive_int("1") == 1

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="число должно быть больше 0"):
            positive_int("0")

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="число должно быть больше 0"):
            positive_int("-5")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            positive_int("abc")

    def test_float_string_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            positive_int("3.14")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            positive_int("")


class TestPositiveFloat:
    def test_valid_positive(self):
        assert positive_float("3.14") == 3.14
        assert positive_float("1.0") == 1.0
        assert positive_float("0.001") == 0.001

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="число должно быть больше 0"):
            positive_float("0.0")

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="число должно быть больше 0"):
            positive_float("-2.5")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            positive_float("not_a_number")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            positive_float("")


class TestAnyFloat:
    def test_valid_positive(self):
        assert any_float("3.14") == 3.14

    def test_valid_negative(self):
        assert any_float("-2.5") == -2.5

    def test_valid_zero(self):
        assert any_float("0.0") == 0.0

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            any_float("hello")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="введено не число"):
            any_float("")


class TestIdentity:
    def test_returns_same_string(self):
        assert identity("hello") == "hello"

    def test_returns_empty_string(self):
        assert identity("") == ""

    def test_returns_whitespace(self):
        assert identity("   ") == "   "
