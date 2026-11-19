import random
from flask import Flask, render_template, request

import undertale
from matrices import bp_matrices
from vectores import bp_vectores
from sistemas import bp_sistemas
from romanos import bp_romanos
from raices import bp_raices

app = Flask(__name__)

app.register_blueprint(bp_matrices)
app.register_blueprint(bp_vectores)
app.register_blueprint(bp_sistemas)
app.register_blueprint(bp_romanos)
app.register_blueprint(bp_raices)  

@app.route('/')
@app.route('/menu')
def menu():
    imagen_banner = random.choice(['ban.png', 'banalt.png', 'banp.png', 'banp1.png', 'banp2.png', 'banp3.png'])
    return render_template('menu.html', imagen_banner=imagen_banner)

@app.route('/undertale')
def nivel_determinacion():
    return render_template('undertale.html')

@app.route('/resolver_determinacion', methods=['POST'])
def resolver_determinacion():
    try:
        n = int(request.form['dimension'])
        metodo_seleccionado = request.form['metodo']
        
        matriz = []
        for i in range(n):
            fila = []
            for j in range(n):
                valor = float(request.form[f'm_{i}_{j}'])
                fila.append(valor)
            matriz.append(fila)
        
        # Obtener el resultado y la lista de pasos desde undertale.py
        resultado, pasos = undertale.calcular_determinante(matriz, metodo_seleccionado)
        resultado_redondeado = round(resultado, 4)

        # Mostrar el resultado con el diseño del Recinto 5 (solo presentación)
        return render_template('undertale_resultado.html', pasos=pasos, resultado=resultado_redondeado)
    except Exception as e:
        return render_template('undertale_resultado.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)