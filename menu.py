# menu.py
"""Módulo del menú principal."""
import random
from flask import Blueprint, render_template

bp_menu = Blueprint('menu', __name__)


@bp_menu.route('/')
def menu():
    imagen_banner = random.choice(['ban.png', 'banalt.png'])
    return render_template('menu.html', imagen_banner=imagen_banner)