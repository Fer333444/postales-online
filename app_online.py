# app_online.py completo con Cloudinary, simulación de pago, carrito visual e impresión automática local

import os
import subprocess
import json
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string, send_file
from PIL import Image
from fpdf import FPDF
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")

os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

urls_cloudinary = {}
if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

SUMATRA = os.path.join(BASE, "SumatraPDF.exe")
MODELOS_CAMISETAS = ["camiseta_blanca", "camiseta_negra"]

@app.route('/')
def index():
    return render_template_string("""
    <h2>Subir postal</h2>
    <form action="/subir_postal" method="post" enctype="multipart/form-data">
        Código: <input type="text" name="codigo" required><br><br>
        Imagen: <input type="file" name="imagen" accept="image/*" required><br><br>
        <button type="submit">Subir</button>
    </form>
    """)

def imprimir_postal(path_pdf):
    try:
        if os.path.exists(SUMATRA):
            subprocess.run([SUMATRA, '-print-to-default', '-silent', path_pdf])
            print("🖨️ Impresión enviada con SumatraPDF")
        else:
            print("⚠️ SumatraPDF.exe no encontrado")
    except Exception as e:
        print("❌ Error imprimiendo:", e)

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
        return salida, ruta_pdf
    except Exception as e:
        print(f"❌ Error generando postal: {e}")
        return None, None

def generar_previews(codigo):
    urls = {}
    try:
        path_foto = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
        foto = Image.open(path_foto).resize((200, 200)).convert("RGBA")

        for modelo in MODELOS_CAMISETAS:
            path_plantilla = os.path.join(BASE, "static", "plantillas_camiseta", f"{modelo}.png")
            if os.path.exists(path_plantilla):
                base = Image.open(path_plantilla).convert("RGBA")
                base.paste(foto, (150, 250), foto)
                salida = os.path.join(BASE, f"previews_camisetas/{modelo}_{codigo}.png")
                base.save(salida)

                r = cloudinary.uploader.upload(salida)
                urls[modelo] = r['secure_url']

    except Exception as e:
        print("❌ Error generando camisetas:", e)
    return urls

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400

    ruta_img = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta_img)
    ruta_postal, ruta_pdf = insertar_foto_en_postal(codigo)

    try:
        r1 = cloudinary.uploader.upload(ruta_img)
        r2 = cloudinary.uploader.upload(ruta_postal)
        camisetas_urls = generar_previews(codigo)

        urls_cloudinary[codigo] = {
            "imagen": r1['secure_url'],
            "postal": r2['secure_url'],
            "camisetas": camisetas_urls,
            "pdf_local": ruta_pdf
        }

        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

    except Exception as e:
        print("❌ Error subiendo a Cloudinary:", e)

    if ruta_pdf and os.path.exists(ruta_pdf):
        imprimir_postal(ruta_pdf)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    urls = urls_cloudinary.get(codigo, {})
    camisetas_html = ""
    camisetas = urls.get("camisetas", {})
    for modelo, link in camisetas.items():
        camisetas_html += f"""
        <div style='margin:10px;padding:10px;border:1px solid #ccc;width:220px;display:inline-block;'>
            <img src='{link}' width='200'><br>
            <label>Talla:
                <select class='talla'>
                    <option>S</option><option>M</option><option>L</option>
                </select>
            </label><br>
            <label>Cantidad:
                <input type='number' class='cantidad' min='1' value='1'>
            </label><br>
            <button onclick="addToCart('{modelo}', '{link}')">Añadir al carrito</button>
        </div>
        """

    return render_template_string(f"""
    <html><head>
    <script>
    let carrito = JSON.parse(localStorage.getItem('carrito') || '[]');

    function addToCart(modelo, imagen) {{
        const talla = event.target.parentElement.querySelector('.talla').value;
        const cantidad = parseInt(event.target.parentElement.querySelector('.cantidad').value);
        carrito.push({{ modelo, imagen, talla, cantidad }});
        localStorage.setItem('carrito', JSON.stringify(carrito));
        actualizarCarrito();
    }}

    function actualizarCarrito() {{
        const contenedor = document.getElementById('carrito');
        contenedor.innerHTML = '';
        let total = 0;
        carrito.forEach((item, index) => {{
            total += item.cantidad;
            contenedor.innerHTML += `<div style='border-bottom:1px solid #ddd;padding:4px;'>
              <img src='${{item.imagen}}' width='50'>
              ${item.modelo} (${item.talla}) x${item.cantidad}
              <button onclick='eliminarItem(${index})'>❌</button></div>`;
        }});
        document.getElementById('total').innerText = total;
    }}

    function eliminarItem(i) {{
        carrito.splice(i, 1);
        localStorage.setItem('carrito', JSON.stringify(carrito));
        actualizarCarrito();
    }}

    function finalizarCompra() {{
        const total = carrito.reduce((s, i) => s + i.cantidad, 0);
        alert("✅ Pago simulado exitosamente! Total: " + total + " productos.\nGracias por tu compra!");
        carrito = [];
        localStorage.removeItem('carrito');
        actualizarCarrito();
    }}

    function simularPayPal() {{
        alert("💰 Donación simulada a través de PayPal. ¡Gracias por tu apoyo!");
    }}

    window.onload = actualizarCarrito;
    </script>
    </head><body>

    <h2>📸 Tu Postal Generada</h2>
    {'<img src="' + urls.get('imagen', '') + '" width="300">' if urls.get('imagen') else '<p>❌ Imagen no encontrada.</p>'}
    {'<img src="' + urls.get('postal', '') + '" width="300">' if urls.get('postal') else '<p>❌ Postal no generada.</p>'}<br>
    <a href="/descargar_postal/{codigo}">📥 Descargar postal</a> | <a href="/descargar_pdf/{codigo}">📄 Descargar PDF</a>
    <hr>
    <h3>👕 Camisetas personalizadas</h3>
    {camisetas_html if camisetas_html else '<p>❌ No hay camisetas generadas.</p>'}

    <div style='position:fixed;top:20px;right:20px;background:#f9f9f9;border:1px solid #ccc;padding:10px;width:250px;'>
        <h4>🛒 Carrito (<span id='total'>0</span>)</h4>
        <div id='carrito'></div>
        <button onclick="finalizarCompra()">💳 Simular pago</button>
        <button onclick="simularPayPal()">💰 Donar por PayPal</button>
    </div>

    <br><br><a href="/">← Volver</a>
    </body></html>
    """)

@app.route('/descargar_postal/<codigo>')
def descargar_postal(codigo):
    path = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Archivo no encontrado", 404

@app.route('/descargar_pdf/<codigo>')
def descargar_pdf(codigo):
    path = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.pdf")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Archivo no encontrado", 404

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
