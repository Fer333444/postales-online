import os
import subprocess
import json
import time
import requests
from flask import Flask, request, jsonify, redirect, render_template_string
from PIL import Image, UnidentifiedImageError
from fpdf import FPDF
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
SUMATRA = os.path.join(BASE, "SumatraPDF.exe")
cola_postales = []
urls_cloudinary = {}

if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

def crear_producto_shopify(codigo, imagen_url):
    access_token = os.getenv("SHOPIFY_TOKEN")
    tienda = "corbus"
    url_api = f"https://{tienda}.myshopify.com/admin/api/2023-10/products.json"

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    data = {
        "product": {
            "title": f"Camiseta {codigo}",
            "body_html": "<strong>Camiseta personalizada con tu imagen</strong>",
            "vendor": "PostalesOnline",
            "product_type": "Camisetas",
            "status": "active",
            "published_scope": "global",
            "images": [{"src": imagen_url}],
            "variants": [{
                "price": "24.90",
                "sku": f"camiseta-{codigo}",
                "inventory_management": "shopify",
                "inventory_quantity": 1
            }]
        }
    }

    response = requests.post(url_api, json=data, headers=headers)

    if response.status_code == 201:
        product = response.json()['product']
        variant_id = product['variants'][0]['id']
        enlace = f"https://{tienda}.myshopify.com/cart/{variant_id}:1"
        print("✅ Enlace de compra directa:", enlace)
        return enlace
    else:
        print("❌ Error creando producto:", response.status_code, response.text)
        return None
    else:
        print("❌ Error creando producto:", response.status_code, response.text)
        return None

def imprimir_postal_bytes(pdf_bytes, codigo):
    try:
        temp_pdf = os.path.join(BASE, f"temp_{codigo}.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes.read())
        pdf_bytes.seek(0)
        if os.path.exists(SUMATRA):
            subprocess.Popen([SUMATRA, '-print-to-default', '-silent', temp_pdf])
            print("🖨️ Impresión enviada con SumatraPDF")
    except Exception as e:
        print("❌ Error imprimiendo:", e)

def generar_postal_bytes(imagen_bytes, codigo):
    try:
        plantilla_path = os.path.join(BASE, "static", "plantilla_postal.jpg")
        base = Image.open(plantilla_path).convert("RGB")
        foto = Image.open(BytesIO(imagen_bytes)).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))

        salida = BytesIO()
        base.save(salida, format='JPEG')
        salida.seek(0)

        temp_jpg_path = os.path.join(BASE, f"temp_{codigo}.jpg")
        with open(temp_jpg_path, "wb") as f:
            f.write(salida.read())
        salida.seek(0)

        pdf = FPDF(unit="cm", format="A4")
        pdf.add_page()
        pdf.image(temp_jpg_path, x=5, y=5, w=10)
        temp_pdf_path = os.path.join(BASE, f"temp_{codigo}.pdf")
        pdf.output(temp_pdf_path)

        return salida, temp_pdf_path

    except Exception as e:
        print("❌ Error generando postal:", e)
        return None, None

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

@app.route('/')
def index():
    return render_template_string("""
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
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop playsinline id="bg-video">
            <source src='/static/douro_sunset.mp4' type='video/mp4'>
        </video>
        <div class="contenido">
            <h2>Buscar postal</h2>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="Ej: abc123" required />
                <br>
                <button type="submit">Buscar postal</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

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
        return "Imagen vacía", 400

    salida_jpg, ruta_pdf = generar_postal_bytes(imagen_bytes, codigo)
    generar_preview_camisetas(imagen_bytes, codigo)

    if ruta_pdf and os.path.exists(ruta_pdf):
        with open(ruta_pdf, "rb") as f:
            imprimir_postal_bytes(BytesIO(f.read()), codigo)

    timestamp = int(time.time())
    try:
        r1 = cloudinary.uploader.upload(BytesIO(imagen_bytes), public_id=f"postal/{codigo}_{timestamp}_original", overwrite=True)
        r2 = cloudinary.uploader.upload(salida_jpg, public_id=f"postal/{codigo}_{timestamp}_postal", overwrite=True)

        urls_cloudinary[codigo] = {
            "imagen": r1['secure_url'],
            "postal": r2['secure_url']
        }

        enlace_shopify = crear_producto_shopify(codigo, r2['secure_url'])
        urls_cloudinary[codigo]['shopify'] = enlace_shopify

        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

    except Exception as e:
        return f"Subida fallida: {str(e)}", 500

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    data = urls_cloudinary.get(codigo, {})
    shopify_url = data.get("shopify", "")
    boton = f'<a class="shopify-button" href="{shopify_url}" target="_blank">Comprar</a>' if shopify_url else '<p style="color:gray;">Producto no disponible</p>'

    previews = []
    base_path = os.path.join(BASE, "static", "previews")
    if os.path.exists(base_path):
        for file in os.listdir(base_path):
            if file.startswith(f"preview_camiseta_{codigo}"):
                previews.append(f"/static/previews/{file}")

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
            <div>
                <img src="{data.get('postal', '')}" onclick="ampliar(this.src)">
                <br>{boton}
            </div>
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

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
