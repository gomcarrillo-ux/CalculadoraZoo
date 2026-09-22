# vectores.py
"""Módulo de vectores: combinación lineal, independencia lineal y linealidad."""
from flask import Blueprint, render_template, request

from matrices import (
    AlgebraicExpression,
    parse_expression,
    format_value,
    format_matrix,
    multiply_matrices,
    rref,
)

bp_vectores = Blueprint('vectores', __name__)


# ==============================================================================
# 1. LÓGICA VECTORIAL
# ==============================================================================

def add_or_subtract_vectors(u, v, operation='add'):
    """Suma o resta dos vectores componente a componente."""
    if len(u) != len(v):
        raise ValueError("Los vectores deben tener la misma dimensión.")
    return [(u[i] + v[i]) if operation == 'add' else (u[i] - v[i])
            for i in range(len(u))]


def find_pivot_columns(reduced_matrix, num_coefficient_cols):
    """
    Devuelve {columna_pivote: fila_pivote} para las primeras
    `num_coefficient_cols` columnas de una matriz en RREF.
    """
    pivots = {}
    for r_idx, row in enumerate(reduced_matrix):
        for c_idx in range(num_coefficient_cols):
            if not row[c_idx].is_zero():
                pivots[c_idx] = r_idx
                break
    return pivots


def build_parametric_solution(reduced, pivots, num_coefficient_cols):
    """
    Construye la solución paramétrica de un sistema consistente con
    variables libres. Devuelve (dict {col_pivote: AlgebraicExpression}, free_cols).
    """
    free_cols = [c for c in range(num_coefficient_cols) if c not in pivots]
    solution = {}
    for pc, pr in pivots.items():
        expr = reduced[pr][-1]  # término constante (lado derecho)
        for fc in free_cols:
            coef = reduced[pr][fc].get_constant_value()
            if coef != 0:
                expr = expr + AlgebraicExpression({f"x{fc+1}": -coef})
        solution[pc] = expr
    return solution, free_cols


def check_linear_combination(vectors, vector_b):
    """
    Determina si b es combinación lineal de los vectores.
    Retorna: (status, reduced, solution_info)
      status ∈ {'unique', 'infinite', 'inconsistent'}
    """
    n = len(vector_b)
    k = len(vectors)
    augmented = [[vectors[j][i] for j in range(k)] + [vector_b[i]] for i in range(n)]
    reduced = rref(augmented)

    for row in reduced:
        if all(row[j].is_zero() for j in range(k)) and not row[-1].is_zero():
            return 'inconsistent', reduced, None

    pivots = find_pivot_columns(reduced, k)

    if len(pivots) == k:
        scalars = [reduced[pivots[j]][-1] for j in range(k)]
        return 'unique', reduced, scalars
    else:
        solution, free_cols = build_parametric_solution(reduced, pivots, k)
        return 'infinite', reduced, (solution, free_cols)


def check_linear_independence(vectors):
    """
    Determina si los vectores son linealmente independientes.
    Retorna: (independent, reduced, relation_info)
    """
    if not vectors:
        return True, [], None

    n = len(vectors[0])
    k = len(vectors)
    augmented = [[vectors[j][i] for j in range(k)] + [AlgebraicExpression()]
                 for i in range(n)]
    reduced = rref(augmented)
    pivots = find_pivot_columns(reduced, k)

    independent = (len(pivots) == k)

    if independent:
        return True, reduced, None

    solution, free_cols = build_parametric_solution(reduced, pivots, k)
    return False, reduced, (solution, free_cols)


# ==============================================================================
# 2. RUTA /vectores
# ==============================================================================

@bp_vectores.route('/vectores', methods=['GET', 'POST'])
def vectores():
    if request.method == 'GET':
        return render_template('vectores.html')

    metodo = request.form.get('metodo', 'comb_lineal')
    num_rows = int(request.form.get('filas', 2))
    num_cols = int(request.form.get('cols', 2))
    pasos, resultados, nombres_vars = [], [], []
    conclusion = None

    try:
        # ------------------------------------------------------------------
        # COMBINACIÓN LINEAL
        # ------------------------------------------------------------------
        if metodo == 'comb_lineal':
            vectors = [
                [parse_expression(request.form.get(f'v_{i}_{j}', '0')) for i in range(num_rows)]
                for j in range(num_cols)
            ]
            vector_b = [parse_expression(request.form.get(f'b_{i}', '0')) for i in range(num_rows)]

            status, reduced, info = check_linear_combination(vectors, vector_b)

            pasos.append((
                "Paso 1: Sistema Aumentado [v₁ v₂ … vₖ | b]",
                "Se plantea la ecuación vectorial x₁v₁ + x₂v₂ + … + xₖvₖ = b como un sistema lineal cuya matriz aumentada tiene los vectores como columnas.",
                format_matrix([[v[i] for v in vectors] + [vector_b[i]] for i in range(num_rows)])
            ))
            pasos.append((
                "Paso 2: Forma Escalonada Reducida (RREF)",
                "Se aplica eliminación de Gauss-Jordan para determinar si el sistema es consistente.",
                format_matrix(reduced)
            ))

            if status == 'unique':
                pasos.append((
                    "Paso 3: Conclusión",
                    "El sistema es consistente y tiene <strong>solución única</strong>. Por lo tanto, <strong>b SÍ es combinación lineal</strong> de los vectores.",
                    None
                ))
                nombres_vars = [f"x_{{{i+1}}}" for i in range(len(info))]
                resultados = [format_value(s) for s in info]
                conclusion = "combinacion_unica"

            elif status == 'infinite':
                solution, free_cols = info
                pasos.append((
                    "Paso 3: Conclusión",
                    "El sistema es consistente y posee <strong>variables libres</strong>. Por lo tanto, <strong>b SÍ es combinación lineal</strong> de infinitas formas distintas. La solución general es:",
                    None
                ))
                for pc in sorted(solution.keys()):
                    nombres_vars.append(f"x_{{{pc+1}}}")
                    resultados.append(solution[pc].to_latex())
                for fc in free_cols:
                    nombres_vars.append(f"x_{{{fc+1}}}")
                    resultados.append(f"\\text{{libre}}")
                conclusion = "combinacion_infinita"

            else:
                pasos.append((
                    "Paso 3: Conclusión",
                    "Aparece una fila [0 … 0 | b] con b ≠ 0. El sistema es inconsistente; por lo tanto, <strong>b NO es combinación lineal</strong> de los vectores.",
                    None
                ))
                conclusion = "no_combinacion"

        # ------------------------------------------------------------------
        # INDEPENDENCIA LINEAL
        # ------------------------------------------------------------------
        elif metodo == 'independencia':
            vectors = [
                [parse_expression(request.form.get(f'v_{i}_{j}', '0')) for i in range(num_rows)]
                for j in range(num_cols)
            ]
            independent, reduced, relation = check_linear_independence(vectors)

            pasos.append((
                "Paso 1: Sistema Homogéneo [v₁ v₂ … vₖ | 0]",
                "Un conjunto de vectores es linealmente independiente si la ecuación x₁v₁ + x₂v₂ + … + xₖvₖ = 0 solo admite la solución trivial. Se plantea Ax = 0.",
                format_matrix([[v[i] for v in vectors] + [AlgebraicExpression()]
                               for i in range(num_rows)])
            ))
            pasos.append((
                "Paso 2: Forma Escalonada Reducida (RREF)",
                "Se reduce la matriz para identificar la presencia de pivotes en todas las columnas.",
                format_matrix(reduced)
            ))

            if independent:
                pasos.append((
                    "Paso 3: Conclusión",
                    "Todas las columnas contienen un pivote. <strong>No hay variables libres</strong>, por lo que Ax = 0 tiene únicamente la solución trivial. El conjunto es <strong>linealmente independiente</strong>.",
                    None
                ))
                conclusion = "independiente"
            else:
                solution, free_cols = relation
                pasos.append((
                    "Paso 3: Conclusión",
                    "Al menos una columna no contiene pivote. <strong>Existen variables libres</strong>, por lo que Ax = 0 tiene soluciones no triviales. El conjunto es <strong>linealmente dependiente</strong>. Una posible relación de dependencia (con la variable libre igual a 1) es:",
                    None
                ))
                # Mostrar la relación de dependencia
                for pc in sorted(solution.keys()):
                    nombres_vars.append(f"x_{{{pc+1}}}")
                    resultados.append(solution[pc].to_latex())
                for fc in free_cols:
                    nombres_vars.append(f"x_{{{fc+1}}}")
                    resultados.append("1")
                conclusion = "dependiente"

        # ------------------------------------------------------------------
        # LINEALIDAD: A(u+v) y Au + Av
        # ------------------------------------------------------------------
        elif metodo in ['vec_auv', 'vec_au_av']:
            matrix_a = [
                [parse_expression(request.form.get(f'a_{i}_{j}', '0')) for j in range(num_cols)]
                for i in range(num_rows)
            ]
            vector_u = [parse_expression(request.form.get(f'u_{i}', '0')) for i in range(num_cols)]
            vector_v = [parse_expression(request.form.get(f'v_{i}', '0')) for i in range(num_cols)]

            if metodo == 'vec_auv':
                vector_sum = add_or_subtract_vectors(vector_u, vector_v, 'add')
                pasos.append((
                    "Paso 1: Suma vectorial u + v",
                    "Se realiza la suma componente a componente entre los vectores u y v.",
                    format_matrix([[x] for x in vector_sum])
                ))
                result_matrix = multiply_matrices(matrix_a, [[x] for x in vector_sum])
                result = [r[0] for r in result_matrix]
                pasos.append((
                    "Paso 2: Producto matricial A(u + v)",
                    "Se multiplica la matriz A por el vector columna resultante (u + v).",
                    format_matrix(result_matrix)
                ))
            else:
                prod_u_mat = multiply_matrices(matrix_a, [[x] for x in vector_u])
                prod_u = [r[0] for r in prod_u_mat]
                pasos.append((
                    "Paso 1: Producto Au",
                    "Multiplicación de la matriz A por el vector u.",
                    format_matrix(prod_u_mat)
                ))
                prod_v_mat = multiply_matrices(matrix_a, [[x] for x in vector_v])
                prod_v = [r[0] for r in prod_v_mat]
                pasos.append((
                    "Paso 2: Producto Av",
                    "Multiplicación de la matriz A por el vector v.",
                    format_matrix(prod_v_mat)
                ))
                result = add_or_subtract_vectors(prod_u, prod_v, 'add')
                pasos.append((
                    "Paso 3: Suma Au + Av",
                    "Se suman los vectores resultantes Au y Av.",
                    format_matrix([[x] for x in result])
                ))

            nombres_vars = [f"r_{{{i+1}}}" for i in range(len(result))]
            resultados = [format_value(x) for x in result]

    except Exception as e:
        pasos.append(("Error de Cálculo",
                      f"Ocurrió un error al procesar las expresiones: {str(e)}",
                      None))

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