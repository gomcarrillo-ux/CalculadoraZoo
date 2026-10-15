# main.py
import random
from flask import Flask, render_template, request, url_for

# Importación de todos los archivos / módulos
import undertale
from matrices import bp_matrices
from vectores import bp_vectores
from sistemas import bp_sistemas
from romanos import bp_romanos

app = Flask(__name__)

# Registro de los Blueprints para activar las rutas de cada programa
app.register_blueprint(bp_matrices)
app.register_blueprint(bp_vectores)
app.register_blueprint(bp_sistemas)
app.register_blueprint(bp_romanos)

# Ruta para el menú principal
@app.route('/')
@app.route('/menu')
def menu():
    # Selecciona dinámicamente entre ban.png y banalt.png al recargar
    imagen_banner = random.choice(['ban.png', 'banalt.png'])
    return render_template('menu.html', imagen_banner=imagen_banner)

# Ruta para entrar al nivel de Undertale
@app.route('/undertale')
def nivel_determinacion():
    return render_template('undertale.html')

# Ruta para procesar el cálculo dinámico del formulario
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

        # Convertir la lista de pasos a HTML
        pasos_html = ""
        for paso in pasos:
            pasos_html += f"<p style='text-align: left; margin-left: 10%;'>{paso}</p>"

        # Generar las URLs de las imágenes de forma segura antes del f-string
        imagen_sangui = url_for('static', filename='sangui.gif')
        imagen_towa = url_for('static', filename='towa.png')

        # Generar el HTML de respuesta dinámicamente
        return f"""
        <body style="background-color: black; color: white; text-align: center; font-family: 'Courier New', monospace; padding: 30px;">
            <h1>❤️ ¡GOLPE CRÍTICO!</h1>
            
            <div style="border: 2px solid white; padding: 20px; width: 80%; margin: 0 auto; background: #111; overflow-x: auto;">
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid white; padding-bottom: 10px; margin-bottom: 15px;">
                    <h3 style="text-align: left; margin: 0;">* Registro de Batalla (Paso a Paso):</h3>
                    <img src="{imagen_towa}" alt="towa" style="max-height: 100px;">
                </div>
                {pasos_html}
            </div>

            <br><br>
            
            <div>
                <img src="{imagen_sangui}" alt="Sangui" style="max-height: 200px;">
                <div style="border: 4px solid white; padding: 20px; margin: 20px auto; width: 60%; text-align: left; font-size: 1.5em; background-color: black;">
                    * Saber que tu determinante es {resultado_redondeado} te llena de determinación.
                </div>
            </div>

            <br>
            <a href='/undertale' style="color: white; background: black; text-decoration: none; border: 2px solid white; padding: 15px; margin: 10px; font-weight: bold;">VOLVER AL CAMPO DE BATALLA</a>
            <a href='/menu' style="color: white; background: black; text-decoration: none; border: 2px solid white; padding: 15px; margin: 10px; font-weight: bold;">VOLVER AL MENÚ</a>
        </body>
        """
    except Exception as e:
        return f"<body style='background-color: black; color: white; font-family: Courier New;'><h2 style='color:red;'>* Tu ataque falló: {str(e)}</h2><br><a href='/undertale' style='color: white; border: 2px solid white; padding: 10px; text-decoration: none;'>INTENTAR DE NUEVO</a></body>"

if __name__ == '__main__':
    app.run(debug=True)