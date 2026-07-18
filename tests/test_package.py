"""Tests for top-level package re-exports."""

import pytest


def test_all_expected_exports_are_importable():
    import tuican

    assert hasattr(tuican, "Application")
    assert hasattr(tuican, "get_user_id")
    assert hasattr(tuican, "MessageBackend")
    assert hasattr(tuican, "PythonTelegramBotBackend")
    assert hasattr(tuican, "ValidationError")
    assert hasattr(tuican, "KeyboardButton")
    assert hasattr(tuican, "StateStore")


def test_identity_against_direct_submodule_imports():
    import tuican
    import tuican.application
    import tuican.backend
    import tuican.errors
    import tuican.keyboard_button
    import tuican.state_store

    assert tuican.Application is tuican.application.Application
    assert tuican.get_user_id is tuican.application.get_user_id
    assert tuican.MessageBackend is tuican.backend.MessageBackend
    assert tuican.PythonTelegramBotBackend is tuican.backend.PythonTelegramBotBackend
    assert tuican.ValidationError is tuican.errors.ValidationError
    assert tuican.KeyboardButton is tuican.keyboard_button.KeyboardButton
    assert tuican.StateStore is tuican.state_store.StateStore


def test_user_not_found_error_not_exported():
    import tuican

    with pytest.raises(AttributeError):
        tuican.UserNotFoundError


def test_all_matches_exported_set():
    import tuican

    expected = {
        "Application",
        "get_user_id",
        "MessageBackend",
        "PythonTelegramBotBackend",
        "ValidationError",
        "KeyboardButton",
        "StateStore",
    }
    assert set(tuican.__all__) == expected


def test_stores_submodule_still_works():
    from tuican.stores import JsonFileStateStore, InMemoryStateStore

    assert JsonFileStateStore is not None
    assert InMemoryStateStore is not None
