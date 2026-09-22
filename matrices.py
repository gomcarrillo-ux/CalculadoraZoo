# matrices.py
"""Módulo de resolución de sistemas lineales por Gauss-Jordan.
Incluye el motor algebraico simbólico compartido con el módulo de vectores.
"""
import re
from fractions import Fraction

from flask import Blueprint, render_template, request

bp_matrices = Blueprint('matrices', __name__)


# ==============================================================================
# 1. MOTOR ALGEBRAICO SIMBÓLICO
# ==============================================================================

class AlgebraicExpression:
    def __init__(self, terms=None):
        self.terms = {}
        if terms:
            for k, v in terms.items():
                fv = Fraction(v)
                if fv != 0:
                    self.terms[k] = fv

    @classmethod
    def parse(cls, value_str):
        value_str = str(value_str).strip().replace(" ", "")
        if not value_str or value_str == "0":
            return cls()
        value_str = value_str.replace("-", "+-")
        parts = [p for p in value_str.split("+") if p]
        result = {}
        for part in parts:
            sign = 1
            if part.startswith("-"):
                sign = -1
                part = part[1:]
            match = re.search(r'[a-zA-Z]', part)
            if match:
                idx = match.start()
                coef_str = part[:idx]
                var_str = part[idx:]
                coef = Fraction(1) if coef_str in ("", "/") else Fraction(coef_str)
            else:
                coef = Fraction(part)
                var_str = ""
            result[var_str] = result.get(var_str, Fraction(0)) + coef * sign
        return cls(result)

    def is_zero(self):
        return len(self.terms) == 0

    def get_constant_value(self):
        return self.terms.get('', Fraction(0))

    def __add__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        new = dict(self.terms)
        for k, v in other.terms.items():
            new[k] = new.get(k, Fraction(0)) + v
        return AlgebraicExpression(new)

    __radd__ = __add__

    def __sub__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        new = dict(self.terms)
        for k, v in other.terms.items():
            new[k] = new.get(k, Fraction(0)) - v
        return AlgebraicExpression(new)

    def __rsub__(self, other):
        return AlgebraicExpression.parse(str(other)).__sub__(self)

    def __mul__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        new = {}
        for k1, v1 in self.terms.items():
            for k2, v2 in other.terms.items():
                combined = k2 if k1 == "" else k1 if k2 == "" else "".join(sorted([k1, k2]))
                new[combined] = new.get(combined, Fraction(0)) + v1 * v2
        return AlgebraicExpression(new)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        if other.is_zero():
            raise ZeroDivisionError("División por cero.")
        if len(other.terms) != 1:
            raise ValueError("Solo se permite dividir entre un monomio.")
        div_var, div_coef = list(other.terms.items())[0]
        new = {}
        for k, v in self.terms.items():
            if k == div_var:
                new_k = ""
            elif div_var == "":
                new_k = k
            elif k.startswith(div_var):
                new_k = k[len(div_var):]
            else:
                new_k = f"({k}/{div_var})" if k else f"(1/{div_var})"
            new[new_k] = new.get(new_k, Fraction(0)) + v / div_coef
        return AlgebraicExpression(new)

    def __eq__(self, other):
        if not isinstance(other, AlgebraicExpression):
            other = AlgebraicExpression.parse(str(other))
        return self.terms == other.terms

    def __neg__(self):
        return AlgebraicExpression({k: -v for k, v in self.terms.items()})

    def to_latex(self):
        if self.is_zero():
            return "0"
        parts = []
        for k in sorted(self.terms.keys(), key=lambda x: (x == '', x)):
            v = self.terms[k]
            sign = " + " if v > 0 else " - "
            av = abs(v)
            var_fmt = k
            if k != "":
                m = re.match(r'([a-zA-Z]+)(\d+)', k)
                if m:
                    var_fmt = f"{m.group(1)}_{{{m.group(2)}}}"
            if k == "":
                term = (f"{av.numerator}" if av.denominator == 1
                        else f"\\frac{{{av.numerator}}}{{{av.denominator}}}")
            else:
                if av == 1:
                    term = var_fmt
                elif av.denominator == 1:
                    term = f"{av.numerator}{var_fmt}"
                else:
                    term = f"\\frac{{{av.numerator}}}{{{av.denominator}}}{var_fmt}"
            parts.append((sign, term))
        res = ""
        for i, (sign, term) in enumerate(parts):
            if i == 0:
                res += "-" + term if sign == " - " else term
            else:
                res += sign + term
        return res

    def __str__(self):
        return self.to_latex()


# ==============================================================================
# 2. UTILIDADES
# ==============================================================================

def parse_expression(value_str):
    return AlgebraicExpression.parse(value_str)


def format_value(value):
    if isinstance(value, AlgebraicExpression):
        return value.to_latex()
    return str(value)


def format_matrix(matrix):
    return [[format_value(v) for v in row] for row in matrix]


def extract_coefficient_and_variable(value_str):
    value_str = str(value_str).strip().replace(" ", "")
    if not value_str:
        return "0", ""
    sign = ""
    if value_str.startswith("-"):
        sign, value_str = "-", value_str[1:]
    elif value_str.startswith("+"):
        value_str = value_str[1:]
    match = re.search(r'[a-zA-Z]', value_str)
    if match:
        i = match.start()
        c = value_str[:i] or "1"
        v = value_str[i:]
        return sign + c, v
    return sign + value_str, ""


# ==============================================================================
# 3. GAUSS-JORDAN CON PASO A PASO DETALLADO
# ==============================================================================

def _matrix_copy(matrix):
    return [row[:] for row in matrix]


def gauss_jordan_with_steps(augmented, num_vars):
    """
    augmented: matriz aumentada [A|b] de AlgebraicExpression
    num_vars: número de variables (columnas antes de b)
    Retorna: (steps_list, status, solution_dict, pivot_cols, free_cols)
      status: 'unique' | 'infinite' | 'inconsistent'
    """
    m = len(augmented)
    n = num_vars
    aug = _matrix_copy(augmented)
    steps = []
    step_num = [1]

    def add_step(title, desc, matrix):
        steps.append({
            'title': f'Paso {step_num[0]}: {title}',
            'desc': desc,
            'matrix': _matrix_copy(matrix) if matrix is not None else None
        })
        step_num[0] += 1

    add_step(
        "Matriz aumentada [A|b]",
        "Se escribe el sistema como matriz aumentada. Las primeras columnas corresponden a los coeficientes de las variables; la última columna es el vector <em>b</em>.",
        aug
    )

    pivot_positions = []
    pivot_row = 0

    # ---------- ELIMINACIÓN HACIA ADELANTE ----------
    for col in range(n):
        if pivot_row >= m:
            break

        # Buscar pivote en esta columna
        pivot_candidate = None
        for i in range(pivot_row, m):
            if not aug[i][col].is_zero():
                pivot_candidate = i
                break

        if pivot_candidate is None:
            continue  # columna sin pivote -> variable libre (potencial)

        # Intercambio si es necesario
        if pivot_candidate != pivot_row:
            aug[pivot_row], aug[pivot_candidate] = aug[pivot_candidate], aug[pivot_row]
            add_step(
                "Intercambio de filas",
                f"F<sub>{pivot_row+1}</sub> ↔ F<sub>{pivot_candidate+1}</sub> para colocar un pivote en la posición ({pivot_row+1}, {col+1}).",
                aug
            )

        # Escalar pivote a 1
        pivot_val = aug[pivot_row][col]
        if not (pivot_val == AlgebraicExpression.parse("1")):
            aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
            add_step(
                "Escalar fila pivote",
                f"F<sub>{pivot_row+1}</sub> = F<sub>{pivot_row+1}</sub> ÷ ({pivot_val.to_latex()}) para convertir el pivote en 1.",
                aug
            )

        pivot_positions.append((pivot_row, col))

        # Eliminar debajo del pivote
        for i in range(pivot_row + 1, m):
            factor = aug[i][col]
            if not factor.is_zero():
                aug[i] = [aug[i][j] - factor * aug[pivot_row][j] for j in range(n + 1)]
                add_step(
                    "Eliminar debajo del pivote",
                    f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pivot_row+1}</sub> para crear un cero debajo del pivote.",
                    aug
                )

        pivot_row += 1

    add_step(
        "Forma Escalonada por Filas",
        "La matriz alcanza la forma escalonada. Observe el patrón de escalera que forman los pivotes.",
        aug
    )

    # ---------- VERIFICAR CONSISTENCIA ----------
    for i in range(m):
        if all(aug[i][j].is_zero() for j in range(n)) and not aug[i][n].is_zero():
            add_step(
                "Sistema Inconsistente",
                "Aparece una fila del tipo [0 0 … 0 | b] con b ≠ 0. Por el <strong>teorema de existencia y unicidad</strong>, el sistema NO tiene solución.",
                aug
            )
            return steps, 'inconsistent', None, [], []

    # ---------- ELIMINACIÓN HACIA ATRÁS (RREF) ----------
    for k in range(len(pivot_positions) - 1, -1, -1):
        pr, pc = pivot_positions[k]
        for i in range(pr):
            factor = aug[i][pc]
            if not factor.is_zero():
                aug[i] = [aug[i][j] - factor * aug[pr][j] for j in range(n + 1)]
                add_step(
                    "Eliminar arriba del pivote",
                    f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pr+1}</sub> para crear un cero arriba del pivote.",
                    aug
                )

    add_step(
        "Forma Escalonada Reducida (RREF)",
        "Cada pivote es 1 y es el único elemento no nulo en su columna. Esta forma permite leer directamente las variables básicas en términos de las libres.",
        aug
    )

    # ---------- CLASIFICAR VARIABLES ----------
    pivot_cols = [pc for _, pc in pivot_positions]
    free_cols = [c for c in range(n) if c not in pivot_cols]

    if not free_cols:
        # Solución única
        solution = {}
        for pr, pc in pivot_positions:
            solution[pc] = aug[pr][n]
        add_step(
            "Solución Única",
            "No existen variables libres. Por el <strong>teorema de existencia y unicidad</strong>, el sistema tiene solución única.",
            None
        )
        return steps, 'unique', solution, pivot_cols, free_cols

    # Infinitas soluciones: expresar variables básicas en términos de las libres
    solution = {}
    for pr, pc in pivot_positions:
        expr = aug[pr][n]
        for fc in free_cols:
            coef = aug[pr][fc]
            if not coef.is_zero():
                expr = expr + AlgebraicExpression({f"x{fc+1}": -coef})
        solution[pc] = expr

    free_names = ", ".join(f"x<sub>{c+1}</sub>" for c in free_cols)
    add_step(
        "Infinitas Soluciones",
        f"Existen {len(free_cols)} variable(s) libre(s): {free_names}. Por el <strong>teorema de existencia y unicidad</strong>, el sistema tiene infinitas soluciones (una por cada asignación de valores a las variables libres).",
        None
    )
    return steps, 'infinite', solution, pivot_cols, free_cols


# ==============================================================================
# 4. OPERACIONES MATRICIALES (reutilizadas por vectores.py)
# ==============================================================================

def multiply_matrices(matrix_a, matrix_b):
    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    rows_b, cols_b = len(matrix_b), len(matrix_b[0])
    if cols_a != rows_b:
        raise ValueError(f"No se pueden multiplicar matrices {rows_a}x{cols_a} y {rows_b}x{cols_b}.")
    result = []
    for i in range(rows_a):
        row = []
        for j in range(cols_b):
            acc = AlgebraicExpression()
            for k in range(cols_a):
                acc = acc + matrix_a[i][k] * matrix_b[k][j]
            row.append(acc)
        result.append(row)
    return result


def rref(matrix_input):
    """RREF sin grabación de pasos (usado por vectores.py)."""
    A = _matrix_copy(matrix_input)
    rows, cols = len(A), len(A[0])
    r = 0
    for c in range(cols - 1):
        if r >= rows:
            break
        pivot = r
        while pivot < rows and A[pivot][c].is_zero():
            pivot += 1
        if pivot == rows:
            continue
        A[r], A[pivot] = A[pivot], A[r]
        pv = A[r][c]
        A[r] = [x / pv for x in A[r]]
        for i in range(rows):
            if i != r:
                f = A[i][c]
                A[i] = [A[i][j] - f * A[r][j] for j in range(cols)]
        r += 1
    return A


# ==============================================================================
# 5. RUTA /matrices  (SOLO Gauss-Jordan)
# ==============================================================================

@bp_matrices.route('/matrices', methods=['GET', 'POST'])
def matrices():
    if request.method == 'GET':
        return render_template('matrices.html')

    num_rows = int(request.form.get('filas', 2))
    num_cols = int(request.form.get('cols', 2))
    pasos, resultados, nombres_vars = [], [], []
    tipo_solucion = None

    try:
        matrix_a = []
        vector_b = []
        variable_names = [f"x_{{{j+1}}}" for j in range(num_cols)]

        for i in range(num_rows):
            row = []
            for j in range(num_cols):
                raw = request.form.get(f'a_{i}_{j}', '0')
                coef_str, var_str = extract_coefficient_and_variable(raw)
                row.append(parse_expression(coef_str))
                if var_str:
                    m = re.match(r'^([a-zA-Z]+)(\d+)$', var_str)
                    variable_names[j] = f"{m.group(1)}_{{{m.group(2)}}}" if m else var_str
            matrix_a.append(row)
            raw_b = request.form.get(f'b_{i}', '0')
            b_coef, _ = extract_coefficient_and_variable(raw_b)
            vector_b.append(parse_expression(b_coef))

        augmented = [matrix_a[i] + [vector_b[i]] for i in range(num_rows)]

        steps_dict, status, solution, pivot_cols, free_cols = gauss_jordan_with_steps(
            augmented, num_cols
        )

        # Convertir a formato (título, explicación, matriz) esperado por el template
        for s in steps_dict:
            pasos.append((
                s['title'],
                s['desc'],
                format_matrix(s['matrix']) if s['matrix'] is not None else None
            ))

        if status == 'inconsistent':
            tipo_solucion = 'inconsistente'
        elif status == 'unique':
            tipo_solucion = 'unica'
            for pc in sorted(solution.keys()):
                nombres_vars.append(variable_names[pc])
                resultados.append(solution[pc].to_latex())
        else:  # infinite
            tipo_solucion = 'infinitas'
            for pc in sorted(solution.keys()):
                nombres_vars.append(variable_names[pc])
                resultados.append(solution[pc].to_latex())
            for fc in free_cols:
                nombres_vars.append(variable_names[fc])
                resultados.append(f"{variable_names[fc]}\\;\\text{{libre}}")

    except Exception as e:
        pasos.append(("Error", f"Sintaxis o cálculo no válido: {str(e)}", None))

    return render_template(
        'matrices.html',
        pasos=pasos,
        resultados=resultados,
        nombres_vars=nombres_vars,
        tipo_solucion=tipo_solucion,
        filas=num_rows,
        cols=num_cols,
    )