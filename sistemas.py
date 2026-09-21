# sistemas.py
"""Módulo de conversión entre bases numéricas."""
from flask import Blueprint, render_template, request

bp_sistemas = Blueprint('sistemas', __name__)


# ==============================================================================
# LÓGICA DE CONVERSIÓN
# ==============================================================================

def convert_decimal_to_base(decimal_value, target_base):
    """Convierte un decimal a la base destino. Devuelve (resultado, pasos_html)."""
    if decimal_value == 0:
        return "0", "0 dividido por cualquier base = 0 (residuo 0)"

    hex_digits = "0123456789ABCDEF"
    remainders = []
    steps = []
    quotient = decimal_value

    while quotient > 0:
        remainder = quotient % target_base
        new_quotient = quotient // target_base
        character = hex_digits[remainder]
        steps.append(
            f"{quotient} / {target_base} = {new_quotient} "
            f"&rarr; Residuo: {remainder} (dígito '{character}')"
        )
        remainders.append(character)
        quotient = new_quotient

    remainders.reverse()
    return "".join(remainders), "<br>".join(steps)


def convert_base_to_decimal(number_str, source_base):
    """Convierte un número en base origen a decimal. Devuelve (valor, pasos_html)."""
    number_str = str(number_str).strip().upper()
    hex_digits = "0123456789ABCDEF"
    accumulated = 0
    length = len(number_str)
    steps = []

    for index, character in enumerate(number_str):
        digit_value = hex_digits.index(character)
        power = length - 1 - index
        accumulated += digit_value * (source_base ** power)
        steps.append(f"{digit_value} &middot; {source_base}^{power}")

    step_text = " + ".join(steps) + f" = {accumulated}"
    return accumulated, step_text


# ==============================================================================
# RUTA
# ==============================================================================

@bp_sistemas.route('/sistemas', methods=['GET', 'POST'])
def sistemas():
    if request.method == 'GET':
        return render_template('sistemas.html', base=10)

    input_number = request.form.get('numero', '')
    source_base = int(request.form.get('base', 10))
    results, steps, error = {}, [], None

    if not input_number:
        return render_template('sistemas.html', base=source_base)

    try:
        decimal_value, decimal_steps = convert_base_to_decimal(
            input_number, source_base
        )
        if source_base != 10:
            steps.append((
                f"Paso 1: Convertir de Base {source_base} a Decimal",
                decimal_steps,
            ))
        else:
            steps.append((
                "Paso 1: Valor Decimal (Ya está en base 10)",
                str(decimal_value),
            ))

        binary_value, binary_steps = convert_decimal_to_base(decimal_value, 2)
        steps.append((
            "Paso 2: Convertir a Binario (Divisiones sucesivas entre 2)",
            binary_steps,
        ))

        octal_value, octal_steps = convert_decimal_to_base(decimal_value, 8)
        steps.append((
            "Paso 3: Convertir a Octal (Divisiones sucesivas entre 8)",
            octal_steps,
        ))

        hexadecimal_value, hexadecimal_steps = convert_decimal_to_base(
            decimal_value, 16
        )
        steps.append((
            "Paso 4: Convertir a Hexadecimal (Divisiones sucesivas entre 16)",
            hexadecimal_steps,
        ))

        results = {
            'Decimal': str(decimal_value),
            'Binario': binary_value,
            'Octal': octal_value,
            'Hexadecimal': hexadecimal_value,
        }
    except Exception:
        error = (
            f"El valor '{input_number}' no es válido para base {source_base}."
        )

    return render_template(
        'sistemas.html',
        resultados=results,
        pasos=steps,
        error=error,
        numero=input_number,
        base=source_base,
    )