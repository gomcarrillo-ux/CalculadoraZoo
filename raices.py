# raices.py
"""
Módulo 6: Raíces de Ecuaciones y Métodos Numéricos (Bioma Ártico / Belugas 🐳❄️)
"""
import math
import re
from flask import Blueprint, render_template, request, jsonify
from sympy import (
    Symbol, diff, lambdify,
    E as SymE, pi as SymPi, log as SymLog,
    sin, cos, tan, cot, sec, csc,
    asin, acos, atan, sinh, cosh, tanh,
    exp as SymExp, sqrt as SymSqrt, Abs as SymAbs,
)
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    convert_xor,
)

bp_raices = Blueprint('raices', __name__)

# ============================================================
# INTÉRPRETE DE ECUACIONES (tokenizador propio y seguro)
# ============================================================
_SUP = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻', '0123456789+-')
_RE_SUP = re.compile(r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+')
_RE_NUM = re.compile(r'(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?')
_RE_PAL = re.compile(r'[a-zñ]+')
_RE_PREFIJO = re.compile(r'^\s*(?:y|f\s*\(\s*x\s*\))\s*=\s*')

_ALIAS = {
    'sin':  ['sin', 'sen', 'seno'],
    'cos':  ['cos', 'coseno'],
    'tan':  ['tan', 'tg', 'tangente'],
    'cot':  ['cot', 'ctg', 'cotan', 'cotangente'],
    'csc':  ['csc', 'cosec', 'cosecante'],
    'sec':  ['sec'],
    'asin': ['asin', 'arcsin', 'arcsen'],
    'acos': ['acos', 'arccos'],
    'atan': ['atan', 'arctan', 'arctg'],
    'sinh': ['sinh', 'senh'],
    'cosh': ['cosh'],
    'tanh': ['tanh', 'tgh'],
    'ln':   ['ln', 'in'],
    'log':  ['log'],
    'exp':  ['exp'],
    'sqrt': ['sqrt', 'raiz'],
    'Abs':  ['abs'],
}
_NOMBRES = {}
for _canon, _lista in _ALIAS.items():
    for _n in _lista:
        _NOMBRES[_n] = ('func', _canon)
_NOMBRES['pi'] = ('const', 'pi')
_NOMBRES['e'] = ('const', 'E')
_NOMBRES['x'] = ('x', 'x')
_ORDEN = sorted(_NOMBRES, key=len, reverse=True)


def _preparar(texto):
    s = str(texto).strip().lower()
    s = _RE_PREFIJO.sub('', s)
    s = _RE_SUP.sub(lambda m: '^(' + m.group().translate(_SUP) + ')', s)
    for a, b in (('−', '-'), ('–', '-'), ('×', '*'), ('·', '*'), ('⋅', '*'),
                 ('÷', '/'), ('π', 'pi'), ('√', 'sqrt'), (',', '.'),
                 ('[', '('), (']', ')'), ('{', '('), ('}', ')')):
        s = s.replace(a, b)
    return s


def _descomponer(palabra):
    res, i = [], 0
    while i < len(palabra):
        for nombre in _ORDEN:
            if palabra.startswith(nombre, i):
                res.append(_NOMBRES[nombre])
                i += len(nombre)
                break
        else:
            res.append(('x', 'x'))
            i += 1
    return res


def _tokenizar(s):
    toks, i, esp = [], 0, False
    while i < len(s):
        c = s[i]
        if c.isspace():
            esp = True
            i += 1
            continue
        m = _RE_NUM.match(s, i)
        if m:
            toks.append(('num', m.group(), esp))
            i = m.end()
        elif c.isalpha():
            m = _RE_PAL.match(s, i)
            if not m:
                raise ValueError(f"Símbolo no reconocido: '{c}'")
            primero = True
            for kind, val in _descomponer(m.group()):
                toks.append((kind, val, esp if primero else False))
                primero = False
            i = m.end()
        elif s.startswith('**', i):
            toks.append(('op', '^', esp))
            i += 2
        elif c in '+-*/^':
            toks.append(('op', c, esp))
            i += 1
        elif c == '(':
            toks.append(('lp', '(', esp))
            i += 1
        elif c == ')':
            toks.append(('rp', ')', esp))
            i += 1
        else:
            raise ValueError(f"Símbolo no reconocido: '{c}'")
        esp = False
    return toks


def _convertir(toks):
    n = len(toks)
    pos = 0

    def sig():
        return toks[pos] if pos < n else None

    def paren():
        nonlocal pos
        pos += 1
        inner = secuencia()
        t = sig()
        if t is None or t[0] != 'rp':
            raise ValueError("Falta cerrar un paréntesis ')'.")
        pos += 1
        if inner == '':
            raise ValueError("Hay un paréntesis vacío ().")
        return '(' + inner + ')'

    def operando_potencia():
        nonlocal pos
        signo = ''
        t = sig()
        if t and t[0] == 'op' and t[1] in '+-':
            signo = t[1]
            pos += 1
        return '(' + signo + atomo() + ')'

    def arg_sin_paren():
        nonlocal pos
        partes, ultimo, primero = [], None, True
        t = sig()
        if t and t[0] == 'op' and t[1] in '+-':
            partes.append(t[1])
            pos += 1
        while True:
            t = sig()
            if t is None or t[0] in ('op', 'rp'):
                break
            kind, val, esp = t
            if not primero and kind == 'func' and esp:
                break
            if not primero:
                partes.append('**' if (ultimo == 'x' and kind == 'num' and not esp) else '*')
            partes.append(atomo())
            ultimo, primero = kind, False
            t = sig()
            if t and t[0] == 'op' and t[1] == '^':
                pos += 1
                partes.append('**' + operando_potencia())
                ultimo = 'pot'
        if primero:
            raise ValueError("Falta el valor dentro de una función.")
        return ''.join(partes)

    def atomo():
        nonlocal pos
        t = sig()
        if t is None:
            raise ValueError("La ecuación termina de forma inesperada.")
        kind, val, _ = t
        if kind in ('num', 'x', 'const'):
            pos += 1
            return val
        if kind == 'lp':
            return paren()
        if kind == 'func':
            pos += 1
            nxt = sig()
            arg = paren() if (nxt and nxt[0] == 'lp') else '(' + arg_sin_paren() + ')'
            if val == 'ln':
                return f'log{arg}'
            if val == 'log':
                return f'(log{arg}/log(10))'
            return f'{val}{arg}'
        raise ValueError("Hay un operador o paréntesis mal colocado.")

    def secuencia():
        nonlocal pos
        out, prev_val, ultimo = [], False, None
        while pos < n:
            kind, val, esp = toks[pos]
            if kind == 'rp':
                break
            if kind == 'op':
                out.append('**' if val == '^' else val)
                prev_val, ultimo = False, None
                pos += 1
                continue
            if prev_val:
                out.append('**' if (ultimo == 'x' and kind == 'num' and not esp) else '*')
            out.append(atomo())
            prev_val, ultimo = True, kind
        return ''.join(out)

    resultado = secuencia()
    if pos < n:
        raise ValueError("Sobra un paréntesis de cierre ')'.")
    if not resultado:
        raise ValueError("Escribe una ecuación.")
    return resultado


def normalizar_expresion(texto):
    return _convertir(_tokenizar(_preparar(texto)))


_LOCAL_SYMPY = {
    'E': SymE, 'pi': SymPi,
    'log': SymLog,
    'sin': sin, 'cos': cos, 'tan': tan,
    'cot': cot, 'sec': sec, 'csc': csc,
    'asin': asin, 'acos': acos, 'atan': atan,
    'sinh': sinh, 'cosh': cosh, 'tanh': tanh,
    'exp': SymExp, 'sqrt': SymSqrt, 'Abs': SymAbs,
}

def _a_sympy(texto):
    x = Symbol('x')
    expr = normalizar_expresion(texto)
    local = dict(_LOCAL_SYMPY)
    local['x'] = x
    try:
        return parse_expr(expr, local_dict=local,
                          transformations=standard_transformations + (convert_xor,))
    except Exception:
        raise ValueError("No pude entender la ecuación. Revisa que no falte algún signo (+, −, ×).")


def obtener_funciones(expr_str):
    x = Symbol('x')
    f_sym = _a_sympy(expr_str)
    df_sym = diff(f_sym, x)
    f_func = lambdify(x, f_sym, modules=['math', 'sympy'])
    df_func = lambdify(x, df_sym, modules=['math', 'sympy'])
    return f_func, df_func, str(f_sym), str(df_sym)


def bonito(s):
    return s.replace('**', '^').replace('*', '·').replace('log(', 'ln(')


def parse_float_flexible(val_str, default=0.0):
    try:
        return float(_a_sympy(val_str).evalf())
    except Exception:
        return default


def parse_int_flexible(val_str, default=20):
    try:
        val_int = int(parse_float_flexible(val_str, default))
        if val_int < 1:
            return default
        return min(val_int, 1000)
    except Exception:
        return default


def rango_por_defecto(a, b, metodo):
    if metodo == 'newton':
        return a - 3.0, a + 3.0
    lo, hi = min(a, b), max(a, b)
    if hi - lo < 1e-9:
        return lo - 3.0, hi + 3.0
    margen = max((hi - lo) * 0.5, 1.0)
    return lo - margen, hi + margen


def generar_puntos(f, lo, hi, n=200):
    pts = []
    for k in range(n + 1):
        xg = lo + k * (hi - lo) / n
        try:
            yg = float(f(xg))
            if math.isfinite(yg) and abs(yg) < 1e4:
                pts.append({'x': round(xg, 5), 'y': round(yg, 5)})
            else:
                pts.append({'x': round(xg, 5), 'y': None})
        except Exception:
            pts.append({'x': round(xg, 5), 'y': None})
    return pts


# ============================================================
# MÉTODOS NUMÉRICOS (Implementados)
# ============================================================

def metodo_biseccion(f, a, b, tol, max_iter):
    tabla, pasos = [], []
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("El intervalo [a, b] no contiene un cambio de signo. Bisección requiere f(a)*f(b) < 0.")
    
    c_prev, raiz = None, None
    for it in range(1, max_iter + 1):
        c = (a + b) / 2
        fc = f(c)
        error_abs = abs(c - c_prev) if c_prev is not None else 0.0
        error_rel = (error_abs / abs(c)) * 100 if c_prev is not None and c != 0 else 0.0
        
        tabla.append({
            'it': it, 'a': a, 'b': b, 'c': c,
            'fa': fa, 'fb': fb, 'fc': fc,
            'error_abs': error_abs, 'error_rel': error_rel
        })
        
        pasos.append(f"<div class='alert alert-info'>Iteración {it}: a={a:.6f}, b={b:.6f}, c={c:.6f}, f(c)={fc:.6f}</div>")
        
        if abs(fc) < 1e-12 or (c_prev is not None and error_abs < tol):
            raiz = c
            break
            
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
        c_prev = c
        
    return tabla, pasos, raiz if raiz is not None else c


def metodo_regla_falsa(f, a, b, tol, max_iter):
    tabla, pasos = [], []
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("El intervalo [a, b] no contiene un cambio de signo. Regla Falsa requiere f(a)*f(b) < 0.")
    
    c_prev, raiz = None, None
    for it in range(1, max_iter + 1):
        c = b - (fb * (b - a)) / (fb - fa)
        fc = f(c)
        error_abs = abs(c - c_prev) if c_prev is not None else 0.0
        error_rel = (error_abs / abs(c)) * 100 if c_prev is not None and c != 0 else 0.0
        
        tabla.append({
            'it': it, 'a': a, 'b': b, 'c': c,
            'fa': fa, 'fb': fb, 'fc': fc,
            'error_abs': error_abs, 'error_rel': error_rel
        })
        
        pasos.append(f"<div class='alert alert-info'>Iteración {it}: a={a:.6f}, b={b:.6f}, c={c:.6f}, f(c)={fc:.6f}</div>")
        
        if abs(fc) < 1e-12 or (c_prev is not None and error_abs < tol):
            raiz = c
            break
            
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
        c_prev = c
        
    return tabla, pasos, raiz if raiz is not None else c


def metodo_newton_raphson(f, df, x0, tol, max_iter):
    tabla, pasos = [], []
    x_prev, raiz = None, None
    
    for it in range(1, max_iter + 1):
        fx = f(x0)
        dfx = df(x0)
        if abs(dfx) < 1e-15:
            raise ValueError("La derivada es cero. Newton-Raphson no puede continuar.")
            
        x = x0 - fx / dfx
        error_abs = abs(x - x_prev) if x_prev is not None else 0.0
        error_rel = (error_abs / abs(x)) * 100 if x_prev is not None and x != 0 else 0.0
        
        tabla.append({
            'it': it, 'a': x0, 'b': x0, 'c': x,
            'fa': fx, 'fb': fx, 'fc': f(x),
            'error_abs': error_abs, 'error_rel': error_rel
        })
        
        pasos.append(f"<div class='alert alert-info'>Iteración {it}: x0={x0:.6f}, f(x0)={fx:.6f}, x1={x:.6f}, f(x1)={f(x):.6f}</div>")
        
        if abs(f(x)) < 1e-12 or (x_prev is not None and error_abs < tol):
            raiz = x
            break
            
        x_prev, x0 = x0, x
        
    return tabla, pasos, raiz if raiz is not None else x


def metodo_secante(f, x0, x1, tol, max_iter):
    tabla, pasos = [], []
    raiz = None
    
    for it in range(1, max_iter + 1):
        f0, f1 = f(x0), f(x1)
        if abs(f1 - f0) < 1e-15:
            raise ValueError("División por cero en el método de la secante (f(x1) - f(x0) = 0).")
            
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        error_abs = abs(x2 - x1)
        error_rel = (error_abs / abs(x2)) * 100 if x2 != 0 else 0.0
        
        tabla.append({
            'it': it, 'a': x0, 'b': x1, 'c': x2,
            'fa': f0, 'fb': f1, 'fc': f(x2),
            'error_abs': error_abs, 'error_rel': error_rel
        })
        
        pasos.append(f"<div class='alert alert-info'>Iteración {it}: x0={x0:.6f}, x1={x1:.6f}, x2={x2:.6f}, f(x2)={f(x2):.6f}</div>")
        
        if abs(f(x2)) < 1e-12 or error_abs < tol:
            raiz = x2
            break
            
        x0, x1 = x1, x2
        
    return tabla, pasos, raiz if raiz is not None else x2


# ============================================================
# RUTAS FLASK
# ============================================================
@bp_raices.route('/raices/graficar', methods=['POST'])
def raices_graficar():
    datos = request.get_json(silent=True) or {}
    try:
        f, _, f_str, _ = obtener_funciones(datos.get('ecuacion', ''))
        xmin = parse_float_flexible(datos.get('xmin'), -5.0)
        xmax = parse_float_flexible(datos.get('xmax'), 5.0)
        if xmin >= xmax:
            raise ValueError("En 'Ver desde / hasta', el primer número debe ser menor que el segundo.")
        return jsonify(ok=True, puntos=generar_puntos(f, xmin, xmax), interpretacion=bonito(f_str))
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@bp_raices.route('/raices', methods=['GET', 'POST'])
def raices():
    def_ecuacion = "x⁴ - 5x³ + 0.5x² - 11x + 10"
    def_metodo = "biseccion"
    def_a = "0.6"
    def_b = "1.0"
    def_tol = "0.0001"
    def_max_iter = "20"

    if request.method == 'GET':
        puntos_iniciales = []
        try:
            f, _, _, _ = obtener_funciones(def_ecuacion)
            lo, hi = rango_por_defecto(float(def_a), float(def_b), def_metodo)
            puntos_iniciales = generar_puntos(f, lo, hi)
        except Exception:
            pass
        return render_template(
            'raices.html', ecuacion=def_ecuacion, metodo=def_metodo,
            a=def_a, b=def_b, tol=def_tol, max_iter=def_max_iter,
            tabla=[], pasos=[], raiz_hallada=None, error=None,
            puntos_grafica=puntos_iniciales, derivada_tex="", interpretacion="",
        )

    ecuacion_input = request.form.get('ecuacion', def_ecuacion)
    metodo = request.form.get('metodo', def_metodo)
    a_str = request.form.get('a', def_a)
    b_str = request.form.get('b', def_b)
    tol_str = request.form.get('tol', def_tol)
    max_iter_str = request.form.get('max_iter', def_max_iter)

    tabla, pasos, puntos_grafica = [], [], []
    raiz_hallada, error = None, None
    derivada_tex, interpretacion = "", ""

    try:
        a_val = parse_float_flexible(a_str, 0.0)
        b_val = parse_float_flexible(b_str, a_val + 1.0)
        tol_val = parse_float_flexible(tol_str, 0.0001)
        max_iter = parse_int_flexible(max_iter_str, 20)

        f, df, f_str, df_str = obtener_funciones(ecuacion_input)
        interpretacion = bonito(f_str)
        derivada_tex = bonito(df_str)

        lo, hi = rango_por_defecto(a_val, b_val, metodo)
        puntos_grafica = generar_puntos(f, lo, hi)

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

    except Exception as e:
        error = f"Ocurrió un error: {str(e)}"

    return render_template(
        'raices.html', ecuacion=ecuacion_input, metodo=metodo, a=a_str, b=b_str,
        tol=tol_str, max_iter=max_iter_str, tabla=tabla, pasos=pasos,
        raiz_hallada=raiz_hallada, error=error, puntos_grafica=puntos_grafica,
        derivada_tex=derivada_tex, interpretacion=interpretacion,
    )