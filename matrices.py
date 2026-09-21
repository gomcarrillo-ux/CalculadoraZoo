# matrices.py
"""Módulo de operaciones matriciales y sistemas lineales.

Incluye el motor algebraico simbólico (AlgebraicExpression) y las utilidades
de parseo/formato que otros módulos (vectores) reutilizan.
"""
import re
from fractions import Fraction

from flask import Blueprint, render_template, request

bp_matrices = Blueprint('matrices', __name__)


# ==============================================================================
# 1. MOTOR ALGEBRAICO SIMBÓLICO
# ==============================================================================

class AlgebraicExpression:
    """Representa expresiones algebraicas como {variable: Fraction}."""

    def __init__(self, terms=None):
        self.terms = {}
        if terms:
            for key, value in terms.items():
                value_fraction = Fraction(value)
                if value_fraction != 0:
                    self.terms[key] = value_fraction

    @classmethod
    def parse(cls, value_str):
        value_str = str(value_str).strip().replace(" ", "")
        if not value_str or value_str == "0":
            return cls()

        value_str = value_str.replace("-", "+-")
        parts = [p for p in value_str.split("+") if p]

        result_terms = {}
        for part in parts:
            sign = 1
            if part.startswith("-"):
                sign = -1
                part = part[1:]

            match = re.search(r'[a-zA-Z]', part)
            if match:
                index = match.start()
                coefficient_str = part[:index]
                variable_str = part[index:]

                if coefficient_str == "" or coefficient_str == "/":
                    coefficient = Fraction(1)
                else:
                    coefficient = Fraction(coefficient_str)
            else:
                coefficient_str = part
                variable_str = ""
                coefficient = Fraction(coefficient_str)

            coefficient *= sign
            result_terms[variable_str] = (
                result_terms.get(variable_str, Fraction(0)) + coefficient
            )

        return cls(result_terms)

    def is_zero(self):
        return len(self.terms) == 0

    def is_constant(self):
        return len(self.terms) == 0 or (
            len(self.terms) == 1 and '' in self.terms
        )

    def get_constant_value(self):
        return self.terms.get('', Fraction(0))

    def __add__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        new_terms = dict(self.terms)
        for key, value in other.terms.items():
            new_terms[key] = new_terms.get(key, Fraction(0)) + value
        return AlgebraicExpression(new_terms)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        new_terms = dict(self.terms)
        for key, value in other.terms.items():
            new_terms[key] = new_terms.get(key, Fraction(0)) - value
        return AlgebraicExpression(new_terms)

    def __rsub__(self, other):
        return AlgebraicExpression.parse(str(other)).__sub__(self)

    def __mul__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        new_terms = {}
        for key_1, value_1 in self.terms.items():
            for key_2, value_2 in other.terms.items():
                if key_1 == "":
                    combined = key_2
                elif key_2 == "":
                    combined = key_1
                else:
                    combined = "".join(sorted([key_1, key_2]))
                coefficient = value_1 * value_2
                new_terms[combined] = (
                    new_terms.get(combined, Fraction(0)) + coefficient
                )
        return AlgebraicExpression(new_terms)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        if other.is_zero():
            raise ZeroDivisionError("Division by zero.")

        if other.is_constant():
            constant = other.get_constant_value()
            return AlgebraicExpression(
                {k: v / constant for k, v in self.terms.items()}
            )

        if len(other.terms) == 1:
            divisor_variable, divisor_coefficient = list(other.terms.items())[0]
            new_terms = {}
            for key, value in self.terms.items():
                if key == divisor_variable:
                    new_key = ""
                elif key.startswith(divisor_variable):
                    new_key = key[len(divisor_variable):]
                else:
                    new_key = (
                        f"({key}/{divisor_variable})"
                        if key else f"(1/{divisor_variable})"
                    )
                new_terms[new_key] = (
                    new_terms.get(new_key, Fraction(0))
                    + (value / divisor_coefficient)
                )
            return AlgebraicExpression(new_terms)

        raise ValueError("Complex polynomial division is not supported.")

    def to_latex(self):
        if self.is_zero():
            return "0"

        parts = []
        sorted_keys = sorted(self.terms.keys(), key=lambda x: (x == '', x))

        for key in sorted_keys:
            value = self.terms[key]
            sign = " + " if value > 0 else " - "
            absolute_value = abs(value)

            formatted_variable = key
            if key != "":
                match = re.match(r'([a-zA-Z]+)(\d+)', key)
                if match:
                    formatted_variable = (
                        f"{match.group(1)}_{{{match.group(2)}}}"
                    )

            if key == "":
                term_str = (
                    f"{absolute_value.numerator}"
                    if absolute_value.denominator == 1
                    else f"\\frac{{{absolute_value.numerator}}}"
                         f"{{{absolute_value.denominator}}}"
                )
            else:
                if absolute_value == 1:
                    term_str = formatted_variable
                elif absolute_value.denominator == 1:
                    term_str = f"{absolute_value.numerator}{formatted_variable}"
                else:
                    term_str = (
                        f"\\frac{{{absolute_value.numerator}}}"
                        f"{{{absolute_value.denominator}}}"
                        f"{formatted_variable}"
                    )

            parts.append((sign, term_str))

        result = ""
        for index, (sign, term_str) in enumerate(parts):
            if index == 0:
                result += "-" + term_str if sign == " - " else term_str
            else:
                result += sign + term_str
        return result

    def __str__(self):
        return self.to_latex()


# ==============================================================================
# 2. UTILIDADES DE PARSEO Y FORMATO (compartidas con vectores.py)
# ==============================================================================

def parse_expression(value_str):
    return AlgebraicExpression.parse(value_str)


def format_value(value):
    if isinstance(value, AlgebraicExpression):
        return value.to_latex()
    return str(value)


def format_matrix(matrix):
    return [[format_value(element) for element in row] for row in matrix]


def extract_coefficient_and_variable(value_str):
    value_str = str(value_str).strip().replace(" ", "")
    if not value_str:
        return "0", ""

    sign = ""
    if value_str.startswith("-"):
        sign = "-"
        value_str = value_str[1:]
    elif value_str.startswith("+"):
        value_str = value_str[1:]

    match = re.search(r'[a-zA-Z]', value_str)
    if match:
        index = match.start()
        coefficient_str = value_str[:index]
        variable_str = value_str[index:]
        if coefficient_str == "":
            coefficient_str = "1"
        return sign + coefficient_str, variable_str

    return sign + value_str, ""


# ==============================================================================
# 3. OPERACIONES MATRICIALES
# ==============================================================================

def add_or_subtract_matrices(matrix_a, matrix_b, operation='add'):
    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    result = []
    for i in range(rows_a):
        row = []
        for j in range(cols_a):
            if operation == 'add':
                row.append(matrix_a[i][j] + matrix_b[i][j])
            else:
                row.append(matrix_a[i][j] - matrix_b[i][j])
        result.append(row)
    return result


def scalar_multiply_matrix(scalar, matrix):
    scalar_expression = parse_expression(scalar)
    return [
        [scalar_expression * matrix[i][j] for j in range(len(matrix[0]))]
        for i in range(len(matrix))
    ]


def multiply_matrices(matrix_a, matrix_b):
    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    rows_b, cols_b = len(matrix_b), len(matrix_b[0])

    if cols_a != rows_b:
        raise ValueError(
            f"Cannot multiply matrices of dimensions "
            f"{rows_a}x{cols_a} and {rows_b}x{cols_b}."
        )

    result = []
    for i in range(rows_a):
        row = []
        for j in range(cols_b):
            accumulated = AlgebraicExpression()
            for k in range(cols_a):
                accumulated = accumulated + (matrix_a[i][k] * matrix_b[k][j])
            row.append(accumulated)
        result.append(row)
    return result


# ==============================================================================
# 4. SISTEMAS LINEALES Y COMBINACIÓN LINEAL
# ==============================================================================

def reduced_row_echelon_form(matrix_input):
    matrix = [[element for element in row] for row in matrix_input]
    rows, cols = len(matrix), len(matrix[0])
    pivot_row_index = 0

    for col in range(cols - 1):
        if pivot_row_index >= rows:
            break

        pivot_candidate = pivot_row_index
        while pivot_candidate < rows and matrix[pivot_candidate][col].is_zero():
            pivot_candidate += 1

        if pivot_candidate == rows:
            continue

        matrix[pivot_row_index], matrix[pivot_candidate] = (
            matrix[pivot_candidate], matrix[pivot_row_index]
        )
        pivot_value = matrix[pivot_row_index][col]

        matrix[pivot_row_index] = [
            element / pivot_value for element in matrix[pivot_row_index]
        ]

        for i in range(rows):
            if i != pivot_row_index:
                factor = matrix[i][col]
                matrix[i] = [
                    matrix[i][j] - (factor * matrix[pivot_row_index][j])
                    for j in range(cols)
                ]

        pivot_row_index += 1

    return matrix


def solve_linear_system(matrix_a, vector_b):
    augmented = [matrix_a[i] + [vector_b[i]] for i in range(len(matrix_a))]
    reduced = reduced_row_echelon_form(augmented)
    solution = [reduced[i][-1] for i in range(len(matrix_a))]
    return reduced, solution


def check_linear_combination(vectors, vector_b):
    num_rows, num_vectors = len(vector_b), len(vectors)
    matrix_a = [
        [vectors[j][i] for j in range(num_vectors)] for i in range(num_rows)
    ]
    reduced, scalars = solve_linear_system(matrix_a, vector_b)

    for row in reduced:
        coefficients_are_zero = all(el.is_zero() for el in row[:-1])
        if coefficients_are_zero and not row[-1].is_zero():
            return False, reduced, scalars

    return True, reduced, scalars


# ==============================================================================
# 5. RUTA /matrices
# ==============================================================================

@bp_matrices.route('/matrices', methods=['GET', 'POST'])
def matrices():
    if request.method == 'GET':
        return render_template('matrices.html')

    method = request.form.get('metodo')
    num_rows = int(request.form.get('filas', 2))
    num_cols = int(request.form.get('cols', 2))
    steps, results, variable_names = [], [], []

    if request.method == 'POST':
        try:
            if method in ['gauss', 'gauss_jordan']:
                matrix_a = []
                vector_b = []
                variable_names = [f"x_{{{j+1}}}" for j in range(num_cols)]

                for i in range(num_rows):
                    row = []
                    for j in range(num_cols):
                        raw_value = request.form.get(f'a_{i}_{j}', '0')
                        coefficient_str, variable_str = (
                            extract_coefficient_and_variable(raw_value)
                        )
                        row.append(parse_expression(coefficient_str))

                        if variable_str:
                            match = re.match(r'^([a-zA-Z]+)(\d+)$', variable_str)
                            if match:
                                variable_names[j] = (
                                    f"{match.group(1)}_{{{match.group(2)}}}"
                                )
                            else:
                                variable_names[j] = variable_str
                    matrix_a.append(row)

                    raw_b = request.form.get(f'b_{i}', '0')
                    coefficient_b, _ = extract_coefficient_and_variable(raw_b)
                    vector_b.append(parse_expression(coefficient_b))

                reduced, solution = solve_linear_system(matrix_a, vector_b)
                original = [
                    matrix_a[i] + [vector_b[i]] for i in range(len(matrix_a))
                ]

                steps.append((
                    "Matriz Original [A|b]",
                    "Ecuación matricial Ax = b:",
                    format_matrix(original),
                ))
                steps.append((
                    "Forma Escalonada Reducida (RREF)",
                    "Matriz resultante por Gauss-Jordan:",
                    format_matrix(reduced),
                ))

                results = [format_value(x) for x in solution]

            elif method == 'comb_lineal':
                vectors = [
                    [
                        parse_expression(request.form.get(f'v_{i}_{j}', '0'))
                        for i in range(num_rows)
                    ]
                    for j in range(num_cols)
                ]
                vector_b = [
                    parse_expression(request.form.get(f'b_{i}', '0'))
                    for i in range(num_rows)
                ]

                is_combination, reduced, scalars = check_linear_combination(
                    vectors, vector_b
                )
                steps.append((
                    "Sistema Aumentado",
                    "Evaluación de combinación lineal:",
                    format_matrix(reduced),
                ))

                if is_combination:
                    steps.append((
                        "Resultado",
                        "¡El vector $b$ SÍ es combinación lineal!",
                        None,
                    ))
                    results = [format_value(c) for c in scalars]
                    variable_names = [
                        f"c_{{{i+1}}}" for i in range(len(scalars))
                    ]
                else:
                    steps.append((
                        "Resultado",
                        "El vector $b$ NO es combinación lineal.",
                        None,
                    ))

        except Exception as exception:
            steps.append((
                "Error Algebraico",
                f"Sintaxis o cálculo no válido: {str(exception)}",
                None,
            ))

    return render_template(
        'matrices.html',
        pasos=steps,
        resultados=results,
        nombres_vars=variable_names,
        metodo=method,
        filas=num_rows,
        cols=num_cols,
    )