from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        metodo = request.form.get('metodo')
        txt_matrix = request.form.get('txtMatrix')
        
        # Aquí puedes volver a pegar tu lógica matemática real (numpy, sympy, etc.)
        # Estos son los datos de simulación para que la animación funcione.
        pasos = [
            ("Planteamiento inicial", "Se organiza la matriz con los datos ingresados.", [[1, 2, 3], [4, 5, 6]]),
            ("Resolución mágica", "El hechizo hace su trabajo reduciendo las filas.", [[1, 0, 1], [0, 1, 1]])
        ]
        resultados = [1, 1]
        nombres_vars = ["x", "y"]
        
        return render_template('index.html', metodo=metodo, pasos=pasos, resultados=resultados, nombres_vars=nombres_vars)
    
    return render_template('index.html', metodo='gauss_jordan')

if __name__ == '__main__':
    app.run(debug=True)