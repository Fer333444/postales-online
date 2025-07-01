import os
import json
import datetime
import time
from flask import Flask, request, jsonify, redirect
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import cloudinary
import cloudinary.uploader
import stripe
import sendgrid
from sendgrid.helpers.mail import Mail

# Configuración
cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")
cola_postales = []
urls_cloudinary = {}

if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

def generar_postales_multiples(imagen_bytes, codigo):
    plantillas_dir = os.path.join(BASE, "static", "plantillas_postal")
    salida_urls = []

    if not os.path.exists(plantillas_dir):
        print("❌ No se encontró la carpeta de plantillas")
        return []

    try:
        # Verifica que la imagen no esté vacía
        if len(imagen_bytes) < 100:
            print("⚠️ Imagen vacía o muy pequeña")
            return []

        foto = None
        try:
            foto = Image.open(BytesIO(imagen_bytes)).convert("RGB")
        except UnidentifiedImageError as e:
            print(f"❌ Imagen no válida: {e}")
            return []

        foto = foto.resize((430, 330))

        for plantilla_nombre in os.listdir(plantillas_dir):
            if plantilla_nombre.endswith(".jpg"):
                plantilla_path = os.path.join(plantillas_dir, plantilla_nombre)

                try:
                    base = Image.open(plantilla_path).convert("RGB")
                    base.paste(foto, (90, 95))

                    salida = BytesIO()
                    base.save(salida, format='JPEG')
                    salida.seek(0)

                    filename = f"{codigo}_{plantilla_nombre}"
                    output_path = os.path.join(BASE, "static", "postales_generadas", filename)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    with open(output_path, "wb") as f:
                        f.write(salida.read())

                    salida_urls.append(f"/static/postales_generadas/{filename}")

                except Exception as e:
                    print(f"❌ Error generando postal con plantilla {plantilla_nombre}: {e}")

    except Exception as e:
        print("❌ Error general generando postales:", e)

    return salida_urls
@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    data = urls_cloudinary.get(codigo)
    if not data:
        return f'''
        <h2>❌ Código <code>{codigo}</code> no encontrado</h2>
        <p><a href="/">Volver al inicio</a></p>
        ''', 404

    postales_path = os.path.join(BASE, "static", "postales_generadas")
    postales_multiples = []
    if os.path.exists(postales_path):
        for file in os.listdir(postales_path):
            if file.startswith(codigo):
                postales_multiples.append(file)

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tu postal personalizada</title>
        <style>
            body {{
                background-color: #111;
                color: white;
                text-align: center;
                font-family: sans-serif;
            }}
            .grid {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                margin-bottom: 40px;
            }}
            img {{
                max-width: 280px;
                border: 2px solid white;
                border-radius: 8px;
            }}
            label {{
                display: block;
                margin-top: 10px;
            }}
            .shopify-button {{
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                margin: 10px 0;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
            }}
            input[type="email"], select {{
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h2>📸 Tu postal personalizada</h2>
        <form action="/checkout_multiple" method="POST">
            <input type="hidden" name="codigo" value="{codigo}">
            <div class="grid">
                {''.join(f'<div><img src="/static/postales_generadas/{file}"><br><label><input type="checkbox" name="postal" value="{file}"> Seleccionar</label></div>' for file in postales_multiples)}
            </div>
            <div>
                <h3>💌 Recibe tus postales seleccionadas por email tras el pago</h3>
                <input type="email" name="email" placeholder="Tu correo electrónico" required><br>
                <button type="submit" class="shopify-button">💳 Pagar y recibir postales</button>
            </div>
        </form>
    </body>
    </html>
    '''
    return html

@app.route('/admin_pedidos')
def admin_pedidos():
    token = request.args.get("token", "")
    if token != "secreto123":
        return "🔒 Acceso no autorizado", 403

    pedidos_file = os.path.join(BASE, "pedidos.json")
    if not os.path.exists(pedidos_file):
        return "No hay pedidos registrados aún."

    with open(pedidos_file) as f:
        pedidos = json.load(f)

    html = "<h2>📦 Pedidos registrados</h2><ul>"
    for p in pedidos:
        productos = ", ".join([prod['nombre'] for prod in p.get("productos", [])])
        html += f"<li><strong>{p['tipo'].capitalize()}</strong> - {p.get('email', p.get('correo', ''))} - {p['fecha']}<br>Productos: {productos}</li><hr>"
    html += "</ul>"
    return html

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Buscar postal</title>
        <style>
            video#bg-video {
                position: fixed;
                right: 0;
                bottom: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
                filter: brightness(0.4);
            }
            .contenido {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                text-align: center;
                background-color: rgba(0, 0, 0, 0.6);
                padding: 40px;
                border-radius: 15px;
            }
            input, button {
                padding: 10px;
                font-size: 16px;
                margin-top: 10px;
                border-radius: 5px;
                border: none;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop playsinline id="bg-video">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
        </video>
        <div class="contenido">
            <h2>🔍 Buscar tu postal</h2>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="Ej: abc123" required />
                <br>
                <button type="submit">Ver postal</button>
            </form>
            <br><a href="/pedido_vino" style="color:white; background:#9b59b6; padding:10px 20px; border-radius:5px; display:inline-block; text-decoration:none;">🍷 Pedir Vinos</a>
        </div>
    </body>
    </html>
    '''
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
