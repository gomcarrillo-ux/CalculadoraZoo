# vectores.py
"""Módulo de vectores: combinación lineal, independencia lineal y linealidad."""
from flask import Blueprint, render_template, request

from matrices import (
    AlgebraicExpression,
    parse_expression,
    format_value,
    multiply_matrices,
)

bp_vectores = Blueprint('vectores', __name__)


# 1. FUNCIONALIDADES AUXILIARES Y FORMATO LATEX

def _matrix_copy(matrix):
    return [row[:] for row in matrix]


def matrix_to_latex(matrix):
    """Convierte una matriz 2D de expresiones algebraicas a formato KaTeX bmatrix."""
    if not matrix:
        return None
    rows = []
    for row in matrix:
        row_str = " & ".join(x.to_latex() if hasattr(x, 'to_latex') else str(x) for x in row)
        rows.append(row_str)
    return "\\begin{bmatrix} " + " \\\\ ".join(rows) + " \\end{bmatrix}"


# 2. MOTOR DE GAUSS-JORDAN

def gauss_jordan_vectores(augmented, num_vars):
    """Motor Gauss-Jordan corregido que maneja variables libres sin errores de tipo."""
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
        "Se escribe la ecuación vectorial como matriz aumentada [A|b].",
        aug
    )

    pivot_positions = []
    pivot_row = 0

    # ---------- ELIMINACIÓN HACIA ADELANTE ----------
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
                f"F<sub>{pivot_row+1}</sub> ↔ F<sub>{pivot_candidate+1}</sub> para posicionar el pivote.",
                aug
            )

        pivot_val = aug[pivot_row][col]
        if not (pivot_val == AlgebraicExpression.parse("1")):
            aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
            add_step(
                "Escalar fila pivote",
                f"F<sub>{pivot_row+1}</sub> = F<sub>{pivot_row+1}</sub> ÷ ({pivot_val.to_latex()})",
                aug
            )

        pivot_positions.append((pivot_row, col))

        for i in range(pivot_row + 1, m):
            factor = aug[i][col]
            if not factor.is_zero():
                aug[i] = [aug[i][j] - factor * aug[pivot_row][j] for j in range(n + 1)]
                add_step(
                    "Eliminar debajo del pivote",
                    f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pivot_row+1}</sub>",
                    aug
                )

        pivot_row += 1

    add_step("Forma Escalonada por Filas", "Matriz en forma escalonada.", aug)

    # ---------- VERIFICAR CONSISTENCIA ----------
    for i in range(m):
        if all(aug[i][j].is_zero() for j in range(n)) and not aug[i][n].is_zero():
            add_step(
                "Sistema Inconsistente",
                "Fila del tipo [0 … 0 | b] con b ≠ 0. El sistema NO tiene solución.",
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
                    f"F<sub>{i+1}</sub> = F<sub>{i+1}</sub> − ({factor.to_latex()})·F<sub>{pr+1}</sub>",
                    aug
                )

    add_step(
        "Forma Escalonada Reducida (RREF)",
        "Matriz reducida por filas (RREF). Permite despejar las variables.",
        aug
    )

    pivot_cols = [pc for _, pc in pivot_positions]
    free_cols = [c for c in range(n) if c not in pivot_cols]

    if not free_cols:
        solution = {}
        for pr, pc in pivot_positions:
            solution[pc] = aug[pr][n]
        add_step("Solución Única", "No existen variables libres.", None)
        return steps, 'unique', solution, pivot_cols, free_cols

    solution = {}
    for pr, pc in pivot_positions:
        expr = aug[pr][n]
        for fc in free_cols:
            coef = aug[pr][fc]
            if not coef.is_zero():
                expr = expr + AlgebraicExpression({f"x{fc+1}": -coef.get_constant_value()})
        solution[pc] = expr

    free_names = ", ".join(f"x<sub>{c+1}</sub>" for c in free_cols)
    add_step(
        "Infinitas Soluciones",
        f"Existen {len(free_cols)} variable(s) libre(s): {free_names}.",
        None
    )
    return steps, 'infinite', solution, pivot_cols, free_cols


# 3. FUNCIONES VECTORIALES

def add_or_subtract_vectors(u, v, operation='add'):
    if len(u) != len(v):
        raise ValueError("Los vectores deben tener la misma dimensión.")
    return [(u[i] + v[i]) if operation == 'add' else (u[i] - v[i])
            for i in range(len(u))]


def check_linear_combination(vectors, vector_b):
    n = len(vector_b)
    k = len(vectors)
    augmented = [[vectors[j][i] for j in range(k)] + [vector_b[i]] for i in range(n)]
    steps_list, status, solution_dict, pivot_cols, free_cols = gauss_jordan_vectores(augmented, k)
    return status, steps_list, (solution_dict, free_cols)


def check_linear_independence(vectors):
<<<<<<< HEAD
    if not vectors:
=======
    """
    Determina si los vectores son linealmente independientes.
    Retorna: (independent, reduced, relation_info)
    """
    if not vectors or not vectors[0]:
>>>>>>> 840160125716e8761b294d107b7435926de6277b
        return True, [], None

    n = len(vectors[0])
    k = len(vectors)
    augmented = [[vectors[j][i] for j in range(k)] + [AlgebraicExpression()]
                 for i in range(n)]

    steps_list, status, solution_dict, pivot_cols, free_cols = gauss_jordan_vectores(augmented, k)
    independent = (status == 'unique')
    return independent, steps_list, (solution_dict, free_cols)


# 4. RUTA DE FLASK /vectores

@bp_vectores.route('/vectores', methods=['GET', 'POST'])
def vectores():
    if request.method == 'GET':
        return render_template('vectores.html')

    pasos, resultados, nombres_vars = [], [], []
    conclusion = None
    metodo = request.form.get('metodo', 'comb_lineal')

    try:
<<<<<<< HEAD
=======
        num_rows = int(request.form.get('filas', 2))
        num_cols = int(request.form.get('cols', 2))

        # COMBINACIÓN LINEAL
>>>>>>> 840160125716e8761b294d107b7435926de6277b
        if metodo == 'comb_lineal':
            vectors = [
                [parse_expression(request.form.get(f'v_{i}_{j}', '0')) for i in range(num_rows)]
                for j in range(num_cols)
            ]
            vector_b = [parse_expression(request.form.get(f'b_{i}', '0')) for i in range(num_rows)]

            status, steps_list, info = check_linear_combination(vectors, vector_b)

            pasos.append((
                "Planteamiento: Ecuación Vectorial",
                "Se plantea la ecuación x₁v₁ + x₂v₂ + … + xₖvₖ = b como un sistema de ecuaciones lineales:",
                None
            ))

            for s in steps_list:
                pasos.append((
                    s['title'],
                    s['desc'],
                    matrix_to_latex(s['matrix']) if s['matrix'] is not None else None
                ))

            if status == 'unique':
                pasos.append((
                    "Conclusión Final",
                    "El sistema es consistente y tiene <strong>solución única</strong>. Por lo tanto, <strong>b SÍ es combinación lineal</strong>.",
                    None
                ))
                solution_dict, free_cols = info
                for pc in sorted(solution_dict.keys()):
                    nombres_vars.append(f"x_{{{pc+1}}}")
                    resultados.append(solution_dict[pc].to_latex())
                conclusion = "combinacion_unica"

            elif status == 'infinite':
                solution_dict, free_cols = info
                pasos.append((
                    "Conclusión Final",
                    "El sistema es consistente y posee <strong>variables libres</strong>. Por lo tanto, <strong>b SÍ es combinación lineal</strong> de infinitas formas.",
                    None
                ))
                for pc in sorted(solution_dict.keys()):
                    nombres_vars.append(f"x_{{{pc+1}}}")
                    resultados.append(solution_dict[pc].to_latex())
                for fc in free_cols:
                    nombres_vars.append(f"x_{{{fc+1}}}")
<<<<<<< HEAD
                    resultados.append("\\text{libre}")
=======
                    resultados.append(r"\text{libre}")
>>>>>>> 840160125716e8761b294d107b7435926de6277b
                conclusion = "combinacion_infinita"

            else:
                pasos.append((
                    "Conclusión Final",
                    "El sistema es inconsistente. Por lo tanto, <strong>b NO es combinación lineal</strong> de los vectores.",
                    None
                ))
                conclusion = "no_combinacion"

        elif metodo == 'independencia':
            vectors = [
                [parse_expression(request.form.get(f'v_{i}_{j}', '0')) for i in range(num_rows)]
                for j in range(num_cols)
            ]
            independent, steps_list, relation = check_linear_independence(vectors)

            pasos.append((
                "Planteamiento: Sistema Homogéneo",
                "Se plantea x₁v₁ + x₂v₂ + … + xₖvₖ = 0 para determinar si solo existe la solución trivial.",
                None
            ))

            for s in steps_list:
                pasos.append((
                    s['title'],
                    s['desc'],
                    matrix_to_latex(s['matrix']) if s['matrix'] is not None else None
                ))

            if independent:
                pasos.append((
                    "Conclusión Final",
                    "No hay variables libres. El conjunto es <strong>linealmente independiente</strong>.",
                    None
                ))
                conclusion = "independiente"
            else:
                solution_dict, free_cols = relation
                pasos.append((
<<<<<<< HEAD
                    "Conclusión Final",
                    "Existen variables libres. El conjunto es <strong>linealmente dependiente</strong>.",
                    None
                ))
                for pc in sorted(solution_dict.keys()):
=======
                    "Paso 3: Conclusión",
                    "Al menos una columna no contiene pivote. <strong>Existen variables libres</strong>, por lo que Ax = 0 tiene soluciones no triviales. El conjunto es <strong>linealmente dependiente</strong>. Una posible relación de dependencia (asumiendo variable libre = 1) es:",
                    None
                ))
                for pc in sorted(solution.keys()):
>>>>>>> 840160125716e8761b294d107b7435926de6277b
                    nombres_vars.append(f"x_{{{pc+1}}}")
                    resultados.append(solution_dict[pc].to_latex())
                for fc in free_cols:
                    nombres_vars.append(f"x_{{{fc+1}}}")
                    resultados.append("1")
                conclusion = "dependiente"

        elif metodo in ['vec_auv', 'vec_au_av']:
            matrix_a = [
                [parse_expression(request.form.get(f'a_{i}_{j}', '0')) for j in range(num_cols)]
                for i in range(num_rows)
            ]
            vector_u = [parse_expression(request.form.get(f'u_{j}', '0')) for j in range(num_cols)]
            vector_v = [parse_expression(request.form.get(f'v_{j}', '0')) for j in range(num_cols)]

            if metodo == 'vec_auv':
                vector_sum = add_or_subtract_vectors(vector_u, vector_v, 'add')
                pasos.append((
                    "Paso 1: Suma vectorial u + v",
                    "Se suman componente a componente los vectores u y v:",
                    matrix_to_latex([[x] for x in vector_sum])
                ))
                result_matrix = multiply_matrices(matrix_a, [[x] for x in vector_sum])
                result = [r[0] for r in result_matrix]
                pasos.append((
                    "Paso 2: Producto A(u + v)",
                    "Se multiplica la matriz A por el vector suma (u + v):",
                    matrix_to_latex(result_matrix)
                ))
            else:
                prod_u_mat = multiply_matrices(matrix_a, [[x] for x in vector_u])
                prod_u = [r[0] for r in prod_u_mat]
                pasos.append((
                    "Paso 1: Producto Au",
                    "Multiplicación de la matriz A por el vector u:",
                    matrix_to_latex(prod_u_mat)
                ))
                prod_v_mat = multiply_matrices(matrix_a, [[x] for x in vector_v])
                prod_v = [r[0] for r in prod_v_mat]
                pasos.append((
                    "Paso 2: Producto Av",
                    "Multiplicación de la matriz A por el vector v:",
                    matrix_to_latex(prod_v_mat)
                ))
                result = add_or_subtract_vectors(prod_u, prod_v, 'add')
                pasos.append((
                    "Paso 3: Suma Au + Av",
                    "Se suman los vectores resultantes Au y Av:",
                    matrix_to_latex([[x] for x in result])
                ))

            nombres_vars = [f"r_{{{i+1}}}" for i in range(len(result))]
            resultados = [format_value(x) for x in result]

    except Exception as e:
<<<<<<< HEAD
        pasos.append(("Error de Cálculo", f"Ocurrió un error al procesar las expresiones: {str(e)}", None))
=======
        num_rows = 2
        num_cols = 2
        pasos.append((
            "Error de Cálculo",
            f"Ocurrió un error al procesar las expresiones: {str(e)}",
            None
        ))
>>>>>>> 840160125716e8761b294d107b7435926de6277b

    return render_template(
        'vectores.html',
        pasos=pasos,
        resultados=resultados,
        nombres_vars=nombres_vars,
        metodo=metodo,
        filas=num_rows,
        cols=num_cols,
        conclusion=conclusion,
    )