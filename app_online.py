# app_online.py actualizado con validación de imagen antes de subir a Cloudinary

import os
import subprocess
import json
from flask import Flask, request, jsonify, redirect, render_template_string
from PIL import Image, UnidentifiedImageError
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
    <h2>Buscar postal</h2>
    <form action="/search" method="get">
        <input type="text" name="codigo" placeholder="Ej: abc123" required />
        <button type="submit">Buscar postal</button>
    </form>
    """)

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

def imprimir_postal(path_pdf):
    try:
        if os.path.exists(SUMATRA):
            subprocess.run([SUMATRA, '-print-to-default', '-silent', path_pdf])
            print("🖨️ Impresión enviada con SumatraPDF")
        else:
            print("⚠️ SumatraPDF.exe no encontrado")
    except Exception as e:
        print("❌ Error imprimiendo:", e)

def generar_postal_bytes(imagen_bytes, codigo):
    try:
        base = Image.open("static/plantilla_postal.jpg").convert("RGB")
        foto = Image.open(BytesIO(imagen_bytes)).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))

        salida = BytesIO()
        base.save(salida, format='JPEG')
        salida.seek(0)

        pdf_bytes = BytesIO()
        pdf = FPDF(unit="cm", format="A4")
        pdf.add_page()
        temp_jpg = os.path.join(BASE, f"temp_{codigo}.jpg")
        with open(temp_jpg, "wb") as f:
            f.write(salida.read())
        salida.seek(0)
        pdf.image(temp_jpg, x=5, y=5, w=10)
        temp_pdf = os.path.join(BASE, f"temp_{codigo}.pdf")
        pdf.output(temp_pdf)

        return salida, temp_pdf
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

    salida_jpg, ruta_pdf = generar_postal_bytes(imagen_bytes, codigo)

    # ✅ Imprimir en segundo plano mientras sube a Cloudinary
    if ruta_pdf and os.path.exists(ruta_pdf):
        threading.Thread(target=imprimir_postal, args=(ruta_pdf,), daemon=True).start()

    try:
        r1 = cloudinary.uploader.upload(BytesIO(imagen_bytes), public_id=f"postal/{codigo}_original")
        r2 = cloudinary.uploader.upload(salida_jpg, public_id=f"postal/{codigo}_postal")

        urls_cloudinary[codigo] = {
            "imagen": r1['secure_url'],
            "postal": r2['secure_url']
        }

        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

    except Exception as e:
        print("❌ Error subiendo a Cloudinary:", e)
        return "Error en subida", 500

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return redirect(f"/view_image/{codigo}"

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
