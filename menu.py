# menu.py
"""Módulo del menú principal."""
import random
from flask import Blueprint, render_template

bp_menu = Blueprint('menu', __name__)


@bp_menu.route('/')
def menu():
    imagen_banner = random.choice(['ban.png', 'banalt.png', 'banp.png', 'banp1.png', 'banp2.png', 'banp3.png'])
    return render_template('menu.html', imagen_banner=imagen_banner)