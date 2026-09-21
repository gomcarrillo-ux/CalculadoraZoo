# vectores.py
"""Módulo de operaciones vectoriales. Reutiliza el motor algebraico de matrices."""
from flask import Blueprint, render_template, request

from matrices import (
    parse_expression,
    format_value,
    multiply_matrices,
)

bp_vectores = Blueprint('vectores', __name__)


# ==============================================================================
# LÓGICA VECTORIAL
# ==============================================================================

def add_or_subtract_vectors(vector_u, vector_v, operation='add'):
    if len(vector_u) != len(vector_v):
        raise ValueError("Vectors must have the same dimension n.")
    if operation == 'add':
        return [vector_u[i] + vector_v[i] for i in range(len(vector_u))]
    return [vector_u[i] - vector_v[i] for i in range(len(vector_u))]


def scalar_multiply_vector(scalar, vector):
    scalar_expression = parse_expression(scalar)
    return [scalar_expression * component for component in vector]


# ==============================================================================
# RUTA /vectores
# ==============================================================================

@bp_vectores.route('/vectores', methods=['GET', 'POST'])
def vectores():
    if request.method == 'GET':
        return render_template('vectores.html')

    method = request.form.get('metodo')
    num_rows = int(request.form.get('filas', 2))
    num_cols = int(request.form.get('cols', 2))
    steps, results, variable_names = [], [], []

    if request.method == 'POST':
        try:
            matrix_a = [
                [
                    parse_expression(request.form.get(f'a_{i}_{j}', '0'))
                    for j in range(num_cols)
                ]
                for i in range(num_rows)
            ]
            vector_u = [
                parse_expression(request.form.get(f'u_{i}', '0'))
                for i in range(num_cols)
            ]
            vector_v = [
                parse_expression(request.form.get(f'v_{i}', '0'))
                for i in range(num_cols)
            ]

            if method == 'vec_auv':
                vector_sum = add_or_subtract_vectors(vector_u, vector_v, 'add')
                steps.append((
                    "Paso 1: Suma de vectores (u + v)",
                    "Suma vectorial componente a componente:",
                    [[format_value(x)] for x in vector_sum],
                ))
                flat_result = [
                    row[0]
                    for row in multiply_matrices(
                        matrix_a, [[x] for x in vector_sum]
                    )
                ]
                steps.append((
                    "Paso 2: Producto Matricial A(u + v)",
                    "Resultado final:",
                    [[format_value(x)] for x in flat_result],
                ))

            elif method == 'vec_au_av':
                product_au = [
                    row[0]
                    for row in multiply_matrices(
                        matrix_a, [[x] for x in vector_u]
                    )
                ]
                steps.append((
                    "Paso 1: Calcular Au",
                    "Producto de $A$ por $u$:",
                    [[format_value(x)] for x in product_au],
                ))
                product_av = [
                    row[0]
                    for row in multiply_matrices(
                        matrix_a, [[x] for x in vector_v]
                    )
                ]
                steps.append((
                    "Paso 2: Calcular Av",
                    "Producto de $A$ por $v$:",
                    [[format_value(x)] for x in product_av],
                ))
                flat_result = add_or_subtract_vectors(
                    product_au, product_av, 'add'
                )
                steps.append((
                    "Paso 3: Suma Au + Av",
                    "Suma vectorial final:",
                    [[format_value(x)] for x in flat_result],
                ))

            variable_names = [f"r_{{{i+1}}}" for i in range(len(flat_result))]
            results = [format_value(x) for x in flat_result]

        except Exception as exception:
            steps.append((
                "Error Algebraico",
                f"Sintaxis o cálculo no válido: {str(exception)}",
                None,
            ))

    return render_template(
        'vectores.html',
        pasos=steps,
        resultados=results,
        nombres_vars=variable_names,
        metodo=method,
        filas=num_rows,
        cols=num_cols,
    )