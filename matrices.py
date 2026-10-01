# matrices.py
"""Módulo de Álgebra Lineal: Matrices.
Soporta 3 modos de operación:
1. Gauss-Jordan (Sistemas de ecuaciones Ax = b)
2. Matriz Inversa (A^-1 vía [A | I] -> [I | A^-1])
3. Multiplicación de Matrices (A × B)
"""
import re
from fractions import Fraction
from flask import Blueprint, render_template, request

bp_matrices = Blueprint('matrices', __name__)


# 1. MOTOR ALGEBRAICO SIMBÓLICO

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


# 2. UTILIDADES, CÁLCULO DE LÍMITES Y FORMATO LATEX

def parse_expression(value_str):
    return AlgebraicExpression.parse(value_str)


def format_value(value):
    if isinstance(value, AlgebraicExpression):
        return value.to_latex()
    return str(value)


def multiply_matrices(matrix_a, matrix_b):
    """Multiplica dos matrices 2D compuestas por AlgebraicExpression o numéricas."""
    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    rows_b, cols_b = len(matrix_b), len(matrix_b[0])
    if cols_a != rows_b:
        raise ValueError(f"No se pueden multiplicar matrices de {rows_a}x{cols_a} y {rows_b}x{cols_b}.")
    
    result = []
    for i in range(rows_a):
        row_res = []
        for j in range(cols_b):
            acc = AlgebraicExpression()
            for k in range(cols_a):
                val_a = matrix_a[i][k]
                val_b = matrix_b[k][j]
                if not isinstance(val_a, AlgebraicExpression):
                    val_a = AlgebraicExpression.parse(str(val_a))
                if not isinstance(val_b, AlgebraicExpression):
                    val_b = AlgebraicExpression.parse(str(val_b))
                acc = acc + (val_a * val_b)
            row_res.append(acc)
        result.append(row_res)
    return result


def get_system_matrix_limit():
    """Calcula la memoria disponible del sistema y estima la dimensión máxima N x N soportada."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        ram_disponible_mb = mem.available / (1024 * 1024)
        ram_total_gb = mem.total / (1024 ** 3)
        # Estimación: Cada elemento de AlgebraicExpression en Python consume ~1 KB de memoria RAM
        max_elementos = int(mem.available / 1024)
        max_dim = int(max_elementos ** 0.5)
        return {
            'ram_total_gb': f"{ram_total_gb:.2f} GB",
            'ram_disponible_mb': f"{ram_disponible_mb:.0f} MB",
            'max_dim': f"{max_dim} × {max_dim}",
            'max_elementos': f"{max_elementos:,}"
        }
    except Exception:
        return {
            'ram_total_gb': "No detectada",
            'ram_disponible_mb': "No detectada",
            'max_dim': "Estimado ~3,000 × 3,000",
            'max_elementos': "Estimado ~9,000,000"
        }


def matrix_to_latex(matrix, augmented_col=None):
    """Convierte una matriz 2D a formato KaTeX. Soporta división vertical para matrices aumentadas."""
    if not matrix:
        return None
    rows = []
    if augmented_col is not None and augmented_col > 0:
        num_cols = len(matrix[0])
        left_cols = num_cols - augmented_col
        col_spec = "c" * left_cols + "|" + "c" * augmented_col
        for row in matrix:
            row_str = " & ".join(x.to_latex() if hasattr(x, 'to_latex') else str(x) for x in row)
            rows.append(row_str)
        return "\\left[\\begin{array}{" + col_spec + "} " + " \\\\ ".join(rows) + " \\end{array}\\right]"
    else:
        for row in matrix:
            row_str = " & ".join(x.to_latex() if hasattr(x, 'to_latex') else str(x) for x in row)
            rows.append(row_str)
        return "\\begin{bmatrix} " + " \\\\ ".join(rows) + " \\end{bmatrix}"


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


def _matrix_copy(matrix):
    return [row[:] for row in matrix]


# 3. ALGORITMOS CON PASOS EN LATEX

def gauss_jordan_with_steps(augmented, num_vars):
    """Resolución de Ax = b por Gauss-Jordan paso a paso."""
    m = len(augmented)
    n = num_vars
    aug = _matrix_copy(augmented)
    steps = []
    step_num = [1]

    def add_step(title, desc, matrix):
        steps.append({
            'title': f'Paso {step_num[0]}: {title}',
            'desc': desc,
            'matrix': matrix_to_latex(matrix, augmented_col=1) if matrix is not None else None
        })
        step_num[0] += 1

    add_step(
        "Matriz aumentada [A|b]",
        "Se escribe el sistema como matriz aumentada. Las primeras columnas corresponden a los coeficientes de las variables y la última al vector de términos independientes.",
        aug
    )

    pivot_positions = []
    pivot_row = 0

    for col in range(n):
        if pivot_row >= m:
            break

        pivot_candidate = None
        for i in range(pivot_row, m):
            if not aug[i][col].is_zero():
                pivot_candidate = i
                break

        if pivot_candidate is None:
            continue

        if pivot_candidate != pivot_row:
            aug[pivot_row], aug[pivot_candidate] = aug[pivot_candidate], aug[pivot_row]
            add_step(
                "Intercambio de filas",
                f"F<sub>{pivot_row+1}</sub> ↔ F<sub>{pivot_candidate+1}</sub> para colocar un pivote en la posición ({pivot_row+1}, {col+1}).",
                aug
            )

        pivot_val = aug[pivot_row][col]
        if not (pivot_val == AlgebraicExpression.parse("1")):
            aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
            add_step(
                "Escalar fila pivote",
                f"F<sub>{pivot_row+1}</sub> = F<sub>{pivot_row+1}</sub> ÷ ({pivot_val.to_latex()}) para convertir el pivote en 1.",
                aug
            )

        pivot_positions.append((pivot_row, col))

        for i in range(pivot_row + 1, m):
            factor = aug[i][col]
            if not factor.is_zero():
                aug[i] = [aug[i][j] - factor * aug[pivot_row][j] for j in range(n + 1)]
                add_step(
                    "Eliminar debajo del pivote",
                    f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pivot_row+1}</sub> para hacer cero el elemento inferior.",
                    aug
                )

        pivot_row += 1

    add_step(
        "Forma Escalonada por Filas",
        "La matriz alcanza la forma escalonada por filas.",
        aug
    )

    for i in range(m):
        if all(aug[i][j].is_zero() for j in range(n)) and not aug[i][n].is_zero():
            add_step(
                "Sistema Inconsistente",
                "Aparece una fila del tipo [0 … 0 | b] con b ≠ 0. El sistema NO tiene solución.",
                aug
            )
            return steps, 'inconsistent', None, [], []

    for k in range(len(pivot_positions) - 1, -1, -1):
        pr, pc = pivot_positions[k]
        for i in range(pr):
            factor = aug[i][pc]
            if not factor.is_zero():
                aug[i] = [aug[i][j] - factor * aug[pr][j] for j in range(n + 1)]
                add_step(
                    "Eliminar arriba del pivote",
                    f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pr+1}</sub> para hacer cero el elemento superior.",
                    aug
                )

    add_step(
        "Forma Escalonada Reducida (RREF)",
        "Cada pivote es 1 y es el único elemento no nulo en su columna.",
        aug
    )

    pivot_cols = [pc for _, pc in pivot_positions]
    free_cols = [c for c in range(n) if c not in pivot_cols]

    if not free_cols:
        solution = {pc: aug[pr][n] for pr, pc in pivot_positions}
        add_step("Solución Única", "No existen variables libres. El sistema posee solución única.", None)
        return steps, 'unique', solution, pivot_cols, free_cols

    solution = {}
    for pr, pc in pivot_positions:
        expr = aug[pr][n]
        for fc in free_cols:
            coef = aug[pr][fc]
            if not coef.is_zero():
                expr = expr - coef * AlgebraicExpression({f"x{fc+1}": 1})
        solution[pc] = expr

    free_names = ", ".join(f"x<sub>{c+1}</sub>" for c in free_cols)
    add_step(
        "Infinitas Soluciones",
        f"Existen {len(free_cols)} variable(s) libre(s): {free_names}. El sistema posee infinitas soluciones.",
        None
    )
    return steps, 'infinite', solution, pivot_cols, free_cols


def inverse_with_steps(matrix_a):
    """Cálculo de A^-1 por reducción Gauss-Jordan [A | I] -> [I | A^-1]. Evaluando Invertibilidad."""
    n = len(matrix_a)
    if any(len(row) != n for row in matrix_a):
        raise ValueError("La matriz debe ser cuadrada (n x n) para calcular su inversa.")

    aug = []
    for i in range(n):
        identity_row = [AlgebraicExpression.parse("1" if i == j else "0") for j in range(n)]
        aug.append(matrix_a[i] + identity_row)

    steps = []
    step_num = [1]

    def add_step(title, desc, matrix):
        steps.append({
            'title': f'Paso {step_num[0]}: {title}',
            'desc': desc,
            'matrix': matrix_to_latex(matrix, augmented_col=n) if matrix is not None else None
        })
        step_num[0] += 1

    add_step(
        "Matriz Aumentada [A | I]",
        "Se adjunta la matriz identidad <em>I<sub>n</sub></em> a la derecha de la matriz <em>A</em> para iniciar la reducción.",
        aug
    )

    pivot_row = 0
    for col in range(n):
        pivot_candidate = None
        for i in range(pivot_row, n):
            if not aug[i][col].is_zero():
                pivot_candidate = i
                break

        if pivot_candidate is None:
            add_step(
                "Matriz Singular (NO es Invertible)",
                f"No se encontró un pivote no nulo en la columna {col+1}. La matriz <strong>NO ES INVERTIBLE</strong> (su determinante es 0).",
                aug
            )
            return steps, False, None

        if pivot_candidate != pivot_row:
            aug[pivot_row], aug[pivot_candidate] = aug[pivot_candidate], aug[pivot_row]
            add_step(
                "Intercambio de filas",
                f"F<sub>{pivot_row+1}</sub> ↔ F<sub>{pivot_candidate+1}</sub> para posicionar un pivote.",
                aug
            )

        pivot_val = aug[pivot_row][col]
        if not (pivot_val == AlgebraicExpression.parse("1")):
            aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
            add_step(
                "Escalar fila pivote",
                f"F<sub>{pivot_row+1}</sub> = F<sub>{pivot_row+1}</sub> ÷ ({pivot_val.to_latex()}) para obtener pivote 1.",
                aug
            )

        for i in range(n):
            if i != pivot_row:
                factor = aug[i][col]
                if not factor.is_zero():
                    aug[i] = [aug[i][j] - factor * aug[pivot_row][j] for j in range(2 * n)]
                    add_step(
                        f"Eliminar en columna {col+1}",
                        f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pivot_row+1}</sub> para hacer cero el elemento ({i+1}, {col+1}).",
                        aug
                    )

        pivot_row += 1

    inv_matrix = [aug[i][n:] for i in range(n)]

    add_step(
        "Forma Final [I | A⁻¹]",
        "El bloque izquierdo se redujo exitosamente a <em>I<sub>n</sub></em>. Por lo tanto, la matriz <strong>ES INVERTIBLE</strong> y el bloque derecho corresponde a su matriz inversa A<sup>-1</sup>.",
        aug
    )

    return steps, True, inv_matrix


def matrix_multiplication_with_steps(matrix_a, matrix_b):
    """Multiplicación de matrices C = A x B paso a paso."""
    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    rows_b, cols_b = len(matrix_b), len(matrix_b[0])

    if cols_a != rows_b:
        raise ValueError(
            f"No es posible multiplicar matrices de dimensiones {rows_a}×{cols_a} y {rows_b}×{cols_b}."
        )

    steps = []
    result = []

    steps.append({
        'title': 'Análisis de Dimensiones',
        'desc': f'Matriz A: {rows_a}×{cols_a} | Matriz B: {rows_b}×{cols_b}. El producto C = A × B está definido y tendrá dimensión {rows_a}×{cols_b}.',
        'matrix': None
    })

    for i in range(rows_a):
        row_res = []
        for j in range(cols_b):
            terms_str = []
            acc = AlgebraicExpression()
            for k in range(cols_a):
                val_a = matrix_a[i][k]
                val_b = matrix_b[k][j]
                prod = val_a * val_b
                acc = acc + prod
                terms_str.append(f"({val_a.to_latex()}) \\cdot ({val_b.to_latex()})")
            row_res.append(acc)

            calc_expr = " + ".join(terms_str) + f" = {acc.to_latex()}"
            steps.append({
                'title': f'Elemento c_{{{i+1},{j+1}}}',
                'desc': f'Fila {i+1} de A × Columna {j+1} de B: $$c_{{{i+1},{j+1}}} = {calc_expr}$$',
                'matrix': None
            })
        result.append(row_res)

    steps.append({
        'title': 'Matriz Resultante C = A × B',
        'desc': 'Consolidación de todos los elementos calculados:',
        'matrix': matrix_to_latex(result)
    })

    return steps, result


# 4. RUTA PRINCIPAL DE MATRICES

@bp_matrices.route('/matrices', methods=['GET', 'POST'])
def matrices():
    limite = get_system_matrix_limit()

    if request.method == 'GET':
        return render_template(
            'matrices.html',
            modo='gauss',
            filas=2,
            cols=2,
            dim_inv=2,
            filas_a=2,
            cols_a=2,
            filas_b=2,
            cols_b=2,
            inputs={},
            limite_sistema=limite
        )

    modo = request.form.get('modo', 'gauss')
    pasos = []
    resultados = []
    nombres_vars = []
    tipo_solucion = None
    matriz_resultado = None
    user_inputs = {}

    filas = int(request.form.get('filas', 2))
    cols = int(request.form.get('cols', 2))
    dim_inv = int(request.form.get('dim_inv', 2))
    filas_a = int(request.form.get('filas_a', 2))
    cols_a = int(request.form.get('cols_a', 2))
    filas_b = int(request.form.get('filas_b', 2))
    cols_b = int(request.form.get('cols_b', 2))

    try:
        if modo == 'gauss':
            matrix_a = []
            vector_b = []
            variable_names = [f"x_{{{j+1}}}" for j in range(cols)]

            for i in range(filas):
                row = []
                for j in range(cols):
                    key = f'a_{i}_{j}'
                    raw = request.form.get(key, '0')
                    user_inputs[key] = raw
                    coef_str, var_str = extract_coefficient_and_variable(raw)
                    row.append(parse_expression(coef_str))
                    if var_str:
                        m = re.match(r'^([a-zA-Z]+)(\d+)$', var_str)
                        variable_names[j] = f"{m.group(1)}_{{{m.group(2)}}}" if m else var_str
                matrix_a.append(row)
                
                key_b = f'b_{i}'
                raw_b = request.form.get(key_b, '0')
                user_inputs[key_b] = raw_b
                b_coef, _ = extract_coefficient_and_variable(raw_b)
                vector_b.append(parse_expression(b_coef))

            augmented = [matrix_a[i] + [vector_b[i]] for i in range(filas)]
            steps_dict, status, solution, pivot_cols, free_cols = gauss_jordan_with_steps(
                augmented, cols
            )

            for s in steps_dict:
                pasos.append((s['title'], s['desc'], s['matrix']))

            if status == 'inconsistent':
                tipo_solucion = 'inconsistente'
            elif status == 'unique':
                tipo_solucion = 'unica'
                for pc in sorted(solution.keys()):
                    nombres_vars.append(variable_names[pc])
                    resultados.append(solution[pc].to_latex())
            else:
                tipo_solucion = 'infinitas'
                for pc in sorted(solution.keys()):
                    nombres_vars.append(variable_names[pc])
                    resultados.append(solution[pc].to_latex())
                for fc in free_cols:
                    nombres_vars.append(variable_names[fc])
                    resultados.append(f"{variable_names[fc]}\\;\\text{{libre}}")

        elif modo == 'inversa':
            matrix_a = []
            for i in range(dim_inv):
                row = []
                for j in range(dim_inv):
                    key = f'inv_a_{i}_{j}'
                    raw = request.form.get(key, '0')
                    user_inputs[key] = raw
                    coef_str, _ = extract_coefficient_and_variable(raw)
                    row.append(parse_expression(coef_str))
                matrix_a.append(row)

            steps_dict, exists, inv_mat = inverse_with_steps(matrix_a)

            for s in steps_dict:
                pasos.append((s['title'], s['desc'], s['matrix']))

            if exists:
                tipo_solucion = 'invertible'
                matriz_resultado = matrix_to_latex(inv_mat)
            else:
                tipo_solucion = 'singular'

        elif modo == 'multiplicacion':
            matrix_a = []
            for i in range(filas_a):
                row = []
                for j in range(cols_a):
                    key = f'mult_a_{i}_{j}'
                    raw = request.form.get(key, '0')
                    user_inputs[key] = raw
                    coef_str, _ = extract_coefficient_and_variable(raw)
                    row.append(parse_expression(coef_str))
                matrix_a.append(row)

            matrix_b = []
            for i in range(filas_b):
                row = []
                for j in range(cols_b):
                    key = f'mult_b_{i}_{j}'
                    raw = request.form.get(key, '0')
                    user_inputs[key] = raw
                    coef_str, _ = extract_coefficient_and_variable(raw)
                    row.append(parse_expression(coef_str))
                matrix_b.append(row)

            steps_dict, res_mat = matrix_multiplication_with_steps(matrix_a, matrix_b)

            for s in steps_dict:
                pasos.append((s['title'], s['desc'], s['matrix']))

            tipo_solucion = 'multiplicacion'
            matriz_resultado = matrix_to_latex(res_mat)

    except Exception as e:
        pasos.append(("Error de Entrada / Cálculo", f"Ocurrió un error al procesar la solicitud: {str(e)}", None))

    return render_template(
        'matrices.html',
        modo=modo,
        pasos=pasos,
        resultados=resultados,
        nombres_vars=nombres_vars,
        tipo_solucion=tipo_solucion,
        matriz_resultado=matriz_resultado,
        filas=filas,
        cols=cols,
        dim_inv=dim_inv,
        filas_a=filas_a,
        cols_a=cols_a,
        filas_b=filas_b,
        cols_b=cols_b,
        inputs=user_inputs,
        limite_sistema=limite
    )