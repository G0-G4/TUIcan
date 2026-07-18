import pytest

from tuican.validation import positive_int, positive_float, any_float, identity
from tuican.errors import ValidationError


class TestPositiveInt:
    def test_valid_positive(self):
        assert positive_int("42") == 42
        assert positive_int("1") == 1

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="number must be greater than 0"):
            positive_int("0")

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="number must be greater than 0"):
            positive_int("-5")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            positive_int("abc")

    def test_float_string_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            positive_int("3.14")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            positive_int("")

    def test_override_not_a_number_msg(self):
        with pytest.raises(ValidationError, match="custom parse error"):
            positive_int("abc", not_a_number_msg="custom parse error")

    def test_override_must_be_positive_msg(self):
        with pytest.raises(ValidationError, match="custom positive error"):
            positive_int("-5", must_be_positive_msg="custom positive error")

    def test_override_zero_msg(self):
        with pytest.raises(ValidationError, match="custom positive error"):
            positive_int("0", must_be_positive_msg="custom positive error")


class TestPositiveFloat:
    def test_valid_positive(self):
        assert positive_float("3.14") == 3.14
        assert positive_float("1.0") == 1.0
        assert positive_float("0.001") == 0.001

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="number must be greater than 0"):
            positive_float("0.0")

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="number must be greater than 0"):
            positive_float("-2.5")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            positive_float("not_a_number")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            positive_float("")

    def test_override_not_a_number_msg(self):
        with pytest.raises(ValidationError, match="custom parse error"):
            positive_float("abc", not_a_number_msg="custom parse error")

    def test_override_must_be_positive_msg(self):
        with pytest.raises(ValidationError, match="custom positive error"):
            positive_float("-2.5", must_be_positive_msg="custom positive error")

    def test_override_zero_msg(self):
        with pytest.raises(ValidationError, match="custom positive error"):
            positive_float("0.0", must_be_positive_msg="custom positive error")


class TestAnyFloat:
    def test_valid_positive(self):
        assert any_float("3.14") == 3.14

    def test_valid_negative(self):
        assert any_float("-2.5") == -2.5

    def test_valid_zero(self):
        assert any_float("0.0") == 0.0

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            any_float("hello")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="not a number"):
            any_float("")

    def test_override_not_a_number_msg(self):
        with pytest.raises(ValidationError, match="custom parse error"):
            any_float("abc", not_a_number_msg="custom parse error")


class TestIdentity:
    def test_returns_same_string(self):
        assert identity("hello") == "hello"

    def test_returns_empty_string(self):
        assert identity("") == ""

    def test_returns_whitespace(self):
        assert identity("   ") == "   "
