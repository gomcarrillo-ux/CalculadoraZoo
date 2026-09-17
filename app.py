from flask import Flask, render_template, request
from fractions import Fraction

app = Flask(__name__)

# ==============================================================================
# FUNCIONES AUXILIARES DE PARSEO Y FORMATO
# ==============================================================================

def parse_num(val_str):
    """
    Parsea una cadena a objeto Fraction para mantener precisión exacta.
    Evita el uso de librerías flotantes imprecisas.
    """
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
    """
    Formatea un objeto Fraction a entero o fracción legibles.
    """
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return val.numerator
        return f"{val.numerator}/{val.denominator}"
    return val

def format_matrix(M):
    """
    Convierte todos los elementos de una matriz a su representación formateada.
    """
    return [[format_val(x) for x in row] for row in M]

# ==============================================================================
# MÓDULO 1: ALGORITMOS PROPIOS DE SISTEMAS NUMÉRICOS
# ==============================================================================

def algoritmo_dec_a_base(dec_val, base_destino):
    """
    Procedimiento algebraico: Divisiones Sucesivas.
    Convierte un entero decimal N a cualquier base dividiendo iterativamente 
    entre la base de destino hasta obtener cociente 0.
    Los residuos obtenidos representan los dígitos del número en orden inverso.
    """
    if dec_val == 0:
        return "0"
    
    digitos_hex = "0123456789ABCDEF"
    residuos = []
    cociente = dec_val
    
    while cociente > 0:
        residuo = cociente % base_destino  # residuo r_i
        residuos.append(digitos_hex[residuo])
        cociente = cociente // base_destino # nuevo cociente q_{i+1}
        
    residuos.reverse() # Invertir residuos para formar el número
    return "".join(residuos)

def algoritmo_base_a_dec(num_str, base_origen):
    """
    Procedimiento algebraico: Combinación Lineal / Polinomio de Potencias.
    Calcula N = d_k * b^k + d_{k-1} * b^{k-1} + ... + d_0 * b^0
    donde b es la base de origen y d_i es el valor decimal del dígito en la posición i.
    """
    num_str = str(num_str).strip().upper()
    digitos_hex = "0123456789ABCDEF"
    longitud = len(num_str)
    acumulado_decimal = 0
    
    for i, char in enumerate(num_str):
        potencia = longitud - 1 - i
        valor_digito = digitos_hex.index(char)
        acumulado_decimal += valor_digito * (base_origen ** potencia)
        
    return acumulado_decimal

# ==============================================================================
# MÓDULO 2: OPERACIONES VECTORIALES EN R^n
# ==============================================================================

def vec_add_sub(u, v, operacion='suma'):
    """
    Procedimiento algebraico: Suma/Resta Vectorial en R^n.
    Suma o resta componente a componente: (u1 ± v1, u2 ± v2, ..., un ± vn).
    Requiere que dim(u) == dim(v).
    """
    if len(u) != len(v):
        raise ValueError("Los vectores deben ser de la misma dimensión n.")
    
    if operacion == 'suma':
        return [u[i] + v[i] for i in range(len(u))]
    else:
        return [u[i] - v[i] for i in range(len(u))]

def vec_scalar_mult(k, v):
    """
    Procedimiento algebraico: Multiplicación de un Vector por un Escalar.
    Multiplica el escalar k por cada componente del vector: (k*v1, k*v2, ..., k*vn).
    """
    k_frac = parse_num(k)
    return [k_frac * x for x in v]

# ==============================================================================
# MÓDULO 3: OPERACIONES MATRICIALES BÁSICAS
# ==============================================================================

def mat_add_sub(A, B, operacion='suma'):
    """
    Procedimiento algebraico: Suma/Resta de Matrices M_m_n.
    Suma o resta elemento a elemento: C_ij = A_ij ± B_ij.
    Requiere que ambas matrices tengan exactamente las mismas dimensiones (m x n).
    """
    m_A, n_A = len(A), len(A[0])
    m_B, n_B = len(B), len(B[0])
    
    if m_A != m_B or n_A != n_B:
        raise ValueError("Las matrices deben tener las mismas dimensiones (m x n).")
        
    C = []
    for i in range(m_A):
        fila = []
        for j in range(n_A):
            if operacion == 'suma':
                fila.append(A[i][j] + B[i][j])
            else:
                fila.append(A[i][j] - B[i][j])
        C.append(fila)
    return C

def mat_scalar_mult(k, A):
    """
    Procedimiento algebraico: Producto Escalara-Matriz.
    Multiplica cada entrada A_ij por la constante escalar k.
    """
    k_frac = parse_num(k)
    return [[k_frac * A[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_mult(A, B):
    """
    Procedimiento algebraico: Producto Matricial A_(m x n) * B_(n x p).
    Calcula el producto punto de la fila i de A con la columna j de B:
    C_ij = Suma_{k=1..n} (A_ik * B_kj).
    Valida estrictamente que columnas(A) == filas(B).
    """
    m_A, n_A = len(A), len(A[0])
    m_B, n_B = len(B), len(B[0])
    
    if n_A != m_B:
        raise ValueError(f"No se puede multiplicar: Columnas de A ({n_A}) != Filas de B ({m_B}).")
        
    C = []
    for i in range(m_A):
        fila = []
        for j in range(n_B):
            suma = Fraction(0)
            for k in range(n_A):
                suma += A[i][k] * B[k][j]
            fila.append(suma)
        C.append(fila)
    return C

# ==============================================================================
# MÓDULO 4: RESOLUCIÓN DE SISTEMAS Y COMBINACIÓN LINEAL
# ==============================================================================

def rref_pure(M_in):
    """
    Procedimiento algebraico: Eliminación de Gauss-Jordan (RREF).
    Transforma la matriz aumentada M en su Forma Escalonada Reducida por Filas
    mediante operaciones elementales por fila:
    1. Intercambio de filas.
    2. Multiplicación de una fila por un escalar k != 0.
    3. Suma a una fila el múltiplo de otra fila.
    """
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

def resolver_sistema_ax_b(A, b):
    """
    Procedimiento algebraico: Ecuación Matricial A*x = b.
    Construye la matriz aumentada [A | b] y reutiliza Gauss-Jordan (rref_pure)
    para hallar el vector de incógnitas x.
    """
    matriz_aumentada = []
    for i in range(len(A)):
        matriz_aumentada.append(A[i] + [b[i]])
        
    M_reducida = rref_pure(matriz_aumentada)
    solucion = [M_reducida[i][-1] for i in range(len(A))]
    return M_reducida, solucion

def es_combinacion_lineal(vectores, b):
    """
    Procedimiento algebraico: Evaluación de Combinación Lineal en R^n.
    Determina si b se puede expresar como c1*v1 + c2*v2 + ... + ck*vk.
    Construye el sistema con los vectores v_i como columnas: [v1 v2 ... vk | b]
    y verifica consistencia.
    """
    n = len(b) # Dimensión de R^n
    k = len(vectores) # Cantidad de vectores en el conjunto
    
    # Construir la matriz de coeficientes A de dimensión n x k
    A = []
    for i in range(n):
        fila = [vectores[j][i] for j in range(k)]
        A.append(fila)
        
    M_reducida, escalares = resolver_sistema_ax_b(A, b)
    
    # Verificar si el sistema tiene inconsistencias (0x1 + 0x2 = c != 0)
    inconsistente = False
    for fila in M_reducida:
        coeficientes_cero = all(val == 0 for val in fila[:-1])
        if coeficientes_cero and fila[-1] != 0:
            inconsistente = True
            break
            
    return not inconsistente, M_reducida, escalares

# ==============================================================================
# FUNCIONES EXPLICATIVAS PARA LA INTERFAZ HTML
# ==============================================================================

def explicacion_a_decimal(num_str, base_origen):
    num_str = str(num_str).strip().upper()
    if base_origen == 10:
        return f"El número ya está en base 10: ${num_str}_{{{10}}}$"
    
    digitos_hex = "0123456789ABCDEF"
    pasos_suma = []
    longitud = len(num_str)
    
    for i, digito in enumerate(num_str):
        potencia = longitud - 1 - i
        val_entero = digitos_hex.index(digito)
        pasos_suma.append(f"({val_entero} \\times {base_origen}^{{{potencia}}})")
        
    ecuacion = " + ".join(pasos_suma)
    valor_final = algoritmo_base_a_dec(num_str, base_origen)
    return f"Combinación lineal de potencias de la base:<br><br>${ecuacion} = {valor_final}_{{{10}}}$"

def explicacion_desde_decimal(dec_val, base_destino, nombre_base):
    if dec_val == 0:
        return f"<b>{nombre_base} (Base {base_destino}):</b> El valor es $0_{{{base_destino}}}$"
    
    digitos_hex = "0123456789ABCDEF"
    cociente = dec_val
    lineas = [f"<b>Convertir a {nombre_base} (Base {base_destino}):</b><br>Divisiones sucesivas entre {base_destino}:<br>"]
    residuos = []
    
    while cociente > 0:
        nuevo_cociente = cociente // base_destino
        residuo = cociente % base_destino
        residuo_char = digitos_hex[residuo]
        
        if base_destino == 16 and residuo >= 10:
            residuo_display = f"{residuo} \\rightarrow \\mathrm{{{residuo_char}}}"
        else:
            residuo_display = residuo_char
            
        lineas.append(f"• ${cociente} \\div {base_destino} = {nuevo_cociente}$ con residuo <b>${residuo_display}$</b><br>")
        residuos.append(residuo_char)
        cociente = nuevo_cociente
        
    residuos.reverse()
    resultado_final = "".join(residuos)
    lineas.append(f"<br>Lectura de residuos en orden inverso: <b>${resultado_final}_{{{base_destino}}}$</b>")
    return "".join(lineas)

# ==============================================================================
# RUTAS FLASK
# ==============================================================================

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
        # Uso exclusivo de nuestros algoritmos manuales
        dec_val = algoritmo_base_a_dec(numero_input, base_origen)
        bin_str = algoritmo_dec_a_base(dec_val, 2)
        oct_str = algoritmo_dec_a_base(dec_val, 8)
        hex_str = algoritmo_dec_a_base(dec_val, 16)

        pasos.append((
            "Paso 1: Convertir a Decimal (Base 10) con Combinación Lineal", 
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

    except Exception:
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
                A = []
                b = []
                for i in range(filas):
                    row = [parse_num(request.form.get(f'a_{i}_{j}', '0')) for j in range(cols)]
                    A.append(row)
                    b.append(parse_num(request.form.get(f'b_{i}', '0')))
                
                # Reutiliza resolver_sistema_ax_b que llama a rref_pure
                M_rref, sol = resolver_sistema_ax_b(A, b)
                matriz_origen = [A[i] + [b[i]] for i in range(len(A))]
                
                pasos.append(("Matriz Aumentada Original [A|b]", "Ecuación Matricial $Ax = b$ formateada:", format_matrix(matriz_origen)))
                pasos.append(("Reducción Gauss-Jordan", "Matriz en Forma Escalonada Reducida por Filas (RREF):", format_matrix(M_rref)))
                
                resultados = [str(format_val(x)) for x in sol]
                nombres_vars = [f"x_{{{i+1}}}" for i in range(len(sol))]

            elif metodo in ['vec_auv', 'vec_au_av']:
                A = [[parse_num(request.form.get(f'a_{i}_{j}', '0')) for j in range(cols)] for i in range(filas)]
                u = [parse_num(request.form.get(f'u_{i}', '0')) for i in range(cols)]
                v = [parse_num(request.form.get(f'v_{i}', '0')) for i in range(cols)]

                if metodo == 'vec_auv':
                    suma_uv = vec_add_sub(u, v, 'suma')
                    pasos.append((
                        "Paso 1: Suma de vectores (u + v)", 
                        "Suma vectorial componente a componente en $\\mathbb{R}^n$.", 
                        [[format_val(x)] for x in suma_uv]
                    ))
                    
                    resultado_final = mat_mult(A, [[x] for x in suma_uv])
                    res_flat = [row[0] for row in resultado_final]
                    pasos.append((
                        "Paso 2: Producto Matricial A(u + v)", 
                        "Multiplicación de la matriz $A$ por el vector resultado.", 
                        [[format_val(x)] for x in res_flat]
                    ))

                elif metodo == 'vec_au_av':
                    Au = [row[0] for row in mat_mult(A, [[x] for x in u])]
                    pasos.append((
                        "Paso 1: Calcular Au", 
                        "Producto matricial de $A$ por el vector $u$.", 
                        [[format_val(x)] for x in Au]
                    ))
                    
                    Av = [row[0] for row in mat_mult(A, [[x] for x in v])]
                    pasos.append((
                        "Paso 2: Calcular Av", 
                        "Producto matricial de $A$ por el vector $v$.", 
                        [[format_val(x)] for x in Av]
                    ))
                    
                    res_flat = vec_add_sub(Au, Av, 'suma')
                    pasos.append((
                        "Paso 3: Suma vectorial Au + Av", 
                        "Suma de ambos vectores resultantes.", 
                        [[format_val(x)] for x in res_flat]
                    ))

                nombres_vars = [f"r_{{{i+1}}}" for i in range(len(res_flat))]
                resultados = [str(format_val(val)) for val in res_flat]

            elif metodo == 'comb_lineal':
                # Evaluación de si b es combinación lineal de {v1, v2, ..., vk}
                vectores = []
                for j in range(cols): # Columnas representan la cantidad de vectores v_j
                    v_j = [parse_num(request.form.get(f'v_{i}_{j}', '0')) for i in range(filas)]
                    vectores.append(v_j)
                    
                b = [parse_num(request.form.get(f'b_{i}', '0')) for i in range(filas)]
                
                es_comb, M_rref, escalares = es_combinacion_lineal(vectores, b)
                
                pasos.append(("Sistema Aumentado", "Evaluación de $c_1 v_1 + c_2 v_2 + ... + c_k v_k = b$:", format_matrix(M_rref)))
                
                if es_comb:
                    pasos.append(("Resultado", "¡El vector $b$ SÍ es combinación lineal!", None))
                    resultados = [str(format_val(c)) for c in escalares]
                    nombres_vars = [f"c_{{{i+1}}}" for i in range(len(escalares))]
                else:
                    pasos.append(("Resultado", "El vector $b$ NO es combinación lineal (Sistema Inconsistente).", None))
                    resultados = []

        except Exception as e:
            pasos.append(("Error Algebraico", f"Ocurrió un error al procesar el procedimiento: {str(e)}", None))

    return render_template('matrices.html', 
                           pasos=pasos, 
                           resultados=resultados, 
                           nombres_vars=nombres_vars, 
                           metodo=metodo, 
                           filas=filas, 
                           cols=cols)

if __name__ == '__main__':
    app.run(debug=True)