from flask import Flask, render_template, request
import copy

app = Flask(__name__)

def resolver_gauss_jordan(matriz):
    pasos = []
    filas = len(matriz)
    columnas = len(matriz[0])
    
    pasos.append(("Matriz Original:", copy.deepcopy(matriz)))

    try:
        for i in range(filas):
            pivote = matriz[i][i]
            if pivote == 0:
                return ["Error: Pivote cero encontrado, el sistema no tiene solución única o requiere reordenamiento."], []
            
            for j in range(columnas):
                matriz[i][j] = matriz[i][j] / pivote
            pasos.append((f"Hacer 1 el pivote de la fila {i+1}:", copy.deepcopy(matriz)))

            for k in range(i + 1, filas):
                factor = matriz[k][i]
                for j in range(columnas):
                    matriz[k][j] = matriz[k][j] - factor * matriz[i][j]
                if factor != 0:
                    pasos.append((f"Hacer 0 debajo del pivote en la fila {k+1}:", copy.deepcopy(matriz)))

        for i in range(filas - 1, -1, -1):
            for k in range(i - 1, -1, -1):
                factor = matriz[k][i]
                for j in range(columnas):
                    matriz[k][j] = matriz[k][j] - factor * matriz[i][j]
                if factor != 0:
                    pasos.append((f"Hacer 0 arriba del pivote en la fila {k+1}:", copy.deepcopy(matriz)))

        resultados = [round(matriz[i][-1], 4) for i in range(filas)]
        return pasos, resultados
    except Exception as e:
        return [f"Error al procesar la matriz: {str(e)}"], []

@app.route('/', methods=["GET", "POST"])
def start():
    pasos = None
    resultados = None
    error = None
    matriz_input = ""

    if request.method == "POST":
        matriz_input = request.form.get("txtMatrix", "")
        try:
            lineas = matriz_input.strip().split('\n')
            matriz = [[float(num) for num in linea.split()] for linea in lineas]
            
            if len(set(len(fila) for fila in matriz)) > 1:
                error = "Todas las filas deben tener la misma cantidad de elementos."
            else:
                pasos, resultados = resolver_gauss_jordan(matriz)
                if not resultados:
                    error = pasos[0]
                    pasos = None
        except ValueError:
            error = "Por favor, ingresa solo números válidos separados por espacios."
        except Exception as e:
            error = f"Error inesperado: {str(e)}"

    return render_template("index.html", pasos=pasos, resultados=resultados, error=error, matriz_input=matriz_input)

if __name__ == "__main__":
    app.run(debug=True)