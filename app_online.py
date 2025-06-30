import os
import subprocess
import json
import threading
from flask import Flask, request, jsonify, redirect, render_template_string
from PIL import Image, UnidentifiedImageError
from fpdf import FPDF
import cloudinary
import cloudinary.uploader
from io import BytesIO
import time

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
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Buscar postal</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body, html {
                height: 100%;
                font-family: Arial, sans-serif;
            }

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

            h2 {
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id="bg-video">
            <source src='/static/douro_sunset.mp4' type='video/mp4'>
            Tu navegador no soporta videos HTML5.
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

def imprimir_postal_bytes(pdf_bytes, codigo):
    try:
        temp_pdf = os.path.join(BASE, f"temp_{codigo}.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes.read())
        pdf_bytes.seek(0)
        if os.path.exists(SUMATRA):
            subprocess.Popen([SUMATRA, '-print-to-default', '-silent', temp_pdf])
            print("🖨️ Impresión enviada con SumatraPDF")
        else:
            print("⚠️ SumatraPDF.exe no encontrado")
    except Exception as e:
        print("❌ Error imprimiendo:", e)

def generar_postal_bytes(imagen_bytes, codigo):
    try:
        plantilla_path = os.path.join(BASE, "static", "plantilla_postal.jpg")
        if not os.path.exists(plantilla_path):
            raise FileNotFoundError("No se encuentra la plantilla_postal.jpg")

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
        print(f"❌ Imagen inválida o corrupta para código: {codigo}")
        return "❌ Imagen inválida o corrupta", 502

    if len(imagen_bytes) < 100:
        print("❌ Imagen demasiado pequeña o vacía.")
        return "Imagen vacía", 400

    salida_jpg, ruta_pdf = generar_postal_bytes(imagen_bytes, codigo)

    # ✅ Corrección: ahora sí llama a la función que existe
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
        print(f"❌ Cloudinary error real: {str(e)}")
        return f"Subida fallida: {str(e)}", 500

    if codigo not in cola_postales:
        cola_postales.append(codigo)

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
