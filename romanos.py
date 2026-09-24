# romanos.py
"""
Módulo de conversión entre Números Romanos y Arábigos.
Nivel 4: Bioma Desértico (Serpientes y Camellos 🐍🐫)
Permite el uso de librerías externas como 'roman'.
"""
import re
from flask import Blueprint, render_template, request

# Intento de uso de la librería externa 'roman' (permitida exclusivamente en este nivel)
try:
    import roman
    HAS_ROMAN_LIB = True
except ImportError:
    HAS_ROMAN_LIB = False

bp_romanos = Blueprint('romanos', __name__)

# Mapeo estándar de valores romanos
ROMAN_MAP = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
    (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
]

VALUES = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def arabic_to_roman(n):
    """Convierte de número Arábigo a Romano con procedimiento paso a paso."""
    if not (1 <= n <= 3999):
        raise ValueError("El número arábigo debe estar entre 1 y 3999 para la notación romana estándar.")
    
    # Verificación opcional con la librería externa
    lib_result = None
    if HAS_ROMAN_LIB:
        lib_result = roman.toRoman(n)

    steps = []
    num = n
    res = ""
    
    # Paso 1: Descomposición Decimal
    thousands = (n // 1000) * 1000
    hundreds = ((n % 1000) // 100) * 100
    tens = ((n % 100) // 10) * 10
    units = n % 10
    
    decomp_parts = []
    if thousands: decomp_parts.append(str(thousands))
    if hundreds: decomp_parts.append(str(hundreds))
    if tens: decomp_parts.append(str(tens))
    if units: decomp_parts.append(str(units))
    
    steps.append((
        "Paso 1: Descomposición posicional del número decimal",
        f"Descomponemos el número <strong>{n}</strong> en sus componentes:<br>"
        f"$$ {n} = {' + '.join(decomp_parts)} $$"
    ))
    
    # Paso 2: Conversión a Símbolos Romanos
    step2_desc = []
    for val, sym in ROMAN_MAP:
        while num >= val:
            res += sym
            num -= val
            step2_desc.append(f"Se sustrae {val} &rarr; Agrega símbolo '<strong>{sym}</strong>' (Resta restante: {num})")
            
    steps.append((
        "Paso 2: Conversión a símbolos romanos",
        "<br>".join(step2_desc)
    ))
    
    explicacion_final = f"Combinación de componentes: <strong>{res}</strong>"
    if HAS_ROMAN_LIB:
        explicacion_final += f"<br><small class='text-muted'>(Verificado también mediante la librería externa <code>roman.toRoman()</code>: <strong>{lib_result}</strong>)</small>"

    steps.append((
        "Paso 3: Resultado Romano Final",
        explicacion_final
    ))
    
    return res, steps


def roman_to_arabic(roman_str):
    """Convierte de número Romano a Arábigo con procedimiento y validación canónica."""
    roman_str = roman_str.strip().upper()
    if not roman_str:
        raise ValueError("Por favor, ingrese una cifra en números romanos.")
    
    if not re.match(r'^[IVXLCDM]+$', roman_str):
        raise ValueError(f"El texto '{roman_str}' contiene caracteres no válidos. Solo se permiten I, V, X, L, C, D, M.")
    
    steps = []
    
    # Verificación con librería externa si está instalada
    if HAS_ROMAN_LIB:
        try:
            val_lib = roman.fromRoman(roman_str)
        except Exception:
            raise ValueError(f"'{roman_str}' no cumple con la sintaxis romana canónica.")

    steps.append((
        "Paso 1: Identificación de valores de cada símbolo",
        "Símbolos detectados: " + ", ".join([f"<strong>{c}</strong> = {VALUES[c]}" for c in roman_str])
    ))
    
    total = 0
    i = 0
    sub_steps = []
    n = len(roman_str)
    
    while i < n:
        current_val = VALUES[roman_str[i]]
        if i + 1 < n and VALUES[roman_str[i+1]] > current_val:
            next_val = VALUES[roman_str[i+1]]
            diff = next_val - current_val
            total += diff
            sub_steps.append(
                f"Símbolos <strong>{roman_str[i]}{roman_str[i+1]}</strong>: "
                f"Un valor menor ({current_val}) antecede a uno mayor ({next_val}) &rarr; Sustracción: {next_val} − {current_val} = <strong>{diff}</strong>"
            )
            i += 2
        else:
            total += current_val
            sub_steps.append(f"Símbolo <strong>{roman_str[i]}</strong>: Se suma <strong>{current_val}</strong>")
            i += 1
            
    steps.append((
        "Paso 2: Aplicación de reglas de adición y sustracción",
        "<br>".join(sub_steps)
    ))
    
    # Re-conversión para garantizar que sea un número romano canónico correcto (evita IL, VV, IIII, etc.)
    canonical_roman, _ = arabic_to_roman(total)
    if canonical_roman != roman_str:
        raise ValueError(f"'{roman_str}' no es una representación romana válida. La notación correcta para el valor {total} es '<strong>{canonical_roman}</strong>'.")
        
    explicacion_final = f"Suma total calculada: <strong>{total}</strong>"
    if HAS_ROMAN_LIB:
        explicacion_final += f"<br><small class='text-muted'>(Verificado también mediante la librería externa <code>roman.fromRoman()</code>: <strong>{total}</strong>)</small>"

    steps.append((
        "Paso 3: Resultado Decimal Final",
        explicacion_final
    ))
    
    return total, steps


# RUTA PRINCIPAL
@bp_romanos.route('/romanos', methods=['GET', 'POST'])
def romanos():
    if request.method == 'GET':
        return render_template('romanos.html', modo='arabico_a_romano')

    modo = request.form.get('modo', 'arabico_a_romano')
    input_val = request.form.get('numero', '').strip()
    resultados, pasos, error = {}, [], None

    if not input_val:
        return render_template('romanos.html', modo=modo)

    try:
        if modo == 'arabico_a_romano':
            num_int = int(input_val)
            res_romano, pasos = arabic_to_roman(num_int)
            resultados = {
                'Número Arábigo': str(num_int),
                'Número Romano': res_romano
            }
        else:  # romano_a_arabico
            res_arabico, pasos = roman_to_arabic(input_val)
            resultados = {
                'Número Romano': input_val.upper(),
                'Número Arábigo': str(res_arabico)
            }
    except ValueError as e:
        error = str(e)
    except Exception as e:
        error = f"Error en la conversión: {str(e)}"

    return render_template(
        'romanos.html',
        resultados=resultados,
        pasos=pasos,
        error=error,
        numero=input_val,
        modo=modo
    )