"""
Cálculo de determinantes con procedimiento paso a paso.

Métodos disponibles (basados en la presentación "Determinantes"):
  - cofactores  : desarrollo por cofactores (diapositivas 9-13). Requiere ~n! multiplicaciones.
  - sarrus      : regla de Sarrus, solo para matrices 3x3 (diapositiva 29).
  - eliminacion : reducción a forma triangular con operaciones de fila (diapositivas 15 y 18-24).
                  det A = (-1)^k · (producto de la diagonal de U), con k = número de intercambios.
  - auto        : cofactores si n <= 3 y eliminación si n >= 4 (diapositivas 15-16).

Nota: la regla de Cramer (diapositivas 30-32) sirve para RESOLVER sistemas Ax = b usando
determinantes; no es un método para calcular un determinante.

Todo el cálculo usa fracciones exactas para evitar errores de redondeo.
Todos los errores de validación se lanzan como ErrorDeterminante (subclase de ValueError)
y sus mensajes están en castellano.
"""
import re
from fractions import Fraction

METODOS_VALIDOS = ("auto", "cofactores", "sarrus", "eliminacion")
MAX_N = 10                # tamaño máximo aceptado (N x N)
MAX_N_COFACTORES = 8      # más allá de esto, n! es demasiado costoso (diapositivas 15-16)
LIMITE_VALOR = 10 ** 12   # valor absoluto máximo aceptado en cada entrada
LARGO_MAX_TEXTO = 40      # largo máximo del texto de un número

# Tamaños de letra del paso a paso (se pueden ajustar aquí)
TAMANO_TEXTO_PASOS = "1.25em"      # texto de cada paso
TAMANO_TEXTO_RESULTADO = "1.4em"   # línea del determinante final
TAMANO_TABLAS = "1.35em"           # números dentro de las matrices

# Formatos aceptados: 5, -3, 2.5, .5, 1e3, 1.5e-2, 3/4
_PATRON_NUMERO = re.compile(
    r"[+-]?(?:\d+/\d+|(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d{1,3})?)"
)


class ErrorDeterminante(ValueError):
    """Error de validación de los datos de entrada (mensaje siempre en castellano)."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def a_fraccion(valor, ubicacion=""):
    """
    Convierte un número (int, float, str o Fraction) a una Fraction exacta.
    'ubicacion' es un texto opcional, por ejemplo " (fila 2, columna 3)", que se
    agrega a los mensajes de error.
    """
    def mensaje_invalido():
        texto = str(valor)[:LARGO_MAX_TEXTO]
        return f"Valor no válido{ubicacion}: {texto!r}. Debe ser un número (por ejemplo 5, -3, 2.5 o 3/4)."

    if isinstance(valor, bool):
        raise ErrorDeterminante(mensaje_invalido())

    if isinstance(valor, (int, Fraction)):
        resultado = Fraction(valor)
    else:
        texto = str(valor).strip()
        if len(texto) > LARGO_MAX_TEXTO or not _PATRON_NUMERO.fullmatch(texto):
            raise ErrorDeterminante(mensaje_invalido())
        try:
            resultado = Fraction(texto.replace(",", "."))
        except (ValueError, ZeroDivisionError):
            raise ErrorDeterminante(mensaje_invalido())

    if abs(resultado) > LIMITE_VALOR:
        raise ErrorDeterminante(
            f"El valor{ubicacion} es demasiado grande: el máximo permitido es "
            f"{LIMITE_VALOR} en valor absoluto."
        )
    return resultado


def fmt(x):
    """Texto de un número: entero si se puede, o fracción a/b."""
    x = Fraction(x)
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def par(x):
    """Igual que fmt, pero entre paréntesis si el número es negativo."""
    x = Fraction(x)
    return fmt(x) if x >= 0 else f"({fmt(x)})"


def fmt_final(x):
    """Texto del resultado final (con aproximación decimal si es una fracción)."""
    x = Fraction(x)
    if x.denominator == 1:
        return fmt(x)
    return f"{fmt(x)} ≈ {float(x):.6g}"


def a_numero(x):
    """Resultado para devolver: int si es entero, float en otro caso."""
    x = Fraction(x)
    return x.numerator if x.denominator == 1 else float(x)


def copiar_matriz(matriz):
    """Crea una copia exacta de la matriz para no modificar la original."""
    return [fila[:] for fila in matriz]


def formatear_matriz(matriz):
    """Convierte la matriz a una tabla HTML para mostrarla en el paso a paso."""
    res = (f"<table style='margin: 10px auto; border-collapse: collapse; text-align: center; "
           f"font-size: {TAMANO_TABLAS};'>")
    for fila in matriz:
        res += "<tr>"
        for val in fila:
            res += f"<td style='padding: 8px; border: 1px solid white;'>{fmt(val)}</td>"
        res += "</tr>"
    res += "</table>"
    return res


def dar_formato_pasos(pasos):
    """
    Devuelve los pasos con la letra más grande. Solo cambia el tamaño de la fuente:
    no altera la alineación ni el espaciado, porque usa un <span> (en línea) y no un bloque.
    Las tablas ya traen su propio tamaño.
    """
    resultado = []
    for paso in pasos:
        if paso.startswith("<table"):
            resultado.append(paso)
            continue
        tamano = TAMANO_TEXTO_RESULTADO if "Determinante final" in paso else TAMANO_TEXTO_PASOS
        resultado.append(f"<span style='font-size: {tamano};'>{paso}</span>")
    return resultado


def matriz_desde_formulario(formulario, dimension):
    """
    Lee del formulario HTML los campos m_i_j y devuelve la matriz n x n.
    Uso en Flask:
        matriz = matriz_desde_formulario(request.form, request.form.get('dimension'))
    """
    try:
        n = int(str(dimension).strip())
    except (TypeError, ValueError):
        raise ErrorDeterminante("La dimensión debe ser un número entero.")
    if not 1 <= n <= MAX_N:
        raise ErrorDeterminante(f"La dimensión debe estar entre 1 y {MAX_N}.")
    if not hasattr(formulario, "get"):
        raise ErrorDeterminante("El formulario recibido no es válido.")

    matriz = []
    for i in range(n):
        fila = []
        for j in range(n):
            ubicacion = f" (fila {i + 1}, columna {j + 1})"
            bruto = formulario.get(f"m_{i}_{j}")
            if bruto is None or str(bruto).strip() == "":
                raise ErrorDeterminante(f"Falta el valor{ubicacion}.")
            fila.append(a_fraccion(bruto, ubicacion))
        matriz.append(fila)
    return matriz


def _menor(matriz, i, j):
    """Submatriz que resulta de eliminar la fila i y la columna j."""
    return [fila[:j] + fila[j + 1:] for k, fila in enumerate(matriz) if k != i]


def _mejor_fila(matriz):
    """Fila con más ceros (en caso de empate, la primera): simplifica el desarrollo."""
    n = len(matriz)
    return max(range(n), key=lambda i: (sum(1 for v in matriz[i] if v == 0), -i))


def _det_rec(matriz):
    """Determinante por cofactores sin registrar pasos (se usa para calcular los menores)."""
    n = len(matriz)
    if n == 1:
        return matriz[0][0]
    if n == 2:
        return matriz[0][0] * matriz[1][1] - matriz[0][1] * matriz[1][0]
    i = _mejor_fila(matriz)
    total = Fraction(0)
    for j in range(n):
        a = matriz[i][j]
        if a == 0:
            continue
        total += (-1) ** (i + j) * a * _det_rec(_menor(matriz, i, j))
    return total


# ---------------------------------------------------------------------------
# Método 1: cofactores
# ---------------------------------------------------------------------------
def determinante_cofactores(matriz, pasos):
    """Desarrollo por cofactores: det A = Σ aij · Cij, con Cij = (-1)^(i+j) · Mij."""
    n = len(matriz)

    if n == 1:
        pasos.append(f"* Matriz 1x1. El determinante es el único elemento: {fmt(matriz[0][0])}")
        return matriz[0][0]

    if n == 2:
        a, b = matriz[0]
        c, d = matriz[1]
        det = a * d - b * c
        pasos.append("* Matriz 2x2 detectada. Aplicando la fórmula: det A = (a·d) − (b·c)")
        pasos.append(f"* Cálculo: ({fmt(a)} · {fmt(d)}) − ({fmt(b)} · {fmt(c)}) = {fmt(det)}")
        return det

    i = _mejor_fila(matriz)
    pasos.append(f"* Desarrollo por cofactores a lo largo de la fila {i + 1} "
                 f"(la que tiene más ceros) de la matriz {n}x{n}:")
    pasos.append(formatear_matriz(matriz))
    pasos.append("* Fórmula: det A = Σ aij · Cij, donde Cij = (−1)<sup>i+j</sup> · Mij "
                 "y Mij es el Menor (determinante de la submatriz sin la fila i y la columna j).")

    terminos = []
    total = Fraction(0)
    for j in range(n):
        a = matriz[i][j]
        if a == 0:
            pasos.append(f"<br>* a{i + 1}{j + 1} = 0 → su término vale 0, no hace falta calcular su Menor.")
            continue

        signo = (-1) ** (i + j)
        simbolo = "+1" if signo == 1 else "−1"
        menor = _menor(matriz, i, j)
        M = _det_rec(menor)
        C = signo * M
        termino = a * C

        pasos.append(f"<br>* Elemento a{i + 1}{j + 1} = {fmt(a)}. Signo (−1)<sup>{i + 1}+{j + 1}</sup> = {simbolo}. "
                     f"Menor M{i + 1}{j + 1} (se elimina la fila {i + 1} y la columna {j + 1}):")
        pasos.append(formatear_matriz(menor))
        if len(menor) == 2:
            pasos.append(f"* M{i + 1}{j + 1} = ({par(menor[0][0])} · {par(menor[1][1])}) − "
                         f"({par(menor[0][1])} · {par(menor[1][0])}) = {fmt(M)}")
        else:
            pasos.append(f"* M{i + 1}{j + 1} = {fmt(M)}")
        pasos.append(f"* C{i + 1}{j + 1} = ({signo}) · {par(M)} = {fmt(C)}")
        pasos.append(f"* Término: a{i + 1}{j + 1} · C{i + 1}{j + 1} = {par(a)} · {par(C)} = {fmt(termino)}")

        terminos.append(termino)
        total += termino

    suma = " + ".join(par(t) for t in terminos) if terminos else "0"
    pasos.append(f"<br>* Suma de los términos: {suma} = {fmt(total)}")
    pasos.append(f"<b>* Determinante final calculado por cofactores: {fmt_final(total)}</b>")
    return total


# ---------------------------------------------------------------------------
# Método 2: regla de Sarrus (solo 3x3)
# ---------------------------------------------------------------------------
def determinante_sarrus(matriz, pasos):
    """Regla de Sarrus para matrices 3x3."""
    m = matriz
    pasos.append("* Regla de Sarrus (3x3): se repiten las dos primeras columnas a la derecha de la matriz.")
    pasos.append(formatear_matriz([fila + fila[:2] for fila in m]))

    principales = [
        ("a11·a22·a33", m[0][0], m[1][1], m[2][2]),
        ("a12·a23·a31", m[0][1], m[1][2], m[2][0]),
        ("a13·a21·a32", m[0][2], m[1][0], m[2][1]),
    ]
    secundarias = [
        ("a13·a22·a31", m[0][2], m[1][1], m[2][0]),
        ("a11·a23·a32", m[0][0], m[1][2], m[2][1]),
        ("a12·a21·a33", m[0][1], m[1][0], m[2][2]),
    ]

    pasos.append("<br>* Diagonales principales (suman):")
    suma_pos = Fraction(0)
    for nombre, x, y, z in principales:
        prod = x * y * z
        suma_pos += prod
        pasos.append(f"* {nombre} = {par(x)} · {par(y)} · {par(z)} = {fmt(prod)}")
    pasos.append(f"* Suma de diagonales principales = {fmt(suma_pos)}")

    pasos.append("<br>* Diagonales secundarias (restan):")
    suma_neg = Fraction(0)
    for nombre, x, y, z in secundarias:
        prod = x * y * z
        suma_neg += prod
        pasos.append(f"* {nombre} = {par(x)} · {par(y)} · {par(z)} = {fmt(prod)}")
    pasos.append(f"* Suma de diagonales secundarias = {fmt(suma_neg)}")

    det = suma_pos - suma_neg
    pasos.append(f"<br>* det A = {fmt(suma_pos)} − {par(suma_neg)} = {fmt(det)}")
    pasos.append(f"<b>* ¡Determinante final calculado por Sarrus: {fmt_final(det)}!</b>")
    return det


# ---------------------------------------------------------------------------
# Método 3: eliminación (reducción a forma triangular)
# ---------------------------------------------------------------------------
def determinante_eliminacion(matriz, pasos):
    """
    Reduce A a una matriz triangular U usando SOLO reemplazos de fila (no cambian el
    determinante) e intercambios de fila (cambian el signo).
    Resultado: det A = (-1)^k · det U, y det U = producto de la diagonal (teorema).
    """
    n = len(matriz)
    A = copiar_matriz(matriz)
    intercambios = 0

    pasos.append("* Iniciando reducción a matriz triangular (operaciones de fila):")
    pasos.append("* Reemplazo Fi → Fi + k·Fj: el determinante NO cambia. "
                 "Intercambio Fi ↔ Fj: el determinante cambia de signo.")
    pasos.append(formatear_matriz(A))

    ya_triangular = all(A[r][c] == 0 for c in range(n) for r in range(c + 1, n))
    if ya_triangular:
        pasos.append("* La matriz ya es triangular: det A es el producto de las entradas de la diagonal principal.")

    for i in range(n):
        # Buscar una fila (desde i hacia abajo) con pivote distinto de cero
        fila_pivote = next((r for r in range(i, n) if A[r][i] != 0), None)

        if fila_pivote is None:
            pasos.append(f"* En la columna {i + 1} no hay pivote (todas las entradas desde la fila {i + 1} son 0): "
                         f"la forma escalonada tiene un 0 en la diagonal.")
            pasos.append("<b>* Determinante final: 0</b>")
            return Fraction(0)

        if fila_pivote != i:
            A[i], A[fila_pivote] = A[fila_pivote], A[i]
            intercambios += 1
            pasos.append(f"<br>* Intercambio de F{i + 1} con F{fila_pivote + 1} "
                         f"(el signo del determinante se invierte):")
            pasos.append(formatear_matriz(A))

        pivote = A[i][i]
        operaciones = []
        for j in range(i + 1, n):
            if A[j][i] != 0:
                factor = A[j][i] / pivote
                for k in range(i, n):
                    A[j][k] -= factor * A[i][k]
                operaciones.append(f"F{j + 1} → F{j + 1} − ({fmt(factor)})·F{i + 1}")

        if operaciones:
            pasos.append(f"<br>* Haciendo ceros debajo del pivote {fmt(pivote)} (columna {i + 1}):")
            for op in operaciones:
                pasos.append(f"&nbsp;&nbsp;{op}")
            pasos.append(formatear_matriz(A))

    pasos.append("<br>* Matriz triangular U obtenida. det U es el producto de su diagonal principal.")
    diagonal = [A[i][i] for i in range(n)]
    producto = Fraction(1)
    for d in diagonal:
        producto *= d
    pasos.append("* Multiplicando diagonal: " + " · ".join(par(d) for d in diagonal) + f" = {fmt(producto)}")

    det = (-1) ** intercambios * producto
    pasos.append(f"* Hubo {intercambios} intercambio(s) de filas: det A = (−1)<sup>{intercambios}</sup> · det U "
                 f"= {fmt((-1) ** intercambios)} · {par(producto)}")
    pasos.append(f"<b>* ¡Determinante final calculado por eliminación: {fmt_final(det)}!</b>")
    return det


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def calcular_determinante(matriz, metodo="auto"):
    """
    Calcula el determinante de una matriz cuadrada.
    Devuelve (resultado, pasos). 'pasos' es una lista de cadenas HTML.
    Lanza ErrorDeterminante (subclase de ValueError) si los datos o el método no son válidos.
    """
    # --- Validación de la estructura de la matriz ---
    if not isinstance(matriz, (list, tuple)) or len(matriz) == 0:
        raise ErrorDeterminante("La matriz no puede estar vacía y debe ser una lista de filas.")
    n = len(matriz)
    if n > MAX_N:
        raise ErrorDeterminante(f"El tamaño máximo permitido es {MAX_N}x{MAX_N}.")
    for i, fila in enumerate(matriz):
        if not isinstance(fila, (list, tuple)):
            raise ErrorDeterminante(f"La fila {i + 1} no es una lista de valores.")
        if len(fila) != n:
            raise ErrorDeterminante(
                f"La matriz debe ser cuadrada: tiene {n} fila(s), pero la fila {i + 1} "
                f"tiene {len(fila)} columna(s)."
            )

    # --- Validación del método ---
    if not isinstance(metodo, str):
        raise ErrorDeterminante("El método debe ser un texto: " + ", ".join(METODOS_VALIDOS) + ".")
    metodo = metodo.strip().lower()
    if metodo not in METODOS_VALIDOS:
        raise ErrorDeterminante(
            f"Método desconocido: {metodo[:LARGO_MAX_TEXTO]!r}. "
            f"Los métodos válidos son: " + ", ".join(METODOS_VALIDOS) + "."
        )

    # --- Validación de los valores ---
    A = [[a_fraccion(v, f" (fila {i + 1}, columna {j + 1})") for j, v in enumerate(fila)]
         for i, fila in enumerate(matriz)]

    pasos = []
    if metodo == "auto":
        if n <= 3:
            metodo_usado = "cofactores"
            pasos.append(f"* [MODO AUTOMÁTICO] Matriz pequeña ({n}x{n}). Método seleccionado: Cofactores.")
        else:
            metodo_usado = "eliminacion"
            pasos.append(f"* [MODO AUTOMÁTICO] Matriz grande ({n}x{n}). Método seleccionado: Eliminación "
                         f"(reducción a forma triangular), porque los cofactores requieren ~n! multiplicaciones.")
    else:
        metodo_usado = metodo

    if metodo_usado == "cofactores":
        if n > MAX_N_COFACTORES:
            raise ErrorDeterminante(
                f"Los cofactores requieren ~n! multiplicaciones; para {n}x{n} es inviable. "
                f"Usa el método de eliminación."
            )
        resultado = determinante_cofactores(A, pasos)
    elif metodo_usado == "sarrus":
        if n != 3:
            raise ErrorDeterminante("La regla de Sarrus solo se aplica a matrices 3x3.")
        resultado = determinante_sarrus(A, pasos)
    else:
        resultado = determinante_eliminacion(A, pasos)

    if resultado == 0:
        pasos.append("<br>* det A = 0 → A NO es invertible (el área/volumen colapsa y se pierde dimensión).")
    else:
        pasos.append("<br>* det A ≠ 0 → A es invertible.")

    return a_numero(resultado), dar_formato_pasos(pasos)


# ---------------------------------------------------------------------------
# Autopruebas: ejecuta  python determinantes.py
# ---------------------------------------------------------------------------
def _autopruebas():
    """Verifica el cálculo y las validaciones. Devuelve True si todo es correcto."""
    correcto = True

    def comprobar(descripcion, condicion):
        nonlocal correcto
        print(("  OK    " if condicion else "  FALLÓ ") + descripcion)
        if not condicion:
            correcto = False

    print("Pruebas de cálculo:")
    casos = [
        ("2x2 de la presentación", [[3, -2], [-5, 4]], 2),
        ("3x3 con ceros", [[1, 5, 0], [2, 4, -1], [0, -2, 0]], -2),
        ("3x3 con eliminación", [[1, -4, 2], [-2, 8, -9], [-1, 7, 0]], 15),
        ("triangular (3·2·(−2))", [[3, 5, 1], [0, 2, 7], [0, 0, -2]], -12),
        ("singular 2x2", [[1, 2], [2, 4]], 0),
        ("4x4 con intercambios", [[0, 2, 1, 3], [1, 0, 4, 2], [2, 1, 0, 1], [3, 1, 2, 0]], -33),
        ("matriz identidad 5x5", [[1 if i == j else 0 for j in range(5)] for i in range(5)], 1),
        ("1x1", [[7]], 7),
    ]
    for nombre, matriz, esperado in casos:
        for metodo in ("auto", "cofactores", "eliminacion") + (("sarrus",) if len(matriz) == 3 else ()):
            comprobar(f"{nombre} [{metodo}] = {esperado}", calcular_determinante(matriz, metodo)[0] == esperado)

    comprobar("decimales: [[0.5, 1], [2, 3.5]] = -0.25", calcular_determinante([[0.5, 1], [2, 3.5]])[0] == -0.25)
    comprobar("coma decimal: [['1,5', 2], [3, 4]] = 0", calcular_determinante([["1,5", 2], [3, 4]])[0] == 0)

    print("Pruebas de validación (todos los mensajes deben estar en castellano):")
    invalidos = [
        ("matriz vacía", [], "auto"),
        ("matriz no es lista", "abc", "auto"),
        ("matriz no cuadrada", [[1, 2]], "auto"),
        ("fila que no es lista", [[1, 2], 5], "auto"),
        ("tamaño mayor al máximo", [[1] * 11] * 11, "eliminacion"),
        ("Sarrus con 2x2", [[1, 2], [3, 4]], "sarrus"),
        ("cofactores 9x9", [[1] * 9] * 9, "cofactores"),
        ("texto en la matriz", [[1, "x"], [1, 1]], "auto"),
        ("booleano en la matriz", [[True, 1], [1, 1]], "auto"),
        ("infinito", [[float("inf"), 1], [1, 1]], "auto"),
        ("no es un número", [[float("nan"), 1], [1, 1]], "auto"),
        ("exponente enorme", [["1e999999999", 1], [1, 1]], "auto"),
        ("valor demasiado grande", [[10 ** 13, 1], [1, 1]], "auto"),
        ("división entre cero", [["1/0", 1], [1, 1]], "auto"),
        ("método desconocido", [[1]], "cramer"),
        ("método no es texto", [[1]], None),
    ]
    for descripcion, matriz, metodo in invalidos:
        try:
            calcular_determinante(matriz, metodo)
            comprobar(f"{descripcion}: debía dar error", False)
        except ErrorDeterminante as error:
            comprobar(f"{descripcion}: {error}", True)

    class FormularioFalso:
        def __init__(self, datos):
            self.datos = datos

        def get(self, clave, defecto=None):
            return self.datos.get(clave, defecto)

    formulario = FormularioFalso({"m_0_0": "2", "m_0_1": "1", "m_1_0": "1", "m_1_1": "3"})
    comprobar("formulario válido 2x2 = 5",
              calcular_determinante(matriz_desde_formulario(formulario, "2"))[0] == 5)
    for descripcion, formulario_prueba, dim in [
        ("dimensión con texto", formulario, "abc"),
        ("dimensión ausente", formulario, None),
        ("dimensión fuera de rango", formulario, "0"),
        ("campo faltante", FormularioFalso({"m_0_0": "1"}), "2"),
        ("campo con texto", FormularioFalso({"m_0_0": "a"}), "1"),
        ("formulario inválido", 5, "1"),
    ]:
        try:
            matriz_desde_formulario(formulario_prueba, dim)
            comprobar(f"{descripcion}: debía dar error", False)
        except ErrorDeterminante as error:
            comprobar(f"{descripcion}: {error}", True)

    print("RESULTADO: " + ("todas las pruebas pasaron." if correcto else "hay pruebas que fallaron."))
    return correcto


if __name__ == "__main__":
    raise SystemExit(0 if _autopruebas() else 1)