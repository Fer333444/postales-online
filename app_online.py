import os
import subprocess
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image
from fpdf import FPDF

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

SUMATRA = os.path.join(BASE, "SumatraPDF.exe")

def imprimir_postal(path_pdf):
    try:
        if os.path.exists(SUMATRA):
            subprocess.run([SUMATRA, '-print-to-default', '-silent', path_pdf])
    except Exception as e:
        print("❌ Error imprimiendo:", e)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Postcard Search</title>
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
                background-color: rgba(255,255,255,0.8);
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
            <h2>🔍 Search your Postcard</h2>
            <form action='/search' method='get'>
                <input type='text' name='codigo' placeholder='Ex: abc123' required />
                <button type='submit'>Search</button>
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
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    ruta_postal = f"/galeria/cliente123/postal_{codigo}.jpg"
    path_img = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    path_postal = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")

    imagen_existe = os.path.exists(path_img)
    postal_existe = os.path.exists(path_postal)

    return render_template_string(open("plantilla_view_image.html", encoding="utf-8").read(), codigo=codigo, ruta_img=ruta_img, ruta_postal=ruta_postal, imagen_existe=imagen_existe, postal_existe=postal_existe)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400
    ruta_img = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta_img)
    ruta_pdf = insertar_foto_en_postal(codigo)
    if ruta_pdf and os.path.exists(ruta_pdf):
        imprimir_postal(ruta_pdf)
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "✅ Imagen subida correctamente", 200

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def insertar_foto_en_postal(codigo):
    try:
        base = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        salida = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
        base.save(salida)

        pdf = FPDF(unit="cm", format="A4")
        pdf.add_page()
        pdf.image(salida, x=5, y=5, w=10)
        ruta_pdf = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.pdf")
        pdf.output(ruta_pdf)
        return ruta_pdf
    except Exception as e:
        print(f"❌ Error generando postal: {e}")
        return None
from flask import render_template

@app.route('/tienda')
def tienda():
    return render_template("tienda.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
