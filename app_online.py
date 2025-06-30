import os
import json
import time
import requests
from flask import Flask, request, jsonify, redirect
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)

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
        for plantilla_nombre in os.listdir(plantillas_dir):
            if plantilla_nombre.endswith(".jpg"):
                plantilla_path = os.path.join(plantillas_dir, plantilla_nombre)
                base = Image.open(plantilla_path).convert("RGB")
                foto = Image.open(BytesIO(imagen_bytes)).convert("RGB")
                foto = foto.resize((430, 330))
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
        print("❌ Error generando múltiples postales:", e)

    return salida_urls

def generar_preview_camisetas(imagen_bytes, codigo):
    rutas = []
    base_dir = os.path.join(BASE, "static", "previews")
    os.makedirs(base_dir, exist_ok=True)

    combinaciones = [
        ("hombre", "blanca", "camiseta_hombre_blanca.jpg"),
        ("mujer", "negra", "camiseta_mujer_negra.jpg")
    ]

    for genero, color, plantilla in combinaciones:
        try:
            fondo = Image.open(os.path.join(BASE, "static", plantilla)).convert("RGBA")
            foto = Image.open(BytesIO(imagen_bytes)).resize((220, 220)).convert("RGBA")
            fondo.paste(foto, (95, 120), foto)
            salida_path = os.path.join(base_dir, f"preview_camiseta_{codigo}_{genero}_{color}.png")
            fondo.save(salida_path)
            rutas.append(salida_path)
        except Exception as e:
            print(f"❌ Error generando camiseta {genero}-{color}: {e}")

    return rutas

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    archivo = request.files.get("imagen")

    if not codigo or not archivo:
        return "❌ Código o imagen faltante", 400

    imagen_bytes = archivo.read()

    try:
        test_image = Image.open(BytesIO(imagen_bytes))
        test_image.verify()
    except UnidentifiedImageError:
        return "❌ Imagen inválida o corrupta", 502

    if len(imagen_bytes) < 100:
        return "❌ Imagen vacía", 400

    postales_urls = generar_postales_multiples(imagen_bytes, codigo)
    generar_preview_camisetas(imagen_bytes, codigo)

    timestamp = int(time.time())
    try:
        r1 = cloudinary.uploader.upload(BytesIO(imagen_bytes), public_id=f"postal/{codigo}_{timestamp}_original", overwrite=True)

        urls_cloudinary[codigo] = {
            "imagen": r1['secure_url'],
            "postales": postales_urls
        }

        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

    except Exception as e:
        print(f"❌ Error en subida: {e}")
        return f"Subida fallida: {str(e)}", 500

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    data = urls_cloudinary.get(codigo, {})
    url_compra = "https://www.pattseries.com/products/inclinacion-de-pecho"
    boton = f'<a class="shopify-button" href="{url_compra}" target="_blank">Comprar</a>'

    previews = []
    base_previews = os.path.join(BASE, "static", "previews")
    if os.path.exists(base_previews):
        for file in os.listdir(base_previews):
            if file.startswith(f"preview_camiseta_{codigo}"):
                previews.append(f"/static/previews/{file}")

    postales_path = os.path.join(BASE, "static", "postales_generadas")
    postales_multiples = []
    if os.path.exists(postales_path):
        for file in os.listdir(postales_path):
            if file.startswith(codigo):
                postales_multiples.append(f"/static/postales_generadas/{file}")

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vista de postal y camisetas</title>
        <style>
            body {{ background-color: #111; color: white; text-align: center; font-family: sans-serif; }}
            img {{ max-width: 280px; margin: 10px; cursor: pointer; border: 2px solid white; border-radius: 8px; }}
            .grid {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
            .shopify-button {{
                background-color: #2ecc71; color: white; padding: 10px 20px;
                margin: 5px auto; border: none; border-radius: 5px;
                text-decoration: none; display: inline-block;
            }}
            #modal {{
                display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background-color: rgba(0,0,0,0.8); justify-content: center; align-items: center;
                z-index: 1000;
            }}
            #modal img {{ max-height: 90%; max-width: 90%; }}
        </style>
    </head>
    <body>
        <h2>📸 Tu postal personalizada</h2>
        <div class="grid">
            <div>
                <img src="{data.get('imagen', '')}" onclick="ampliar(this.src)">
                <br>{boton}
            </div>
            {''.join(f'<div><img src="{url}" onclick="ampliar(this.src)"><br>{boton}</div>' for url in postales_multiples)}
            {''.join(f'<div><img src="{preview}" onclick="ampliar(this.src)"><br>{boton}</div>' for preview in previews)}
        </div>
        <div id="modal" onclick="cerrar()">
            <img id="modal-img">
        </div>
        <script>
            function ampliar(src) {{
                document.getElementById("modal-img").src = src;
                document.getElementById("modal").style.display = "flex";
            }}
            function cerrar() {{
                document.getElementById("modal").style.display = "none";
                document.getElementById("modal-img").src = "";
            }}
        </script>
    </body>
    </html>
    '''
    return html
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)