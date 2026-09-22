# app.py
"""Punto de entrada de la aplicación Flask."""
from flask import Flask

from menu import bp_menu
from sistemas import bp_sistemas
from matrices import bp_matrices
from vectores import bp_vectores


def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp_menu)
    app.register_blueprint(bp_sistemas)
    app.register_blueprint(bp_matrices)
    app.register_blueprint(bp_vectores)
    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)