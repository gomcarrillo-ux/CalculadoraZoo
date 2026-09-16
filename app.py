from flask import Flask, render_template, request
from fractions import Fraction

app = Flask(__name__)

def parse_num(val_str):
    val_str = str(val_str).strip()
    if not val_str:
        return Fraction(0)
    try:
        return Fraction(val_str)
    except ValueError:
        try:
            return Fraction(float(val_str)).limit_denominator()
        except ValueError:
            return Fraction(0)

def format_val(val):
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return val.numerator
        return f"{val.numerator}/{val.denominator}"
    return val

def format_matrix(M):
    return [[format_val(x) for x in row] for row in M]

def mat_vec_mult(A, v):
    filas = len(A)
    cols = len(v)
    resultado = []
    for i in range(filas):
        suma = Fraction(0)
        for j in range(cols):
            suma += A[i][j] * v[j]
        resultado.append(suma)
    return resultado

def vec_add(u, v):
    return [u[i] + v[i] for i in range(len(u))]

def rref_pure(M_in):
    A = [[x for x in row] for row in M_in]
    rows = len(A)
    cols = len(A[0])
    r = 0
    
    for c in range(cols - 1):
        if r >= rows:
            break
        
        pivot_row = r
        while pivot_row < rows and A[pivot_row][c] == 0:
            pivot_row += 1
            
        if pivot_row == rows:
            continue
            
        A[r], A[pivot_row] = A[pivot_row], A[r]
        
        pivot_val = A[r][c]
        A[r] = [x / pivot_val for x in A[r]]
        
        for i in range(rows):
            if i != r:
                factor = A[i][c]
                A[i] = [A[i][j] - factor * A[r][j] for j in range(cols)]
                
        r += 1
        
    return A

def explicacion_a_decimal(num_str, base_origen):
    """Genera el texto paso a paso para convertir a base 10."""
    num_str = str(num_str).strip().upper()
    if base_origen == 10:
        return f"El número ya está en base 10: ${num_str}_{{{10}}}$"
    
    pasos_suma = []
    longitud = len(num_str)
    for i, digito in enumerate(num_str):
        potencia = longitud - 1 - i
        val_entero = int(digito, base_origen)
        pasos_suma.append(f"({val_entero} \\times {base_origen}^{{{potencia}}})")
        
    ecuacion = " + ".join(pasos_suma)
    valor_final = int(num_str, base_origen)
    return f"Multiplicamos cada dígito por la base elevada a su posición de derecha a izquierda (empezando en 0):<br><br>${ecuacion} = {valor_final}_{{{10}}}$"

def explicacion_desde_decimal(dec_val, base_destino, nombre_base):
    """Genera las divisiones sucesivas para convertir a la base destino."""
    if dec_val == 0:
        return f"<b>{nombre_base} (Base {base_destino}):</b> El valor es $0_{{{base_destino}}}$"
    
    cociente = dec_val
    lineas = [f"<b>Convertir a {nombre_base} (Base {base_destino}):</b><br>Dividimos sucesivamente entre {base_destino} hasta que el cociente sea 0:<br>"]
    residuos = []
    
    while cociente > 0:
        nuevo_cociente = cociente // base_destino
        residuo = cociente % base_destino
        
        residuo_str = str(residuo)
        if base_destino == 16 and residuo >= 10:
            residuo_str = chr(55 + residuo) # Convierte 10 a A, 11 a B, etc.
            residuo_display = f"{residuo} \\rightarrow \\mathrm{{{residuo_str}}}"
        else:
            residuo_display = residuo_str
            
        lineas.append(f"• ${cociente} \\div {base_destino} = {nuevo_cociente}$ con residuo <b>${residuo_display}$</b><br>")
        residuos.append(residuo_str)
        cociente = nuevo_cociente
        
    residuos.reverse()
    resultado_final = "".join(residuos)
    lineas.append(f"<br>Leyendo los residuos de abajo hacia arriba obtenemos: <b>${resultado_final}_{{{base_destino}}}$</b>")
    return "".join(lineas)

@app.route('/')
def menu():
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
        # Conversiones internas nativas
        dec_val = int(numero_input, base_origen)
        bin_str = bin(dec_val)[2:]
        oct_str = oct(dec_val)[2:]
        hex_str = hex(dec_val)[2:].upper()

        # Generar las explicaciones detalladas
        pasos.append((
            "Paso 1: Convertir a Decimal (Base 10)", 
            explicacion_a_decimal(numero_input, base_origen)
        ))
        
        pasos.append((
            "Paso 2: Convertir de Decimal a Binario",
            explicacion_desde_decimal(dec_val, 2, "Binario")
        ))

        pasos.append((
            "Paso 3: Convertir de Decimal a Octal",
            explicacion_desde_decimal(dec_val, 8, "Octal")
        ))
        
        pasos.append((
            "Paso 4: Convertir de Decimal a Hexadecimal",
            explicacion_desde_decimal(dec_val, 16, "Hexadecimal")
        ))

        resultados = {
            'Decimal': str(dec_val),
            'Binario': bin_str,
            'Octal': oct_str,
            'Hexadecimal': hex_str
        }

    except ValueError:
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
                matrix_data = []
                for i in range(filas):
                    row = []
                    for j in range(cols):
                        val = request.form.get(f'a_{i}_{j}', '0')
                        row.append(parse_num(val))
                    b_val = request.form.get(f'b_{i}', '0')
                    row.append(parse_num(b_val))
                    matrix_data.append(row)
                
                pasos.append(("Matriz Original", "Esta es la matriz aumentada con la que iniciamos el hechizo:", format_matrix(matrix_data)))
                
                M_rref = rref_pure(matrix_data)
                pasos.append(("Reducción de Matriz", "Aplicamos eliminación para simplificar la matriz:", format_matrix(M_rref)))
                
                resultados = [str(format_val(M_rref[i][-1])) for i in range(min(filas, cols))]
                nombres_vars = [f"x_{{{i+1}}}" for i in range(min(filas, cols))]

            elif metodo in ['vec_auv', 'vec_au_av']:
                A = []
                for i in range(filas):
                    row = []
                    for j in range(cols):
                        val = request.form.get(f'a_{i}_{j}', '0')
                        row.append(parse_num(val))
                    A.append(row)
                
                u = [parse_num(request.form.get(f'u_{i}', '0')) for i in range(cols)]
                v = [parse_num(request.form.get(f'v_{i}', '0')) for i in range(cols)]

                if metodo == 'vec_auv':
                    suma_uv = vec_add(u, v)
                    pasos.append((
                        "Paso 1: Suma de vectores (u + v)", 
                        "Primero sumamos los vectores $u$ y $v$ elemento a elemento.", 
                        [[format_val(x)] for x in suma_uv]
                    ))
                    
                    resultado_final = mat_vec_mult(A, suma_uv)
                    pasos.append((
                        "Paso 2: Multiplicar A(u + v)", 
                        "Multiplicamos la matriz $A$ por el vector resultante de la suma.", 
                        [[format_val(x)] for x in resultado_final]
                    ))

                elif metodo == 'vec_au_av':
                    Au = mat_vec_mult(A, u)
                    pasos.append((
                        "Paso 1: Calcular Au", 
                        "Multiplicamos la matriz $A$ por el vector $u$.", 
                        [[format_val(x)] for x in Au]
                    ))
                    
                    Av = mat_vec_mult(A, v)
                    pasos.append((
                        "Paso 2: Calcular Av", 
                        "Multiplicamos la matriz $A$ por el vector $v$.", 
                        [[format_val(x)] for x in Av]
                    ))
                    
                    resultado_final = vec_add(Au, Av)
                    pasos.append((
                        "Paso 3: Sumar los resultados", 
                        "Sumamos los dos vectores resultantes para obtener $Au + Av$.", 
                        [[format_val(x)] for x in resultado_final]
                    ))

                nombres_vars = [f"r_{{{i+1}}}" for i in range(len(A))]
                resultados = [str(format_val(val)) for val in resultado_final]

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