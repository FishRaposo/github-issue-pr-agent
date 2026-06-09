#!/usr/bin/env python3
"""Demo repository for GitHub Issue-to-PR Automation Agent.

Contains a simple calculator with an intentional bug:
division by zero is not handled."""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    return a / b


def calculate(operation, a, b):
    operations = {"add": add, "subtract": subtract, "multiply": multiply, "divide": divide}
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    return operations[operation](a, b)


if __name__ == "__main__":
    print("Calculator Demo")
    print(f"2 + 3 = {add(2, 3)}")
    print(f"10 - 4 = {subtract(10, 4)}")
    print(f"6 * 7 = {multiply(6, 7)}")
    print(f"15 / 0 = {divide(15, 0)}")
