# raices.py
"""
Módulo 6: Raíces de Ecuaciones y Métodos Numéricos (Bioma Ártico / Belugas 🐳❄️)
Soporta:
  1. Bisección (Método Cerrado)
  2. Regla Falsa / Falsa Posición (Método Cerrado)
  3. Newton-Raphson (Método Abierto)
  4. Secante (Método Abierto)

Todos los métodos están codificados paso a paso desde cero sin librerías de resolución automática.
"""
import math
import re
from flask import Blueprint, render_template, request
from sympy import Symbol, diff, lambdify, sympify
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)

bp_raices = Blueprint('raices', __name__)

# ============================================================
# PARSERS NUMÉRICOS FLEXIBLES (NOTACIÓN CIENTÍFICA Y POTENCIAS)
# ============================================================

def parse_float_flexible(val_str, default=0.0):
    """Parsea números flotantes aceptando decimales, notación científica (1e-6) o potencias (10^-6)."""
    try:
        s = str(val_str).strip().replace(',', '.')
        if '^' in s:
            s = s.replace('^', '**')
            return float(sympify(s))
        return float(s)
    except Exception:
        return default

def parse_int_flexible(val_str, default=20):
    """Parsea enteros aceptando notación científica (ej: 1e2 -> 100, 1e-6 -> fallback seguro a default)."""
    try:
        val_float = parse_float_flexible(val_str, default)
        val_int = int(val_float)
        if val_int < 1:
            return default
        return min(val_int, 1000)  # Límite máximo de seguridad para no saturar el servidor
    except Exception:
        return default

# ============================================================
# EVALUADOR MATEMÁTICO ULTRA-FLEXIBLE Y ROBUSTO
# ============================================================

def normalizar_expresion(expr_str):
    """
    Convierte sintaxis flexible de usuario (soportando 'In', 'ln', 'log', 'sen', 'cos', 'tan', 'tg',
    expresiones sin paréntesis como 'cosx' o 'senx', potencias y multiplicación implícita)
    en sintaxis matemática estándar de SymPy.
    """
    s = expr_str.strip().replace(',', '.')
    s = s.replace('^', '**')
    
    # 1. Normalizar funciones en español y variantes de logaritmo
    s = re.sub(r'\b(seno|sen)\b', 'sin', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(coseno)\b', 'cos', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(tangente|tg)\b', 'tan', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(cotangente|ctg|cotan)\b', 'cot', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(cosecante|cosec)\b', 'csc', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(ln|in|log)\b', 'log', s, flags=re.IGNORECASE)
    
    # 2. Envolver argumentos pegados sin paréntesis (ej: cosx -> cos(x), sen2x -> sin(2x), logx -> log(x))
    patron_funcs = r'(asin|acos|atan|sinh|cosh|tanh|sin|cos|tan|cot|sec|csc|log|exp|sqrt|abs)'
    s = re.sub(patron_funcs + r'\s*([a-zA-Z0-9_]+)(?!\()', r'\1(\2)', s, flags=re.IGNORECASE)
    
    # 3. Proteger funciones usando marcadores numéricos para que el reemplazo de variables no las corrompa
    mapa_funciones = [
        ('asin', '__1__'),  ('acos', '__2__'),  ('atan', '__3__'),
        ('sinh', '__4__'),  ('cosh', '__5__'),  ('tanh', '__6__'),
        ('sin', '__7__'),   ('cos', '__8__'),   ('tan', '__9__'),
        ('cot', '__10__'),  ('sec', '__11__'),  ('csc', '__12__'),
        ('log', '__13__'),  ('exp', '__14__'),  ('sqrt', '__15__'),
        ('abs', '__16__')
    ]
    for orig, mark in mapa_funciones:
        s = re.sub(r'\b' + orig + r'\b', mark, s, flags=re.IGNORECASE)
        
    # 4. Reemplazar cualquier otra letra utilizada como variable (y, z, t, etc.) por 'x'
    s = re.sub(r'[a-wyzA-WYZ]', 'x', s)
    s = s.replace('X', 'x')
    
    # 5. Restaurar los nombres de las funciones protegidas
    for orig, mark in mapa_funciones:
        s = s.replace(mark, orig)
        
    # 6. Convertir notación de exponentes como x2 -> x**2
    s = re.sub(r'x(?!\*)(?=\d)', 'x**', s)
    
    # 7. Insertar multiplicaciones implícitas (ej: 5x -> 5*x, xcos(x) -> x*cos(x), (x+1)x -> (x+1)*x)
    s = re.sub(r'(\d)\s*([a-zA-Z\(])', r'\1*\2', s)
    s = re.sub(r'(\))\s*([a-zA-Z0-9\(])', r'\1*\2', s)
    s = re.sub(r'\bx\s*(\(|[a-zA-Z]+)', r'x*\1', s)
    
    return s

def obtener_funciones(expr_str):
    """Parsea la función del usuario soportando cualquier variante de exponente, trigonométrica y multiplicación."""
    x = Symbol('x')
    expr_clean = normalizar_expresion(expr_str)
    
    transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
    
    f_sym = parse_expr(expr_clean, transformations=transformations)
    df_sym = diff(f_sym, x)
    
    f_func = lambdify(x, f_sym, modules=['math', 'numpy'])
    df_func = lambdify(x, df_sym, modules=['math', 'numpy'])
    
    return f_func, df_func, str(f_sym), str(df_sym)


# ============================================================
# ALGORITMOS NUMÉRICOS MANUALES CON TABLAS EN PASO A PASO
# ============================================================

def metodo_biseccion(f, a, b, tol, max_iter):
    fa, fb = float(f(a)), float(f(b))
    if fa * fb > 0:
        raise ValueError(f"No hay cambio de signo en el intervalo [{a}, {b}]. f(a)={fa:.4f}, f(b)={fb:.4f}.")
    
    tabla = []
    pasos_explicados = []
    c_prev = None
    
    for it in range(1, max_iter + 1):
        c = float((a + b) / 2.0)
        fc = float(f(c))
        fa = float(f(a))
        fb = float(f(b))
        
        error_abs = float(abs(c - c_prev)) if c_prev is not None else float(abs(b - a))
        error_rel = float((abs(c - c_prev) / abs(c) * 100)) if (c_prev is not None and c != 0) else 100.0
        
        tabla.append({
            'it': it,
            'a': a,
            'b': b,
            'c': c,
            'fa': fa,
            'fb': fb,
            'fc': fc,
            'error_abs': error_abs,
            'error_rel': error_rel
        })
        
        if fa * fc < 0:
            explicacion_cambio = f"Como f(a)·f(c) < 0, la raíz está en [{a:.6f}, {c:.6f}]. El nuevo extremo superior b pasa a ser c = {c:.6f}."
            b_next = c
            a_next = a
        else:
            explicacion_cambio = f"Como f(a)·f(c) > 0, la raíz está en [{c:.6f}, {b:.6f}]. El nuevo extremo inferior a pasa a ser c = {c:.6f}."
            a_next = c
            b_next = b
            
        paso_html = f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark'>📌 Iteración {it}</span>
                <span class='badge bg-info text-dark fs-6'>Punto medio c = {c:.6f}</span>
            </div>
            <div class='card-body p-2'>
                <div class='table-responsive'>
                    <table class='table table-sm table-bordered text-center align-middle mb-2' style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>a</th>
                                <th>b</th>
                                <th>c (Punto medio)</th>
                                <th>f(a)</th>
                                <th>f(b)</th>
                                <th>f(c)</th>
                                <th>Error Absoluto (Ea)</th>
                                <th>Error Relativo (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{a:.6f}</td>
                                <td>{b:.6f}</td>
                                <td class='fw-bold text-primary'>{c:.6f}</td>
                                <td>{fa:.6f}</td>
                                <td>{fb:.6f}</td>
                                <td class='fw-bold'>{fc:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{error_rel:.4f}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-secondary p-2 mb-0 small'>
                    💡 <b>Evaluación del Subintervalo:</b> {explicacion_cambio}
                </div>
            </div>
        </div>
        """
        pasos_explicados.append(paso_html)
        
        if error_abs < tol or abs(fc) < 1e-12:
            break
            
        a = a_next
        b = b_next
        c_prev = c
        
    return tabla, pasos_explicados, c


def metodo_regla_falsa(f, a, b, tol, max_iter):
    fa, fb = float(f(a)), float(f(b))
    if fa * fb > 0:
        raise ValueError(f"No hay cambio de signo en el intervalo [{a}, {b}]. f(a)={fa:.4f}, f(b)={fb:.4f}.")
    
    tabla = []
    pasos_explicados = []
    c_prev = None
    
    for it in range(1, max_iter + 1):
        fa = float(f(a))
        fb = float(f(b))
        c = float((a * fb - b * fa) / (fb - fa))
        fc = float(f(c))
        
        error_abs = float(abs(c - c_prev)) if c_prev is not None else float(abs(b - a))
        error_rel = float((abs(c - c_prev) / abs(c) * 100)) if (c_prev is not None and c != 0) else 100.0
        
        tabla.append({
            'it': it,
            'a': a,
            'b': b,
            'c': c,
            'fa': fa,
            'fb': fb,
            'fc': fc,
            'error_abs': error_abs,
            'error_rel': error_rel
        })
        
        if fa * fc < 0:
            explicacion_cambio = f"Como f(a)·f(c) < 0, la raíz se ubica entre a y c. El extremo b se actualiza a c = {c:.6f}."
            b_next = c
            a_next = a
        else:
            explicacion_cambio = f"Como f(a)·f(c) > 0, la raíz se ubica entre c y b. El extremo a se actualiza a c = {c:.6f}."
            a_next = c
            b_next = b
            
        paso_html = f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark'>📌 Iteración {it}</span>
                <span class='badge bg-info text-dark fs-6'>Intersección c = {c:.6f}</span>
            </div>
            <div class='card-body p-2'>
                <div class='table-responsive'>
                    <table class='table table-sm table-bordered text-center align-middle mb-2' style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>a</th>
                                <th>b</th>
                                <th>c (Falsa Posición)</th>
                                <th>f(a)</th>
                                <th>f(b)</th>
                                <th>f(c)</th>
                                <th>Error Absoluto (Ea)</th>
                                <th>Error Relativo (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{a:.6f}</td>
                                <td>{b:.6f}</td>
                                <td class='fw-bold text-primary'>{c:.6f}</td>
                                <td>{fa:.6f}</td>
                                <td>{fb:.6f}</td>
                                <td class='fw-bold'>{fc:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{error_rel:.4f}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-secondary p-2 mb-0 small'>
                    💡 <b>Fórmula Regla Falsa:</b> c = [{a:.6f}·f({b:.6f}) - {b:.6f}·f({a:.6f})] / [f({b:.6f}) - f({a:.6f})] = <b>{c:.6f}</b>.<br>
                    📌 <b>Actualización:</b> {explicacion_cambio}
                </div>
            </div>
        </div>
        """
        pasos_explicados.append(paso_html)
        
        if error_abs < tol or abs(fc) < 1e-12:
            break
            
        a = a_next
        b = b_next
        c_prev = c
        
    return tabla, pasos_explicados, c


def metodo_newton_raphson(f, df, x0, tol, max_iter):
    tabla = []
    pasos_explicados = []
    x_curr = x0
    
    for it in range(1, max_iter + 1):
        fx = float(f(x_curr))
        dfx = float(df(x_curr))
        
        if abs(dfx) < 1e-12:
            raise ValueError(f"La derivada es casi cero (f'({x_curr:.4f}) = {dfx:.4e}). El método de Newton no puede continuar.")
            
        x_next = float(x_curr - (fx / dfx))
        fn = float(f(x_next))
        
        error_abs = float(abs(x_next - x_curr))
        error_rel = float((error_abs / abs(x_next) * 100)) if x_next != 0 else 100.0
        
        tabla.append({
            'it': it,
            'a': x_curr,
            'b': dfx,
            'c': x_next,
            'fa': fx,
            'fb': dfx,
            'fc': fn,
            'error_abs': error_abs,
            'error_rel': error_rel
        })
        
        paso_html = f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark'>📌 Iteración {it}</span>
                <span class='badge bg-primary fs-6'>x_{it} = {x_next:.6f}</span>
            </div>
            <div class='card-body p-2'>
                <div class='table-responsive'>
                    <table class='table table-sm table-bordered text-center align-middle mb-2' style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>x_k (Actual)</th>
                                <th>f(x_k)</th>
                                <th>f'(x_k) (Derivada)</th>
                                <th>x_{it} (Nueva Aprox)</th>
                                <th>f(x_{it})</th>
                                <th>Error Absoluto (Ea)</th>
                                <th>Error Relativo (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{x_curr:.6f}</td>
                                <td>{fx:.6f}</td>
                                <td>{dfx:.6f}</td>
                                <td class='fw-bold text-primary'>{x_next:.6f}</td>
                                <td>{fn:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{error_rel:.4f}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-secondary p-2 mb-0 small'>
                    💡 <b>Fórmula Tangente:</b> x_{it} = {x_curr:.6f} - ({fx:.6f} / {dfx:.6f}) = <b>{x_next:.6f}</b>.
                </div>
            </div>
        </div>
        """
        pasos_explicados.append(paso_html)
        
        if error_abs < tol or abs(fn) < 1e-12:
            break
            
        x_curr = x_next
        
    return tabla, pasos_explicados, x_next


def metodo_secante(f, x0, x1, tol, max_iter):
    tabla = []
    pasos_explicados = []
    
    for it in range(1, max_iter + 1):
        fx0 = float(f(x0))
        fx1 = float(f(x1))
        
        if abs(fx1 - fx0) < 1e-12:
            raise ValueError(f"División por cero en la secante: f(x1) - f(x0) ≈ 0 en la iteración {it}.")
            
        x2 = float(x1 - (fx1 * (x1 - x0)) / (fx1 - fx0))
        fx2 = float(f(x2))
        
        error_abs = float(abs(x2 - x1))
        error_rel = float((error_abs / abs(x2) * 100)) if x2 != 0 else 100.0
        
        tabla.append({
            'it': it,
            'a': x0,
            'b': x1,
            'c': x2,
            'fa': fx0,
            'fb': fx1,
            'fc': fx2,
            'error_abs': error_abs,
            'error_rel': error_rel
        })
        
        paso_html = f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark'>📌 Iteración {it}</span>
                <span class='badge bg-primary fs-6'>x_{it+1} = {x2:.6f}</span>
            </div>
            <div class='card-body p-2'>
                <div class='table-responsive'>
                    <table class='table table-sm table-bordered text-center align-middle mb-2' style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>x_{it-1}</th>
                                <th>x_{it}</th>
                                <th>f(x_{it-1})</th>
                                <th>f(x_{it})</th>
                                <th>x_{it+1} (Nueva aprox)</th>
                                <th>f(x_{it+1})</th>
                                <th>Error Absoluto (Ea)</th>
                                <th>Error Relativo (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{x0:.6f}</td>
                                <td>{x1:.6f}</td>
                                <td>{fx0:.6f}</td>
                                <td>{fx1:.6f}</td>
                                <td class='fw-bold text-primary'>{x2:.6f}</td>
                                <td>{fx2:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{error_rel:.4f}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-secondary p-2 mb-0 small'>
                    💡 <b>Fórmula Secante:</b> Secante trazada entre x_{it-1}={x0:.6f} y x_{it}={x1:.6f} ➔ <b>x_{it+1} = {x2:.6f}</b>.
                </div>
            </div>
        </div>
        """
        pasos_explicados.append(paso_html)
        
        if error_abs < tol or abs(fx2) < 1e-12:
            break
            
        x0 = x1
        x1 = x2
        
    return tabla, pasos_explicados, x2


# ============================================================
# RUTA FLASK PRINCIPAL
# ============================================================

@bp_raices.route('/raices', methods=['GET', 'POST'])
def raices():
    def_ecuacion = "x4 - 5x3 + 0.5x2 - 11x + 10"
    def_metodo = "biseccion"
    def_a = "0.6"
    def_b = "1.0"
    def_tol = "0.0001"
    def_max_iter = "20"

    if request.method == 'GET':
        return render_template(
            'raices.html',
            ecuacion=def_ecuacion,
            metodo=def_metodo,
            a=def_a,
            b=def_b,
            tol=def_tol,
            max_iter=def_max_iter,
            tabla=[],
            pasos=[],
            raiz_hallada=None,
            error=None,
            puntos_grafica=[],
            derivada_tex=""
        )

    ecuacion_input = request.form.get('ecuacion', def_ecuacion)
    metodo = request.form.get('metodo', def_metodo)
    a_str = request.form.get('a', def_a)
    b_str = request.form.get('b', def_b)
    tol_str = request.form.get('tol', def_tol)
    max_iter_str = request.form.get('max_iter', def_max_iter)

    tabla = []
    pasos = []
    raiz_hallada = None
    error = None
    puntos_grafica = []
    derivada_tex = ""

    try:
        # Conversión numérica flexible con soporte para notación científica (ej: 1e-6)
        a_val = parse_float_flexible(a_str, 0.0)
        b_val = parse_float_flexible(b_str, a_val + 1.0)
        tol_val = parse_float_flexible(tol_str, 0.0001)
        max_iter = parse_int_flexible(max_iter_str, 20)
        
        f, df, f_tex, df_tex = obtener_funciones(ecuacion_input)
        derivada_tex = df_tex
        
        if metodo == 'biseccion':
            tabla, pasos, raiz_hallada = metodo_biseccion(f, a_val, b_val, tol_val, max_iter)
        elif metodo == 'regla_falsa':
            tabla, pasos, raiz_hallada = metodo_regla_falsa(f, a_val, b_val, tol_val, max_iter)
        elif metodo == 'newton':
            tabla, pasos, raiz_hallada = metodo_newton_raphson(f, df, a_val, tol_val, max_iter)
        elif metodo == 'secante':
            tabla, pasos, raiz_hallada = metodo_secante(f, a_val, b_val, tol_val, max_iter)

        if raiz_hallada is not None:
            raiz_hallada = float(raiz_hallada)

        # Generación de 101 puntos de la curva f(x) para la gráfica
        x_start = min(a_val, b_val) - 1.5
        x_end = max(a_val, b_val) + 1.5
        paso_g = (x_end - x_start) / 100.0
        
        for k in range(101):
            x_g = x_start + k * paso_g
            try:
                y_g = float(f(x_g))
                if abs(y_g) < 200:
                    puntos_grafica.append({'x': round(x_g, 4), 'y': round(y_g, 4)})
            except:
                pass

    except Exception as e:
        error = f"Ocurrió un error en el cálculo: {str(e)}"

    return render_template(
        'raices.html',
        ecuacion=ecuacion_input,
        metodo=metodo,
        a=a_str,
        b=b_str,
        tol=tol_str,
        max_iter=max_iter_str,
        tabla=tabla,
        pasos=pasos,
        raiz_hallada=raiz_hallada,
        error=error,
        puntos_grafica=puntos_grafica,
        derivada_tex=derivada_tex
    )