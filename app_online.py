import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# 📁 Configuración de rutas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

# 🏠 Página principal
@app.route('/')
def index():
    return render_template_string("""
    <html>
    <head>
        <title>Postcard Finder</title>
        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: #fff;
                margin: 0;
                padding: 0;
            }
            video#bg {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                object-fit: cover;
                z-index: -1;
            }
            .formulario {
                background: rgba(255,255,255,0.8);
                margin-top: 20vh;
                padding: 30px;
                display: inline-block;
                border-radius: 10px;
            }
            input, button {
                padding: 12px;
                font-size: 16px;
                border-radius: 6px;
                border: none;
            }
            a {
                display: block;
                margin-top: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <video id="bg" autoplay loop muted>
            <source src="/static/douro_sunset.mp4" type="video/mp4" />
        </video>
        <div class="formulario">
            <h2>🔍 Search Your Postcard</h2>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="Enter code" required />
                <button type="submit">Search</button>
            </form>
            <a href="/shop">🛍️ Visit Shop</a>
        </div>
    </body>
    </html>
    """)

# 🔍 Redirección al visualizador
@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

# 🖼️ Visualización de postal
@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    ruta_postal = f"/galeria/cliente123/postal_{codigo}.jpg"
    existe_img = os.path.exists(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg"))
    existe_postal = os.path.exists(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))

    if not existe_img:
        return f"<h2>❌ Original photo not found.</h2><a href='/'>← Back</a>"
    if not existe_postal:
        return f"<h2>❌ Postcard not generated yet.</h2><a href='/'>← Back</a>"

    return render_template_string("""
    <html>
    <head>
        <title>Postcard {{codigo}}</title>
        <style>
            body { font-family: Arial; background: #f9f9f9; margin: 0; padding: 20px; }
            h2 { text-align: center; }
            .grid { display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; }
            .product {
                background: white;
                border-radius: 10px;
                padding: 20px;
                width: 240px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .product img { width: 100%; border-radius: 8px; }
            .cart {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.3);
            }
            button { padding: 8px 12px; background: black; color: white; border: none; border-radius: 6px; margin-top: 10px; width: 100%; }
            select, input { padding: 6px; width: 100%; margin-top: 5px; }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({name, qty, size});
                updateCart();
            }

            function updateCart() {
                const div = document.getElementById("cart");
                if (!div) return;
                let html = "<b>Your Cart</b><ul>";
                cart.forEach(p => {
                    html += `<li>${p.qty} × ${p.name} (${p.size})</li>`;
                });
                html += "</ul><button style='background:#5865F2'>Stripe</button> <button style='background:#FFCC00'>PayPal</button>";
                div.innerHTML = html;
            }
        </script>
    </head>
    <body>
        <h2>📸 Your Postcard & Original</h2>
        <div class="grid">
            <div class="product">
                <img src="{{ruta_img}}" />
                <p><b>Original Photo</b></p>
                <input id="qty1" value="1" />
                <button onclick="addToCart('Original Photo', qty1.value, '-')">Add to Cart</button>
            </div>
            <div class="product">
                <img src="{{ruta_postal}}" />
                <p><b>Postcard</b></p>
                <input id="qty2" value="1" />
                <button onclick="addToCart('Postcard', qty2.value, '-')">Add to Cart</button>
            </div>
        </div>
        <h2>👕 T-Shirts by Category</h2>
        <div class="grid">
            {% for group in ['Men','Women','Kids'] %}
                {% for color in ['White','Black'] %}
                <div class="product">
                    <img src="/static/{{color.lower()}}_shirt.jpg" />
                    <p><b>{{color}} T-Shirt ({{group}})</b></p>
                    <select id="s_{{group}}{{color}}">{% for t in ['XS','S','M','L','XL'] %}<option>{{t}}</option>{% endfor %}</select>
                    <input id="q_{{group}}{{color}}" value="1" />
                    <button onclick="addToCart('{{color}} T-Shirt - {{group}}', q_{{group}}{{color}}.value, s_{{group}}{{color}}.value)">Add to Cart</button>
                </div>
                {% endfor %}
            {% endfor %}
        </div>
        <div id="cart" class="cart">🛒 Cart empty</div>
    </body>
    </html>
    """, codigo=codigo, ruta_img=ruta_img, ruta_postal=ruta_postal)

# 🔄 Nuevas postales
@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        return jsonify({"codigo": cola_postales[0]})
    return jsonify({"codigo": None})

# 📤 Subir imagen
@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "Faltan datos", 400
    ruta = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta)
    insertar_foto_en_postal(codigo)
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "OK", 200

# 🖨️ Generar postal
def insertar_foto_en_postal(codigo):
    try:
        base = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        base.save(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))
    except Exception as e:
        print("❌ Error postal:", e)

# 🖼️ Servir imágenes
@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

# 🚀 Lanzar servidor
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)