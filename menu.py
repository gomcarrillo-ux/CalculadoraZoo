# menu.py
"""Módulo del menú principal."""
from flask import Blueprint, render_template

bp_menu = Blueprint('menu', __name__)


@bp_menu.route('/')
def menu():
    return render_template('menu.html')