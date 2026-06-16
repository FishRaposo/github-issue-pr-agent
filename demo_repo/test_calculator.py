"""Sandbox test suite for the demo calculator.

The ``test_divide_by_zero_returns_none`` case FAILS against the shipped buggy
``divide`` (which raises ``ZeroDivisionError``) and PASSES once the agent applies
its fix (return ``None`` when the divisor is zero). This is the before/after
contract that the agent's pipeline verifies before opening a PR.
"""

from calculator import add, calculate, divide, multiply, subtract


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(10, 4) == 6


def test_multiply():
    assert multiply(6, 7) == 42


def test_divide_normal():
    assert divide(10, 2) == 5


def test_divide_by_zero_returns_none():
    # Before the fix this raises ZeroDivisionError; after the fix it returns None.
    assert divide(15, 0) is None


def test_calculate_dispatch():
    assert calculate("add", 2, 2) == 4
    assert calculate("divide", 8, 0) is None
