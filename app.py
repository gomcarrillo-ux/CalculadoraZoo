import re
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

def format_parametric_expr(indep, coefs_libres, variables_libres_nombres):
    """Construye la expresión algebraica paramétrica para variables dependientes."""
    terms = []
    if indep != 0:
        terms.append(formatear_fraccion(indep))

    for col_lib, coef in coefs_libres.items():
        if coef == 0:
            continue
        param = variables_libres_nombres[col_lib]
        abs_coef = abs(coef)
        coef_str = formatear_fraccion(abs_coef)

        if coef_str == "1":
            term_str = param
        else:
            term_str = f"{coef_str}*{param}"

        if coef > 0:
            if not terms:
                terms.append(term_str)
            else:
                terms.append(f"+ {term_str}")
        else:
            if not terms:
                terms.append(f"-{term_str}")
            else:
                terms.append(f"- {term_str}")

    if not terms:
        return "0"
    return " ".join(terms)

def parse_ecuaciones(texto):
    """
    Toma un texto con ecuaciones (ej: "2x + y = 5") y lo convierte
    en una matriz aumentada de fracciones, detectando los nombres de las variables.
    """
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]

    todas_vars = set(re.findall(r'[a-zA-Z_]\w*', texto))
    vars_ordenadas = sorted(list(todas_vars))
    
    matriz = []
    
    for linea in lineas:
        if '=' not in linea:
            raise ValueError(f"La ecuación '{linea}' no tiene el signo igual (=).")
        
        lhs, rhs = linea.split('=', 1)
        
        def parse_lado(lado_str, multiplicador=1):
            lado_str = lado_str.replace(" ", "")
            if not lado_str.startswith('+') and not lado_str.startswith('-'):
                lado_str = '+' + lado_str
            
            patron = r'([+-])(\d*\.?\d*(?:/\d+)?)([a-zA-Z_]\w*)?'
            terminos = re.findall(patron, lado_str)
            
            coeficientes = {v: Fraction(0) for v in vars_ordenadas}
            constante = Fraction(0)
            
            for signo, num_str, var in terminos:
                if num_str == '':
                    num = Fraction(1)
                elif '/' in num_str:
                    num = Fraction(num_str)
                else:
                    num = Fraction(num_str)
                
                if signo == '-':
                    num = -num
                    
                num = num * multiplicador
                
                if var:
                    coeficientes[var] += num
                else:
                    constante += num
                    
            return coeficientes, constante

        coef_lhs, const_lhs = parse_lado(lhs, 1)
        coef_rhs, const_rhs = parse_lado(rhs, -1)
        
        fila = []
        for v in vars_ordenadas:
            fila.append(coef_lhs[v] + coef_rhs[v])
            
        termino_independiente = -(const_lhs + const_rhs)
        fila.append(termino_independiente)
        matriz.append(fila)
        
    return matriz, vars_ordenadas

def resolver_matriz(matriz_input, metodo="gauss_jordan", nombres_vars=None):
    pasos = []
    matriz = [[Fraction(num) for num in fila] for fila in matriz_input]

    filas = len(matriz)
    columnas = len(matriz[0])
    num_vars = columnas - 1

    if not nombres_vars:
        nombres_vars = [f"X{i+1}" for i in range(num_vars)]

    pasos.append(
        (
            "Matriz Original",
            f"Matriz aumentada representando las variables: {', '.join(nombres_vars)}",
            matriz_a_strings(matriz),
        )
    )

    pivote_filas = []
    piv_row = 0

    for col in range(num_vars):
        if piv_row >= filas:
            break

        max_fila = piv_row
        for k in range(piv_row + 1, filas):
            if abs(matriz[k][col]) > abs(matriz[max_fila][col]):
                max_fila = k

        if matriz[max_fila][col] == 0:
            continue

        if max_fila != piv_row:
            matriz[piv_row], matriz[max_fila] = matriz[max_fila], matriz[piv_row]
            pasos.append((
                f"Intercambio: F{piv_row+1} ↔ F{max_fila+1}",
                "Se intercambian filas para posicionar el mejor pivote.",
                matriz_a_strings(matriz),
            ))

        pivote = matriz[piv_row][col]
        if pivote != 1:
            for j in range(columnas):
                matriz[piv_row][j] /= pivote
            pasos.append((
                f"F{piv_row+1} → F{piv_row+1} / ({formatear_fraccion(pivote)})",
                "Normalizamos la fila para que el pivote sea 1.",
                matriz_a_strings(matriz),
            ))

        for k in range(filas):
            if k == piv_row:
                continue
            if metodo == "gauss" and k < piv_row:
                continue

            factor = matriz[k][col]
            if factor != 0:
                for j in range(columnas):
                    matriz[k][j] -= factor * matriz[piv_row][j]
                signo = "-" if factor > 0 else "+"
                pasos.append((
                    f"F{k+1} → F{k+1} {signo} ({formatear_fraccion(abs(factor))}) * F{piv_row+1}",
                    f"Eliminamos el término de la variable {nombres_vars[col]} en la fila {k+1}.",
                    matriz_a_strings(matriz),
                ))

        pivote_filas.append((piv_row, col))
        piv_row += 1

    for r in range(filas):
        es_cero_coefs = all(matriz[r][c] == 0 for c in range(num_vars))
        if es_cero_coefs and matriz[r][-1] != 0:
            pasos.append((
                "Contradicción Detectada",
                f"Obtuvimos 0 = {formatear_fraccion(matriz[r][-1])}. El sistema no tiene solución.",
                matriz_a_strings(matriz),
            ))
            return pasos, [], [], "El sistema NO TIENE SOLUCIÓN (Inconsistente)."

    cols_pivote = {col: r for r, col in pivote_filas}
    vars_libres = [c for c in range(num_vars) if c not in cols_pivote]

    if not vars_libres and len(pivote_filas) == num_vars:
        resultados_dict = {}
        if metodo == "gauss":
            for r, c in reversed(pivote_filas):
                suma = matriz[r][-1]
                for c_next in range(c + 1, num_vars):
                    suma -= matriz[r][c_next] * resultados_dict[c_next]
                resultados_dict[c] = suma
                pasos.append((
                    f"Sustitución para {nombres_vars[c]}",
                    f"{nombres_vars[c]} = {formatear_fraccion(suma)}.",
                    matriz_a_strings(matriz),
                ))
        else:
            for r, c in pivote_filas:
                resultados_dict[c] = matriz[r][-1]

        res_finales = [formatear_fraccion(resultados_dict[i]) for i in range(num_vars)]
        return pasos, res_finales, nombres_vars, None

    if metodo == "gauss":
        for r, c in reversed(pivote_filas):
            for k in range(r - 1, -1, -1):
                factor = matriz[k][c]
                if factor != 0:
                    for j in range(columnas):
                        matriz[k][j] -= factor * matriz[r][j]

    nombres_parametros = {col_lib: f"t{idx+1}" for idx, col_lib in enumerate(vars_libres)}

    res_finales = []
    for v in range(num_vars):
        if v in vars_libres:
            res_finales.append(f"{nombres_parametros[v]} (Variable libre)")
        else:
            r = cols_pivote[v]
            indep = matriz[r][-1]
            coefs_libres = {col_lib: -matriz[r][col_lib] for col_lib in vars_libres}
            expr = format_parametric_expr(indep, coefs_libres, nombres_parametros)
            res_finales.append(expr)

    msg_info = f"SISTEMA COMPATIBLE INDETERMINADO: Infinitas soluciones dependientes de {len(vars_libres)} parámetro(s)."
    return pasos, res_finales, nombres_vars, msg_info

@app.route("/", methods=["GET", "POST"])
def start():
    pasos = None
    resultados = None
    nombres_vars = None
    error = None
    info = None
    matriz_input = ""
    metodo = "gauss_jordan"

    if request.method == "POST":
        matriz_input = request.form.get("txtMatrix", "")
        metodo = request.form.get("metodo", "gauss_jordan")

        try:
            if '=' in matriz_input:
                matriz, vars_detectadas = parse_ecuaciones(matriz_input)
                if len(matriz[0]) < 2:
                    error = "El sistema debe tener al menos una variable y un resultado."
                else:
                    pasos, resultados, nombres_vars, error_o_info = resolver_matriz(matriz, metodo, vars_detectadas)
            else:
                lineas = matriz_input.strip().split("\n")
                matriz = [linea.split() for linea in lineas if linea.strip()]
                
                if len(set(len(fila) for fila in matriz)) > 1:
                    error = "Todas las filas deben tener la misma cantidad de elementos."
                elif len(matriz) > 0 and len(matriz[0]) < 2:
                    error = "La matriz debe tener al menos 2 columnas."
                else:
                    pasos, resultados, nombres_vars, error_o_info = resolver_matriz(matriz, metodo)
            
            if not resultados and error_o_info:
                error = error_o_info
            elif error_o_info:
                info = error_o_info
                
        except ValueError as ve:
            error = f"Error en la entrada: {str(ve)}"
        except Exception as e:
            error = f"Error inesperado al procesar: {str(e)}"

    return render_template(
        "index.html",
        pasos=pasos,
        resultados=resultados,
        nombres_vars=nombres_vars,
        error=error,
        info=info,
        matriz_input=matriz_input,
        metodo=metodo,
    )

if __name__ == "__main__":
    app.run(debug=True)