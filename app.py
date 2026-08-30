import copy
from fractions import Fraction
from flask import Flask, render_template, request

app = Flask(__name__)


def formatear_fraccion(f):
    if isinstance(f, Fraction):
        if f.denominator == 1:
            return str(f.numerator)
        return f"{f.numerator}/{f.denominator}"
    return str(f)


def matriz_a_strings(matriz):
    return [[formatear_fraccion(val) for val in fila] for fila in matriz]


def resolver_matriz(matriz_input, metodo="gauss_jordan"):
    pasos = []
    matriz = [[Fraction(num) for num in fila] for fila in matriz_input]

    filas = len(matriz)
    columnas = len(matriz[0])

    pasos.append(
        (
            "Matriz Original",
            "Es el sistema de ecuaciones lineal inicial expresado en forma de matriz aumentada.",
            matriz_a_strings(matriz),
        )
    )

    try:
        # --- ELIMINACIÓN HACIA ADELANTE (TRIANGULACIÓN) ---
        for i in range(filas):
            # Pivoteo parcial
            max_fila = i
            for k in range(i + 1, filas):
                if abs(matriz[k][i]) > abs(matriz[max_fila][i]):
                    max_fila = k

            if matriz[max_fila][i] == 0:
                return [
                    "Error: El sistema no tiene solución única (pivote 0 sin posibilidad de intercambio)."
                ], []

            # Intercambio de filas
            if max_fila != i:
                matriz[i], matriz[max_fila] = matriz[max_fila], matriz[i]
                pasos.append(
                    (
                        f"Intercambio de filas: F{i+1} ↔ F{max_fila+1}",
                        f"Se intercambia la fila {i+1} con la fila {max_fila+1} para colocar en la diagonal el pivote de mayor valor absoluto. Esto evita divisiones por cero y reduce errores numéricos.",
                        matriz_a_strings(matriz),
                    )
                )

            # Normalizar el pivote a 1
            pivote = matriz[i][i]
            if pivote != 1:
                for j in range(columnas):
                    matriz[i][j] = matriz[i][j] / pivote
                pasos.append(
                    (
                        f"F{i+1} → F{i+1} / ({formatear_fraccion(pivote)})",
                        f"Se divide toda la fila {i+1} entre su pivote actual ({formatear_fraccion(pivote)}) para convertir el elemento de la diagonal principal en 1 (pivote unitario).",
                        matriz_a_strings(matriz),
                    )
                )

            # Hacer ceros por debajo del pivote
            for k in range(i + 1, filas):
                factor = matriz[k][i]
                if factor != 0:
                    for j in range(columnas):
                        matriz[k][j] = matriz[k][j] - factor * matriz[i][j]
                    signo = "-" if factor > 0 else "+"
                    pasos.append(
                        (
                            f"F{k+1} → F{k+1} {signo} ({formatear_fraccion(abs(factor))}) * F{i+1}",
                            f"Se resta a la fila {k+1} un múltiplo de la fila pivote ({formatear_fraccion(factor)} * F{i+1}) para eliminar la incógnita y obtener un 0 por debajo del pivote.",
                            matriz_a_strings(matriz),
                        )
                    )

        resultados = [Fraction(0)] * filas

        # --- RAMIFICACIÓN SEGÚN EL MÉTODO SELECCIONADO ---
        if metodo == "gauss":
            # Sustitución hacia atrás
            for i in range(filas - 1, -1, -1):
                suma = matriz[i][-1]
                for j in range(i + 1, filas):
                    suma -= matriz[i][j] * resultados[j]
                resultados[i] = suma / matriz[i][i]
                pasos.append(
                    (
                        f"Sustitución hacia atrás para X{i+1}: X{i+1} = {formatear_fraccion(resultados[i])}",
                        f"Con la matriz triangulada, despejamos la variable X{i+1} sustituyendo los valores ya calculados de las variables inferiores.",
                        matriz_a_strings(matriz),
                    )
                )

        elif metodo == "gauss_jordan":
            # Hacer ceros por encima del pivote
            for i in range(filas - 1, -1, -1):
                for k in range(i - 1, -1, -1):
                    factor = matriz[k][i]
                    if factor != 0:
                        for j in range(columnas):
                            matriz[k][j] = (
                                matriz[k][j] - factor * matriz[i][j]
                            )
                        signo = "-" if factor > 0 else "+"
                        pasos.append(
                            (
                                f"F{k+1} → F{k+1} {signo} ({formatear_fraccion(abs(factor))}) * F{i+1}",
                                f"Se elimina el término por encima de la diagonal resta a la fila {k+1} la fila pivote multiplicada por {formatear_fraccion(factor)}, logrando la matriz escalonada reducida.",
                                matriz_a_strings(matriz),
                            )
                        )

            resultados = [matriz[i][-1] for i in range(filas)]

        res_formateados = [formatear_fraccion(r) for r in resultados]
        return pasos, res_formateados

    except Exception as e:
        return [f"Error al procesar la matriz: {str(e)}"], []


@app.route("/", methods=["GET", "POST"])
def start():
    pasos = None
    resultados = None
    error = None
    matriz_input = ""
    metodo = "gauss_jordan"

    if request.method == "POST":
        matriz_input = request.form.get("txtMatrix", "")
        metodo = request.form.get("metodo", "gauss_jordan")

        try:
            lineas = matriz_input.strip().split("\n")
            matriz = [linea.split() for linea in lineas if linea.strip()]

            if len(set(len(fila) for fila in matriz)) > 1:
                error = (
                    "Todas las filas deben tener la misma cantidad de elementos."
                )
            elif len(matriz[0]) != len(matriz) + 1:
                error = f"La matriz debe ser aumentada (N filas × N+1 columnas). Se detectaron {len(matriz)} filas y {len(matriz[0])} columnas."
            else:
                pasos, resultados = resolver_matriz(matriz, metodo)
                if not resultados:
                    error = pasos[0]
                    pasos = None
        except ValueError:
            error = "Asegúrate de ingresar valores numéricos válidos (ej: 2, -3, 0.5 o 1/3) separados por espacios."
        except Exception as e:
            error = f"Error inesperado: {str(e)}"

    return render_template(
        "index.html",
        pasos=pasos,
        resultados=resultados,
        error=error,
        matriz_input=matriz_input,
        metodo=metodo,
    )


if __name__ == "__main__":
    app.run(debug=True)