#!/usr/bin/env python3
"""Demo calculator for the GitHub Issue-to-PR agent walkthrough.

Contains a deliberate bug: ``divide`` does not guard against a zero divisor, so
``divide(x, 0)`` raises ``ZeroDivisionError``. The bundled test
``test_divide_by_zero_returns_none`` fails because of it. The agent reads the
matching issue (#101), plans the fix, edits this file, and re-runs the tests —
which then pass.
"""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    return a / b


def calculate(operation, a, b):
    operations = {
        "add": add,
        "subtract": subtract,
        "multiply": multiply,
        "divide": divide,
    }
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    return operations[operation](a, b)


if __name__ == "__main__":
    print("Calculator Demo")
    print(f"2 + 3 = {add(2, 3)}")
    print(f"10 - 4 = {subtract(10, 4)}")
    print(f"6 * 7 = {multiply(6, 7)}")
