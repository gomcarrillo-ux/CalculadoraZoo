from flask import Flask, render_template, request
from sympy import Matrix, sympify

app = Flask(__name__)

@app.route('/')
def menu():
    # Renderiza tu menú principal arcade
    return render_template('menu.html')

@app.route('/sistemas', methods=['GET', 'POST'])
def sistemas():
    if request.method == 'GET':
        return render_template('sistemas.html', base=10)
    
    numero_input = request.form.get('numero', '')
    base_origen = int(request.form.get('base', 10))
    
    resultados = {}
    pasos = []
    error = None

    try:
        # Convertir el valor de entrada a Decimal (Base 10)
        dec_val = int(numero_input, base_origen)
        
        # Calcular las representaciones en otras bases
        bin_str = bin(dec_val)[2:]
        oct_str = oct(dec_val)[2:]
        hex_str = hex(dec_val)[2:].upper()

        # Construir el paso a paso
        pasos.append((
            "1. Convertir a Decimal", 
            f"El valor se convierte primero a decimal puro: ${dec_val}_{{{10}}}$"
        ))
        
        pasos.append((
            "2. Conversión a Sistemas Numéricos",
            f"• <b>Binario (Base 2):</b> ${bin_str}_2$<br>"
            f"• <b>Octal (Base 8):</b> ${oct_str}_8$<br>"
            f"• <b>Decimal (Base 10):</b> ${dec_val}_{{{10}}}$<br>"
            f"• <b>Hexadecimal (Base 16):</b> $\mathrm{{{hex_str}}}_{{16}}$"
        ))

        # Guardar resultados finales
        resultados = {
            'Decimal': str(dec_val),
            'Binario': bin_str,
            'Octal': oct_str,
            'Hexadecimal': hex_str
        }

    except ValueError:
        # Mensaje de error si se ingresan letras en bases incorrectas
        error = f"¡Una burbuja reventó! El valor '{numero_input}' no es válido para base {base_origen}."
        
    return render_template('sistemas.html', 
                           resultados=resultados, 
                           pasos=pasos, 
                           error=error, 
                           numero=numero_input, 
                           base=base_origen)


@app.route('/matrices', methods=['GET', 'POST'])
def matrices():
    if request.method == 'GET':
        return render_template('matrices.html')
    
    metodo = request.form.get('metodo')
    filas = int(request.form.get('filas', 2))
    cols = int(request.form.get('cols', 2))
    
    pasos = []
    resultados = []
    nombres_vars = []

    if request.method == 'POST':
        try:
            if metodo in ['gauss', 'gauss_jordan']:
                # Leer matriz aumentada
                matrix_data = []
                for i in range(filas):
                    row = []
                    for j in range(cols):
                        val = request.form.get(f'a_{i}_{j}', '0')
                        row.append(sympify(val))
                    b_val = request.form.get(f'b_{i}', '0')
                    row.append(sympify(b_val))
                    matrix_data.append(row)
                
                M = Matrix(matrix_data)
                pasos.append(("Matriz Original", "Esta es la matriz aumentada con la que iniciamos el hechizo:", M.tolist()))
                
                if metodo == 'gauss_jordan' or metodo == 'gauss':
                    # Aplicar reducción
                    M_rref, pivots = M.rref()
                    pasos.append(("Reducción de Matriz", "Aplicamos eliminación para simplificar la matriz:", M_rref.tolist()))
                    
                    # Extraer variables finales (asumiendo sistema con solución única)
                    resultados = [str(M_rref[i, -1]) for i in range(min(filas, cols))]
                    nombres_vars = [f"x_{{{i+1}}}" for i in range(min(filas, cols))]

            elif metodo in ['vec_auv', 'vec_au_av']:
                # Leer Matriz A
                matrix_A = []
                for i in range(filas):
                    row = []
                    for j in range(cols):
                        val = request.form.get(f'a_{i}_{j}', '0')
                        row.append(sympify(val))
                    matrix_A.append(row)
                A = Matrix(matrix_A)
                
                # Leer Vector u
                vec_u = []
                for i in range(cols):
                    val = request.form.get(f'u_{i}', '0')
                    vec_u.append([sympify(val)])
                u = Matrix(vec_u)
                
                # Leer Vector v
                vec_v = []
                for i in range(cols):
                    val = request.form.get(f'v_{i}', '0')
                    vec_v.append([sympify(val)])
                v = Matrix(vec_v)

                # Lógica separada para A(u+v)
                if metodo == 'vec_auv':
                    suma_uv = u + v
                    pasos.append((
                        "Paso 1: Suma de vectores (u + v)", 
                        "Primero sumamos los vectores $u$ y $v$ elemento a elemento.", 
                        suma_uv.tolist()
                    ))
                    
                    resultado_final = A * suma_uv
                    pasos.append((
                        "Paso 2: Multiplicar A(u + v)", 
                        "Multiplicamos la matriz $A$ por el vector resultante de la suma.", 
                        resultado_final.tolist()
                    ))

                # Lógica separada para Au + Av
                elif metodo == 'vec_au_av':
                    Au = A * u
                    pasos.append((
                        "Paso 1: Calcular Au", 
                        "Multiplicamos la matriz $A$ por el vector $u$.", 
                        Au.tolist()
                    ))
                    
                    Av = A * v
                    pasos.append((
                        "Paso 2: Calcular Av", 
                        "Multiplicamos la matriz $A$ por el vector $v$.", 
                        Av.tolist()
                    ))
                    
                    resultado_final = Au + Av
                    pasos.append((
                        "Paso 3: Sumar los resultados", 
                        "Sumamos los dos vectores resultantes para obtener $Au + Av$.", 
                        resultado_final.tolist()
                    ))

                # Formato de variables para KaTeX
                nombres_vars = [f"r_{{{i+1}}}" for i in range(A.rows)]
                resultados = [str(val) for val in resultado_final]

        except Exception as e:
            pasos.append(("Error Mágico", "Hubo un problema al evaluar las variables. Revisa que las expresiones sean correctas.", None))

    return render_template('matrices.html', 
                           pasos=pasos, 
                           resultados=resultados, 
                           nombres_vars=nombres_vars, 
                           metodo=metodo, 
                           filas=filas, 
                           cols=cols)

if __name__ == '__main__':
    app.run(debug=True)