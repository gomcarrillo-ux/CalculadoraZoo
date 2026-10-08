def copiar_matriz(matriz):
    """Crea una copia exacta de la matriz para no modificar la original."""
    return [fila[:] for fila in matriz]

def formatear_matriz(matriz):
    """Convierte la matriz a una tabla HTML para mostrarla en el paso a paso."""
    res = "<table style='margin: 10px auto; border-collapse: collapse; text-align: center; font-size: 1.1em;'>"
    for fila in matriz:
        res += "<tr>"
        for val in fila:
            res += f"<td style='padding: 8px; border: 1px solid white;'>{round(val, 4)}</td>"
        res += "</tr>"
    res += "</table>"
    return res

def determinante_cofactores(matriz, pasos, nivel=0):
    """
    Calcula el determinante usando la expansión por cofactores.
    Registra el paso a paso.
    """
    n = len(matriz)
    if n == 1:
        if nivel == 0: 
            pasos.append("* Matriz 1x1. El determinante es el único elemento: " + str(matriz[0][0]))
        return matriz[0][0]
    
    if n == 2:
        det = (matriz[0][0] * matriz[1][1]) - (matriz[0][1] * matriz[1][0])
        if nivel == 0:
            pasos.append("* Matriz 2x2 detectada. Aplicando fórmula: (a*d) - (b*c)")
            pasos.append(f"* Cálculo: ({matriz[0][0]} * {matriz[1][1]}) - ({matriz[0][1]} * {matriz[1][0]}) = {det}")
        return det
    
    det = 0
    if nivel == 0:
        pasos.append(f"* Iniciando expansión por cofactores (fila 1) para matriz {n}x{n}:")
        pasos.append(formatear_matriz(matriz))
        
    for c in range(n):
        # Crear la submatriz eliminando la primera fila y la columna actual
        menor = [fila[:c] + fila[c+1:] for fila in matriz[1:]]
        signo = (-1) ** c
        valor_actual = matriz[0][c]
        
        if nivel == 0:
            pasos.append(f"<br>* Submatriz para el elemento {valor_actual} (Signo multiplicador: {signo}):")
            pasos.append(formatear_matriz(menor))
            
        sub_det = determinante_cofactores(menor, pasos, nivel + 1)
        det += signo * valor_actual * sub_det
        
    if nivel == 0:
        pasos.append(f"<br><b>* ¡Determinante final calculado por cofactores: {round(det, 4)}!</b>")
        
    return det

def determinante_lu_triangular(matriz, pasos):
    """
    Calcula el determinante usando reducción a matriz triangular (Eliminación Gaussiana).
    Este es el método eficiente asociado a sistemas de Cramer para matrices grandes.
    """
    n = len(matriz)
    A = copiar_matriz(matriz)
    det = 1.0
    
    pasos.append("* Iniciando reducción a matriz triangular (Eliminación de Gauss / Cramer):")
    pasos.append(formatear_matriz(A))

    for i in range(n):
        # Buscar el mayor pivote
        fila_pivote = i
        for j in range(i + 1, n):
            if abs(A[j][i]) > abs(A[fila_pivote][i]):
                fila_pivote = j
        
        # Si el pivote es 0, el determinante es 0
        if A[fila_pivote][i] == 0:
            pasos.append(f"* El pivote en la columna {i+1} es 0. La matriz es singular (no tiene inversa).")
            pasos.append("<b>* Determinante final: 0</b>")
            return 0.0
        
        # Intercambiar filas si es necesario
        if fila_pivote != i:
            A[i], A[fila_pivote] = A[fila_pivote], A[i]
            det *= -1.0
            pasos.append(f"* Intercambio de fila {i+1} con fila {fila_pivote+1} (el signo del determinante se invierte):")
            pasos.append(formatear_matriz(A))
        
        pivote = A[i][i]
        det *= pivote
        
        hubo_cambio = False
        # Hacer ceros debajo del pivote
        for j in range(i + 1, n):
            factor = A[j][i] / pivote
            if factor != 0:
                hubo_cambio = True
                for k in range(i, n):
                    A[j][k] -= factor * A[i][k]
                    
        if hubo_cambio:
            pasos.append(f"* Haciendo ceros debajo del pivote {round(pivote, 4)} en la columna {i+1}:")
            pasos.append(formatear_matriz(A))

    pasos.append("<br>* Matriz triangular obtenida. El determinante es el producto de su diagonal principal.")
    diagonal_str = " * ".join([str(round(A[i][i], 4)) for i in range(n)])
    pasos.append(f"* Multiplicando diagonal: {diagonal_str}")
    pasos.append(f"<b>* ¡Determinante final calculado: {round(det, 4)}!</b>")
    return det

def calcular_determinante(matriz, metodo="auto"):
    """
    Función principal que decide qué método utilizar y devuelve el resultado junto con los pasos.
    """
    n = len(matriz)
    if any(len(fila) != n for fila in matriz):
        raise ValueError("La matriz debe ser cuadrada.")
    
    pasos = []
    
    # El programa considera el más eficiente si está en "auto"
    if metodo == "auto":
        if n <= 3:
            metodo_usado = "cofactores"
            pasos.append(f"* [MODO AUTOMÁTICO] Matriz pequeña ({n}x{n}) detectada. Método seleccionado: Cofactores.")
        else:
            metodo_usado = "eliminacion"
            pasos.append(f"* [MODO AUTOMÁTICO] Matriz grande ({n}x{n}) detectada. Método seleccionado: Eliminación Gaussiana (Cramer eficiente).")
    else:
        metodo_usado = metodo

    if metodo_usado == "cofactores":
        resultado = determinante_cofactores(matriz, pasos)
    else:
        resultado = determinante_lu_triangular(matriz, pasos)
        
    return resultado, pasos