# app_online.py actualizado al modo original: solo código, sin subida manual de imagen

import os
import subprocess
import json
from flask import Flask, request, jsonify, redirect, render_template_string
from PIL import Image
from fpdf import FPDF
import cloudinary
import cloudinary.uploader
from io import BytesIO

cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")
SUMATRA = os.path.join(BASE, "SumatraPDF.exe")
cola_postales = []
urls_cloudinary = {}

if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1.0'/>
        <title>Buscar postal</title>
        <style>
            html, body {
                margin: 0; padding: 0;
                height: 100vh;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }
            video#bgVideo {
                position: fixed;
                top: 0; left: 0;
                min-width: 100%; min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .contenedor {
                background-color: rgba(255,255,255,0.85);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                width: 90%;
                max-width: 400px;
                margin: 20vh auto;
            }
            input, button {
                width: 100%;
                padding: 12px;
                font-size: 18px;
                margin-top: 10px;
                border: none;
                border-radius: 6px;
            }
            button {
                background: black;
                color: white;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id='bgVideo'>
            <source src='/static/douro_sunset.mp4' type='video/mp4'>
        </video>
        <div class='contenedor'>
            <h2>🔍 Buscar tu postal</h2>
            <form action='/search' method='get'>
                <input type='text' name='codigo' placeholder='Ej: abc123' required />
                <button type='submit'>Buscar postal</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    data = urls_cloudinary.get(codigo, {})
    return render_template_string(f"""
    <h2>📸 Your Postcard & Original</h2>
    {'<img src="' + data.get('imagen', '') + '" width="300">' if data.get('imagen') else '<p>❌ Original photo not found.</p>'}
    {'<img src="' + data.get('postal', '') + '" width="300">' if data.get('postal') else '<p>❌ Postcard not generated yet.</p>'}<br>
    <a href="/">← Back</a>
    """)

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
