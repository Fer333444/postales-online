# Archivo: app_online.py

import os
import subprocess
import json
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template
from PIL import Image
from fpdf import FPDF

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

SUMATRA = os.path.join(BASE, "SumatraPDF.exe")

PRODUCTOS = {
    "hombre": [
        {"id": "camiseta_h1", "nombre": "Camiseta Hombre Blanca", "precio": 19.99},
        {"id": "camiseta_h2", "nombre": "Camiseta Hombre Negra", "precio": 21.99}
    ],
    "mujer": [
        {"id": "camiseta_m1", "nombre": "Camiseta Mujer Blanca", "precio": 19.99},
        {"id": "camiseta_m2", "nombre": "Camiseta Mujer Negra", "precio": 21.99}
    ],
    "nino": [
        {"id": "camiseta_n1", "nombre": "Camiseta Niño Blanca", "precio": 15.99},
        {"id": "camiseta_n2", "nombre": "Camiseta Niño Negra", "precio": 17.99}
    ],
    "nina": [
        {"id": "camiseta_nn1", "nombre": "Camiseta Niña Blanca", "precio": 15.99},
        {"id": "camiseta_nn2", "nombre": "Camiseta Niña Negra", "precio": 17.99}
    ]
}

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_postal(codigo):
    imagen_original = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    ruta_postal = f"/galeria/cliente123/postal_{codigo}.jpg"
    imagen_existe = os.path.exists(imagen_original)
    postal_existe = os.path.exists(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))

    previews = {}
    for categoria, items in PRODUCTOS.items():
        previews[categoria] = []
        for item in items:
            preview_path = os.path.join("galeria", "cliente123", f"preview_{item["id"]}_{codigo}.jpg")
            preview_full = os.path.join(CARPETA_CLIENTE, f"preview_{item["id"]}_{codigo}.jpg")
            if not os.path.exists(preview_full):
                try:
                    base = Image.open(os.path.join(BASE, "static", "bases", f"{item["id"]}.jpg"))
                    user_img = Image.open(imagen_original).resize((250, 250))
                    base.paste(user_img, (100, 100))
                    base.save(preview_full)
                except:
                    continue
            previews[categoria].append({"id": item["id"], "nombre": item["nombre"], "precio": item["precio"], "imagen": preview_path})

    return render_template("plantilla_postal_tienda.html", codigo=codigo, previews=previews, ruta_img=ruta_img, ruta_postal=ruta_postal, imagen_existe=imagen_existe, postal_existe=postal_existe)

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

    try:
        camiseta_base = os.path.join(BASE, "static", "camiseta_hombre_blanca.jpg")
        salida_mockup = os.path.join(CARPETA_CLIENTE, f"preview_camiseta_{codigo}.jpg")
        postal_original = ruta_img

        if os.path.exists(camiseta_base) and os.path.exists(postal_original):
            camiseta = Image.open(camiseta_base).convert("RGBA")
            postal = Image.open(postal_original).convert("RGBA")
            postal = postal.resize((200, 200))
            offset = ((camiseta.width - postal.width) // 2, 300)
            camiseta.paste(postal, offset, postal)
            camiseta.convert("RGB").save(salida_mockup)
    except Exception as e:
        print(f"❌ Error generando preview camiseta: {e}")

    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "✅ Imagen subida y maqueta generada", 200

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        return jsonify({"codigo": cola_postales.pop(0)})
    return jsonify({"codigo": None})

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

@app.route('/guardar_pedido', methods=['POST'])
def guardar_pedido():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
    data['fecha'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    archivo = os.path.join(BASE, 'pedidos.json')
    try:
        pedidos = []
        if os.path.exists(archivo):
            with open(archivo, 'r', encoding='utf-8') as f:
                pedidos = json.load(f)
        pedidos.append(data)
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(pedidos, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "ok", "message": "Pedido guardado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

def imprimir_postal(path_pdf):
    try:
        if os.path.exists(SUMATRA):
            subprocess.run([SUMATRA, "-print-to-default", "-silent", path_pdf])
            print("🖨️ Impresión enviada con SumatraPDF")
        else:
            print("⚠️ SumatraPDF no encontrado")
    except Exception as e:
        print("❌ Error imprimiendo:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
