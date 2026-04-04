import math
import unittest
from decimal import Decimal

def evaluate_safely(expression):
    """Безопасная версия движка вычислений для тестов"""
    safe_names = {
        'sin': lambda x: math.sin(math.radians(x)),
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': math.sqrt,
        'log': math.log10,
        'ln': math.log,
        'abs': abs,
        'fact': math.factorial,
        'pi': math.pi,
        'e': math.e,
    }
    expr = expression.replace("×", "*").replace("÷", "/").replace("^", "**")
    try:
        return eval(expr, {"__builtins__": None}, safe_names)
    except ZeroDivisionError:
        return "SINGULARITY"
    except Exception as e:
        return None

class TestCalculatorLogic(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(evaluate_safely("1 + 1"), 2)
        self.assertEqual(evaluate_safely("10 - 7"), 3)
        self.assertEqual(evaluate_safely("5 * 5"), 25)
        self.assertEqual(evaluate_safely("10 / 2"), 5)

    def test_complex_expressions(self):
        self.assertEqual(evaluate_safely("2 + 2 * 2"), 6)
        self.assertEqual(evaluate_safely("(2 + 2) * 2"), 8)
        self.assertEqual(evaluate_safely("2^3"), 8)

    def test_division_by_zero(self):
        self.assertEqual(evaluate_safely("1 / 0"), "SINGULARITY")

    def test_scientific_functions(self):
        self.assertAlmostEqual(evaluate_safely("sin(90)"), 1.0)
        self.assertEqual(evaluate_safely("sqrt(16)"), 4.0)

if __name__ == "__main__":
    unittest.main()
