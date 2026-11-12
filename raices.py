# raices.py
"""
Módulo 6: Raíces de Ecuaciones y Métodos Numéricos (Bioma Ártico / Belugas 🐳❄️)
Versión corregida tras auditoría técnica + robustez en métodos abiertos.
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
_SUP = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ˣ', '0123456789+-x')
_RE_SUP = re.compile(r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ˣ]+')
_RE_NUM = re.compile(r'(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?')
_RE_PAL = re.compile(r'[a-zñ]+')
_RE_PREFIJO = re.compile(r'^\s*(?:y|f\s*\(\s*x\s*\))\s*=\s*')
_RE_SUFIJO = re.compile(r'\s*=\s*0(?:\.0+)?\s*$')

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
    s = _RE_SUFIJO.sub('', s)
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
            ch = palabra[i]
            raise ValueError(
                f"El símbolo '{ch}' no está permitido en la ecuación. "
                f"Usa solo 'x', números, operadores (+, -, *, /, ^) y "
                f"funciones como sen, cos, tan, ln, log, e, π."
            )
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
        elif c == '=':
            raise ValueError(
                "No incluyas el signo '=' en la ecuación. "
                "Solo escribe el lado izquierdo de f(x) = 0."
            )
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
        raise ValueError(
            "No pude entender la ecuación. Revisa que no falte algún signo (+, −, ×)."
        )


def obtener_funciones(expr_str):
    x = Symbol('x')
    f_sym = _a_sympy(expr_str)
    df_sym = diff(f_sym, x)
    f_func = lambdify(x, f_sym, modules=['math', 'sympy'])
    df_func = lambdify(x, df_sym, modules=['math', 'sympy'])
    return f_func, df_func, str(f_sym), str(df_sym)


def bonito(s):
    return str(s).replace('**', '^').replace('*', '·').replace('E', 'e')


def parse_float_flexible(val_str, default=0.0):
    if val_str is None:
        return default
    s = str(val_str).strip()
    if not s:
        return default
    try:
        v = float(s.replace(',', '.'))
        return v if math.isfinite(v) else default
    except (ValueError, TypeError):
        pass
    try:
        v = float(_a_sympy(s).evalf())
        return v if math.isfinite(v) else default
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
# MÉTODOS NUMÉRICOS
# ============================================================

def metodo_biseccion(f, a, b, tol, max_iter):
    tabla, pasos = [], []
    fa, fb = float(f(a)), float(f(b))
    if fa * fb > 0:
        raise ValueError(
            f"No hay cambio de signo en el intervalo [{a}, {b}]. "
            f"f(a) = {fa:.6f}, f(b) = {fb:.6f}. Bisección requiere f(a)·f(b) < 0."
        )

    c_prev, raiz, c = None, None, a
    for it in range(1, max_iter + 1):
        c = (a + b) / 2.0
        fc = float(f(c))
        fa = float(f(a))
        fb = float(f(b))

        error_abs = abs(c - c_prev) if c_prev is not None else abs(b - a)
        if c_prev is not None and c != 0:
            error_rel = (error_abs / abs(c)) * 100.0
        else:
            error_rel = None
        er_display = f"{error_rel:.4f}%" if error_rel is not None else "—"

        tabla.append({
            'it': it, 'a': a, 'b': b, 'c': c,
            'fa': fa, 'fb': fb, 'fc': fc,
            'error_abs': error_abs, 'error_rel': error_rel
        })

        prod = fa * fc
        if prod < 0:
            explicacion_cambio = (
                f"<b>Evaluación de Signo:</b> f(a)·f(c) = ({fa:.6f})·({fc:.6f}) = "
                f"<b>{prod:.6f} &lt; 0</b>.<br>👉 El producto es <b>negativo</b>, la raíz "
                f"está en <b>[{a:.6f}, {c:.6f}]</b>. <b>b pasa a valer c = {c:.6f}</b>."
            )
            b_next, a_next = c, a
        else:
            explicacion_cambio = (
                f"<b>Evaluación de Signo:</b> f(a)·f(c) = ({fa:.6f})·({fc:.6f}) = "
                f"<b>{prod:.6f} &gt; 0</b>.<br>👉 El producto es <b>positivo</b>, la raíz "
                f"está en <b>[{c:.6f}, {b:.6f}]</b>. <b>a pasa a valer c = {c:.6f}</b>."
            )
            a_next, b_next = c, b

        if c_prev is not None:
            ea_formula = f"|{c:.6f} - {c_prev:.6f}|"
        else:
            ea_formula = f"|{b:.6f} - {a:.6f}| <i>(cota inicial: ancho del intervalo)</i>"

        explicacion_error = (
            f"<b>Cálculo de Error:</b> Ea = {ea_formula} = <b>{error_abs:.6f}</b> "
            f"(Error Relativo Er = <b>{er_display}</b>). "
        )
        if error_abs < tol or abs(fc) < 1e-12:
            explicacion_error += (
                f"<span class='text-success fw-bold'>¡Criterio de parada alcanzado! "
                f"(Ea &lt; Tol={tol}).</span>"
            )
        else:
            explicacion_error += (
                f"<span class='text-muted'>Aún no se alcanza la tolerancia ({tol}), "
                f"se continúa a la siguiente iteración.</span>"
            )

        pasos.append(f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark fs-6'>📌 Iteración {it} (Método de Bisección)</span>
                <span class='badge bg-info text-dark fs-6'>Punto Medio c = {c:.6f}</span>
            </div>
            <div class='card-body p-3'>
                <p class='mb-2 small text-dark'>
                    <b>Fórmula del Punto Medio:</b> c = (a + b) / 2 = ({a:.6f} + {b:.6f}) / 2 = <b>{c:.6f}</b>
                </p>
                <div class='table-responsive mb-2'>
                    <table class='table table-sm table-bordered text-center align-middle mb-0'
                           style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>Extremo a</th><th>Extremo b</th><th>Aprox c</th>
                                <th>f(a)</th><th>f(b)</th><th>f(c)</th>
                                <th>Error Abs (Ea)</th><th>Error Rel (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{a:.6f}</td><td>{b:.6f}</td>
                                <td class='fw-bold text-primary'>{c:.6f}</td>
                                <td>{fa:.6f}</td><td>{fb:.6f}</td>
                                <td class='fw-bold'>{fc:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{er_display}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-light border p-2 mb-2 small'>{explicacion_cambio}</div>
                <div class='alert alert-secondary p-2 mb-0 small'>💡 {explicacion_error}</div>
            </div>
        </div>
        """)

        if abs(fc) < 1e-12 or error_abs < tol:
            raiz = c
            break

        a, b = a_next, b_next
        c_prev = c

    return tabla, pasos, raiz if raiz is not None else c


def metodo_regla_falsa(f, a, b, tol, max_iter):
    tabla, pasos = [], []
    fa, fb = float(f(a)), float(f(b))
    if fa * fb > 0:
        raise ValueError(
            f"No hay cambio de signo en el intervalo [{a}, {b}]. "
            f"f(a) = {fa:.6f}, f(b) = {fb:.6f}. Regla Falsa requiere f(a)·f(b) < 0."
        )

    c_prev, raiz, c = None, None, a
    for it in range(1, max_iter + 1):
        fa = float(f(a))
        fb = float(f(b))
        den = fb - fa
        if abs(den) < 1e-15:
            raise ValueError(
                f"Regla Falsa inestable: f(b) - f(a) ≈ 0 en iteración {it}. "
                f"Prueba Bisección o cambia el intervalo."
            )
        c = float(b - (fb * (b - a)) / den)
        fc = float(f(c))

        error_abs = abs(c - c_prev) if c_prev is not None else abs(b - a)
        if c_prev is not None and c != 0:
            error_rel = (error_abs / abs(c)) * 100.0
        else:
            error_rel = None
        er_display = f"{error_rel:.4f}%" if error_rel is not None else "—"

        tabla.append({
            'it': it, 'a': a, 'b': b, 'c': c,
            'fa': fa, 'fb': fb, 'fc': fc,
            'error_abs': error_abs, 'error_rel': error_rel
        })

        prod = fa * fc
        if prod < 0:
            explicacion_cambio = (
                f"<b>Evaluación de Signo:</b> f(a)·f(c) = ({fa:.6f})·({fc:.6f}) = "
                f"<b>{prod:.6f} &lt; 0</b>.<br>👉 La raíz está en <b>[{a:.6f}, {c:.6f}]</b>. "
                f"Se actualiza <b>b = c = {c:.6f}</b>."
            )
            b_next, a_next = c, a
        else:
            explicacion_cambio = (
                f"<b>Evaluación de Signo:</b> f(a)·f(c) = ({fa:.6f})·({fc:.6f}) = "
                f"<b>{prod:.6f} &gt; 0</b>.<br>👉 La raíz está en <b>[{c:.6f}, {b:.6f}]</b>. "
                f"Se actualiza <b>a = c = {c:.6f}</b>."
            )
            a_next, b_next = c, b

        if c_prev is not None:
            ea_formula = f"|{c:.6f} - {c_prev:.6f}|"
        else:
            ea_formula = f"|{b:.6f} - {a:.6f}| <i>(cota inicial: ancho del intervalo)</i>"

        explicacion_error = (
            f"<b>Cálculo de Error:</b> Ea = {ea_formula} = <b>{error_abs:.6f}</b> "
            f"(Error Relativo Er = <b>{er_display}</b>). "
        )
        if error_abs < tol or abs(fc) < 1e-12:
            explicacion_error += (
                f"<span class='text-success fw-bold'>¡Convergencia lograda! "
                f"(Ea &lt; Tol={tol}).</span>"
            )
        else:
            explicacion_error += (
                f"<span class='text-muted'>Criterio no alcanzado, se continúa "
                f"con el intervalo ajustado.</span>"
            )

        pasos.append(f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark fs-6'>📌 Iteración {it} (Regla Falsa / Falsa Posición)</span>
                <span class='badge bg-info text-dark fs-6'>Intersección c = {c:.6f}</span>
            </div>
            <div class='card-body p-3'>
                <p class='mb-2 small text-dark'>
                    <b>Fórmula:</b> c = b - [f(b)·(b - a) / (f(b) - f(a))] = <b>{c:.6f}</b>
                </p>
                <div class='table-responsive mb-2'>
                    <table class='table table-sm table-bordered text-center align-middle mb-0'
                           style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>Extremo a</th><th>Extremo b</th><th>Intersección c</th>
                                <th>f(a)</th><th>f(b)</th><th>f(c)</th>
                                <th>Error Abs (Ea)</th><th>Error Rel (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{a:.6f}</td><td>{b:.6f}</td>
                                <td class='fw-bold text-primary'>{c:.6f}</td>
                                <td>{fa:.6f}</td><td>{fb:.6f}</td>
                                <td class='fw-bold'>{fc:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{er_display}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-light border p-2 mb-2 small'>{explicacion_cambio}</div>
                <div class='alert alert-secondary p-2 mb-0 small'>💡 {explicacion_error}</div>
            </div>
        </div>
        """)

        if abs(fc) < 1e-12 or error_abs < tol:
            raiz = c
            break

        a, b = a_next, b_next
        c_prev = c

    return tabla, pasos, raiz if raiz is not None else c


def metodo_newton_raphson(f, df, x0, tol, max_iter):
    tabla, pasos = [], []
    x_curr = float(x0)

    # ✅ MEJORA 1: validar dominio del punto inicial (mensaje claro)
    try:
        f_x0 = float(f(x_curr))
    except Exception as e:
        raise ValueError(
            f"El punto inicial x0 = {x_curr} está fuera del dominio de f: {e}"
        )
    if not math.isfinite(f_x0):
        raise ValueError(
            f"f(x0) = {f_x0} no es un valor finito. Prueba otro punto inicial."
        )

    raiz, x_next, fn = None, x_curr, f_x0

    for it in range(1, max_iter + 1):
        fx = float(f(x_curr))
        dfx = float(df(x_curr))
        if abs(dfx) < 1e-15:
            raise ValueError(
                f"La derivada es casi cero (f'({x_curr:.4f}) = {dfx:.4e}). "
                f"Newton-Raphson no puede continuar."
            )

        x_next = float(x_curr - (fx / dfx))

        # ✅ MEJORA 2: detectar divergencia numérica (inf / nan)
        if not math.isfinite(x_next):
            raise ValueError(
                f"Newton-Raphson divergió en la iteración {it}: x = {x_next}. "
                f"Prueba otro punto inicial o cambia de método."
            )

        fn = float(f(x_next))

        # ✅ MEJORA 3: detectar salida del dominio de f
        if not math.isfinite(fn):
            raise ValueError(
                f"f(x) no es finita en x = {x_next:.6f} (f = {fn}). "
                f"El método salió del dominio. Prueba otro método."
            )

        error_abs = abs(x_next - x_curr)
        error_rel = (error_abs / abs(x_next)) * 100.0 if x_next != 0 else None
        er_display = f"{error_rel:.4f}%" if error_rel is not None else "—"

        tabla.append({
            'it': it,
            'x_k': x_curr, 'fx_k': fx, 'dfx_k': dfx,
            'x_next': x_next, 'fx_next': fn,
            'error_abs': error_abs, 'error_rel': error_rel,
        })

        explicacion_formula = (
            f"<b>Avance Tangencial:</b> x<sub>{it}</sub> = x<sub>{it-1}</sub> - "
            f"[f(x<sub>{it-1}</sub>) / f'(x<sub>{it-1}</sub>)] = "
            f"{x_curr:.6f} - [({fx:.6f}) / ({dfx:.6f})] = <b>{x_next:.6f}</b>.<br>"
            f"👉 La recta tangente en x = {x_curr:.6f} corta el eje X en "
            f"<b>x = {x_next:.6f}</b> con f(x<sub>{it}</sub>) = {fn:.6f}."
        )

        explicacion_error = (
            f"<b>Cálculo de Error:</b> Ea = |{x_next:.6f} - {x_curr:.6f}| = "
            f"<b>{error_abs:.6f}</b> (Error Relativo Er = <b>{er_display}</b>). "
        )
        if error_abs < tol or abs(fn) < 1e-12:
            explicacion_error += (
                f"<span class='text-success fw-bold'>¡Convergencia alcanzada! "
                f"(Ea &lt; Tol={tol}).</span>"
            )
        else:
            explicacion_error += (
                f"<span class='text-muted'>Aún no converge, x<sub>{it}</sub> pasa "
                f"a ser la nueva aproximación.</span>"
            )

        pasos.append(f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark fs-6'>📌 Iteración {it} (Método de Newton-Raphson)</span>
                <span class='badge bg-primary fs-6'>Siguiente x<sub>{it}</sub> = {x_next:.6f}</span>
            </div>
            <div class='card-body p-3'>
                <div class='table-responsive mb-2'>
                    <table class='table table-sm table-bordered text-center align-middle mb-0'
                           style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>x<sub>k</sub> (Actual)</th>
                                <th>f(x<sub>k</sub>)</th>
                                <th>f'(x<sub>k</sub>) [Derivada]</th>
                                <th>x<sub>{it}</sub> [Nueva Aprox]</th>
                                <th>f(x<sub>{it}</sub>)</th>
                                <th>Error Abs (Ea)</th>
                                <th>Error Rel (Er %)</th>
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
                                <td class='text-success'>{er_display}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-light border p-2 mb-2 small'>{explicacion_formula}</div>
                <div class='alert alert-secondary p-2 mb-0 small'>💡 {explicacion_error}</div>
            </div>
        </div>
        """)

        if abs(fn) < 1e-12 or error_abs < tol:
            raiz = x_next
            break

        x_curr = x_next

    return tabla, pasos, raiz if raiz is not None else x_next


def metodo_secante(f, x0, x1, tol, max_iter):
    tabla, pasos = [], []
    x0_curr, x1_curr = float(x0), float(x1)
    raiz = None
    x2 = x1_curr

    for it in range(1, max_iter + 1):
        fx0 = float(f(x0_curr))
        fx1 = float(f(x1_curr))

        diff_y = fx1 - fx0
        if abs(diff_y) < 1e-15:
            raise ValueError(
                f"División por cero en la secante: f(x1) - f(x0) ≈ 0 "
                f"en iteración {it}."
            )

        x2 = float(x1_curr - (fx1 * (x1_curr - x0_curr)) / diff_y)

        # ✅ MEJORA 2: detectar divergencia numérica
        if not math.isfinite(x2):
            raise ValueError(
                f"Secante divergió en la iteración {it}: x = {x2}. "
                f"Prueba otros puntos iniciales."
            )

        fx2 = float(f(x2))

        # ✅ MEJORA 3: detectar salida del dominio de f
        if not math.isfinite(fx2):
            raise ValueError(
                f"f(x) no es finita en x = {x2:.6f}. "
                f"El método salió del dominio. Prueba otro método."
            )

        error_abs = abs(x2 - x1_curr)
        error_rel = (error_abs / abs(x2)) * 100.0 if x2 != 0 else None
        er_display = f"{error_rel:.4f}%" if error_rel is not None else "—"

        tabla.append({
            'it': it,
            'x_k': x0_curr, 'x_k1': x1_curr,
            'fx_k': fx0, 'fx_k1': fx1,
            'x_next': x2, 'fx_next': fx2,
            'error_abs': error_abs, 'error_rel': error_rel,
        })

        explicacion_formula = (
            f"<b>Secante Trazada:</b> x<sub>{it+1}</sub> = x<sub>{it}</sub> - "
            f"[f(x<sub>{it}</sub>)·(x<sub>{it}</sub> - x<sub>{it-1}</sub>) / "
            f"(f(x<sub>{it}</sub>) - f(x<sub>{it-1}</sub>))]<br>"
            f"👉 Sustituyendo: {x1_curr:.6f} - [({fx1:.6f})·({x1_curr:.6f} - "
            f"{x0_curr:.6f}) / ({fx1:.6f} - ({fx0:.6f}))] = <b>{x2:.6f}</b>.<br>"
            f"📌 La secante corta el eje X en <b>x = {x2:.6f}</b> con f(x) = {fx2:.6f}."
        )

        explicacion_error = (
            f"<b>Cálculo de Error:</b> Ea = |{x2:.6f} - {x1_curr:.6f}| = "
            f"<b>{error_abs:.6f}</b> (Error Relativo Er = <b>{er_display}</b>). "
        )
        if error_abs < tol or abs(fx2) < 1e-12:
            explicacion_error += (
                f"<span class='text-success fw-bold'>¡Criterio de parada satisfecho! "
                f"(Ea &lt; Tol={tol}).</span>"
            )
        else:
            explicacion_error += (
                f"<span class='text-muted'>Se actualizan los puntos: "
                f"x0 ⬅ {x1_curr:.6f}, x1 ⬅ {x2:.6f}.</span>"
            )

        pasos.append(f"""
        <div class='card mb-3 shadow-sm border-info'>
            <div class='card-header bg-light d-flex justify-content-between align-items-center py-2'>
                <span class='fw-bold text-dark fs-6'>📌 Iteración {it} (Método de la Secante)</span>
                <span class='badge bg-primary fs-6'>Nueva Aprox x<sub>{it+1}</sub> = {x2:.6f}</span>
            </div>
            <div class='card-body p-3'>
                <div class='table-responsive mb-2'>
                    <table class='table table-sm table-bordered text-center align-middle mb-0'
                           style='font-size: 0.88rem; background-color: #ffffff;'>
                        <thead class='table-secondary'>
                            <tr>
                                <th>x<sub>{it-1}</sub></th>
                                <th>x<sub>{it}</sub></th>
                                <th>f(x<sub>{it-1}</sub>)</th>
                                <th>f(x<sub>{it}</sub>)</th>
                                <th>x<sub>{it+1}</sub> [Aprox Secante]</th>
                                <th>f(x<sub>{it+1}</sub>)</th>
                                <th>Error Abs (Ea)</th>
                                <th>Error Rel (Er %)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{x0_curr:.6f}</td>
                                <td>{x1_curr:.6f}</td>
                                <td>{fx0:.6f}</td>
                                <td>{fx1:.6f}</td>
                                <td class='fw-bold text-primary'>{x2:.6f}</td>
                                <td>{fx2:.6f}</td>
                                <td class='text-danger'>{error_abs:.6f}</td>
                                <td class='text-success'>{er_display}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class='alert alert-light border p-2 mb-2 small'>{explicacion_formula}</div>
                <div class='alert alert-secondary p-2 mb-0 small'>💡 {explicacion_error}</div>
            </div>
        </div>
        """)

        if abs(fx2) < 1e-12 or error_abs < tol:
            raiz = x2
            break

        x0_curr, x1_curr = x1_curr, x2

    return tabla, pasos, raiz if raiz is not None else x2


# ============================================================
# RUTAS FLASK
# ============================================================

def _limpiar_str(v, default):
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@bp_raices.route('/raices/graficar', methods=['POST'])
def raices_graficar():
    datos = request.get_json(silent=True) or {}
    try:
        f, _, f_str, _ = obtener_funciones(datos.get('ecuacion', ''))
        xmin = parse_float_flexible(datos.get('xmin'), -5.0)
        xmax = parse_float_flexible(datos.get('xmax'), 5.0)
        if xmin >= xmax:
            raise ValueError(
                "En 'Ver desde / hasta', el primer número debe ser menor que el segundo."
            )
        return jsonify(
            ok=True,
            puntos=generar_puntos(f, xmin, xmax),
            interpretacion=bonito(f_str),
        )
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
            puntos_grafica=puntos_iniciales,
            derivada_tex="", interpretacion="",
        )

    ecuacion_input = _limpiar_str(request.form.get('ecuacion'), def_ecuacion)
    metodo = _limpiar_str(request.form.get('metodo'), def_metodo)
    a_str = _limpiar_str(request.form.get('a'), def_a)
    b_str = _limpiar_str(request.form.get('b'), def_b)
    tol_str = _limpiar_str(request.form.get('tol'), def_tol)
    max_iter_str = _limpiar_str(request.form.get('max_iter'), def_max_iter)

    tabla, pasos, puntos_grafica = [], [], []
    raiz_hallada, error = None, None
    derivada_tex, interpretacion = "", ""

    try:
        a_val = parse_float_flexible(a_str, 0.0)
        b_val = parse_float_flexible(b_str, a_val + 1.0)
        tol_val = parse_float_flexible(tol_str, 0.0001)
        if tol_val <= 0:
            raise ValueError("La tolerancia debe ser un número positivo.")
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
        else:
            raise ValueError(f"Método desconocido: {metodo}")

        if raiz_hallada is not None:
            raiz_hallada = float(raiz_hallada)

    except Exception as e:
        error = f"Ocurrió un error: {str(e)}"

    return render_template(
        'raices.html', ecuacion=ecuacion_input, metodo=metodo,
        a=a_str, b=b_str, tol=tol_str, max_iter=max_iter_str,
        tabla=tabla, pasos=pasos, raiz_hallada=raiz_hallada,
        error=error, puntos_grafica=puntos_grafica,
        derivada_tex=derivada_tex, interpretacion=interpretacion,
    )