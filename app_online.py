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
from dotenv import load_dotenv

load_dotenv()

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
productos_shopify = {}

if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

def imprimir_postal_bytes(pdf_bytes, codigo):
    try:
        temp_pdf = os.path.join(BASE, f"temp_{codigo}.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes.read())
        pdf_bytes.seek(0)
        if os.path.exists(SUMATRA):
            subprocess.Popen([SUMATRA, '-print-to-default', '-silent', temp_pdf])
            print("📨 Impresión enviada con SumatraPDF")
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
            print(f"❌ Error generando camiseta {genero}-{color}:", e)

    return rutas

def crear_producto_shopify(codigo, ruta_imagen_local):
    access_token = os.getenv("SHOPIFY_TOKEN")
    tienda = "corbus"
    url_api = f"https://{tienda}.myshopify.com/admin/api/2023-10/products.json"

    url_imagen_cloudinary = urls_cloudinary.get(codigo, {}).get("postal", "")

    if not url_imagen_cloudinary:
        print("❌ No se encontró la imagen en Cloudinary para Shopify")
        return None

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
            "images": [{"src": url_imagen_cloudinary}],
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
        handle = response.json()['product']['handle']
        enlace = f"https://{tienda}.myshopify.com/products/{handle}"
        print("✅ Producto creado:", enlace)
        productos_shopify[codigo] = enlace
        return enlace
    else:
        print("❌ Error creando producto:", response.status_code, response.text)
        return None

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

        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

    except Exception as e:
        return f"Subida fallida: {str(e)}", 500

    crear_producto_shopify(codigo, f"static/previews/preview_camiseta_{codigo}_hombre_blanca.png")

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    data = urls_cloudinary.get(codigo, {})
    shopify_url = productos_shopify.get(codigo, "")
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vista de postal y camisetas</title>
        <style>
            body {{ background-color: #111; color: white; text-align: center; font-family: sans-serif; }}
            img {{ max-width: 280px; margin: 10px; cursor: pointer; border: 2px solid white; border-radius: 8px; }}
            .grid {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
            .shopify-button {{ background-color: #2ecc71; color: white; padding: 10px 20px; margin-top: 10px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; }}
        </style>
    </head>
    <body>
        <h2>📸 Tu postal personalizada</h2>
        <div class="grid">
            {"<div><img src='" + data.get("imagen", "") + "'><br><a class='shopify-button' href='" + shopify_url + "' target='_blank'>Comprar</a></div>" if data.get("imagen") else "<p>❌ Sin imagen original.</p>"}
            {"<div><img src='" + data.get("postal", "") + "'><br><a class='shopify-button' href='" + shopify_url + "' target='_blank'>Comprar</a></div>" if data.get("postal") else "<p>❌ Postal no generada.</p>"}
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
