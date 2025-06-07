import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Postcard Search</title>
        <style>
            html, body {
                margin: 0; padding: 0;
                height: 100vh;
                font-family: Arial, sans-serif;
                overflow: hidden;
            }
            video#bgVideo {
                position: fixed;
                right: 0; bottom: 0;
                min-width: 100%; min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .title-overlay {
                position: absolute;
                top: 20px; left: 20px;
                font-size: 28px;
                background: rgba(0,0,0,0.4);
                color: white;
                padding: 8px 15px;
                border-radius: 8px;
            }
            .contenedor {
                background: rgba(255,255,255,0.6);
                backdrop-filter: blur(5px);
                max-width: 400px;
                margin: 20vh auto;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
            }
            input[type="text"], button {
                width: 100%;
                padding: 12px;
                margin-top: 10px;
                font-size: 18px;
                border-radius: 6px;
                border: none;
            }
            button {
                background: #000;
                color: white;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id="bgVideo">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
        </video>
        <div class="title-overlay">Post Card</div>
        <div class="contenedor">
            <h1>🔍 Search your Postcard</h1>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="Ex: 7fb1d2ae" required />
                <button type="submit">Search</button>
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
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Cart</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; margin: 0; }
            .grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
            .product {
                background: white;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                width: 250px;
                text-align: center;
            }
            img { max-width: 100%; border-radius: 8px; }
            select, input { margin-top: 8px; padding: 6px; border-radius: 4px; }
            button { margin-top: 8px; padding: 8px 16px; background: black; color: white; border: none; border-radius: 6px; }
            #cart { margin-top: 30px; background: #fff; padding: 15px; border-radius: 10px; width: 80%; margin-left: auto; margin-right: auto; }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({ name, qty, size });
                renderCart();
            }

            function renderCart() {
                let html = "<h3>🛒 Your Cart</h3><ul>";
                cart.forEach(item => {
                    html += `<li>${item.qty} × ${item.name} [${item.size}]</li>`;
                });
                html += "</ul><p><button>Pay with Stripe</button> <button>Pay with PayPal</button></p>";
                document.getElementById("cart").innerHTML = html;
            }
        </script>
    </head>
    <body>
        <h2>📸 Your Postcard & Shop</h2>
        <div class="grid">
            <div class="product">
                <img src="{{ ruta_img }}" alt="Photo" />
                <p>Original Photo</p>
                <label>Qty:</label><input type="number" id="qty1" value="1" min="1" /><br>
                <button onclick="addToCart('Original Photo', document.getElementById('qty1').value, '-')">Add to Cart</button>
            </div>
            <div class="product">
                <img src="{{ ruta_postal }}" alt="Postcard" />
                <p>Postcard</p>
                <label>Qty:</label><input type="number" id="qty2" value="1" min="1" /><br>
                <button onclick="addToCart('Postcard', document.getElementById('qty2').value, '-')">Add to Cart</button>
            </div>
        </div>
        <h2>👕 T-Shirts</h2>
        <div class="grid">
            {% for group in ['Men', 'Women', 'Boys', 'Girls'] %}
            <div style="width:100%;text-align:left;"><h3>{{ group }}</h3></div>
                {% for color in ['White', 'Black'] %}
                <div class="product">
                    <img src="/static/{{ color | lower }}_shirt.jpg" />
                    <p>{{ color }} T-Shirt</p>
                    <label>Size:</label>
                    <select id="size_{{group}}{{color}}">
                        {% for s in ['XS','S','M','L','XL'] %}<option>{{s}}</option>{% endfor %}
                    </select>
                    <label>Qty:</label>
                    <input type="number" id="qty_{{group}}{{color}}" value="1" min="1"/><br>
                    <button onclick="addToCart('{{ color }} T-Shirt - {{ group }}', document.getElementById('qty_{{group}}{{color}}').value, document.getElementById('size_{{group}}{{color}}').value)">Add to Cart</button>
                </div>
                {% endfor %}
            {% endfor %}
        </div>
        <div id="cart"></div>
        <br><a href="/">← Go Back</a>
    </body>
    </html>
    """, codigo=codigo, ruta_img=ruta_img, ruta_postal=ruta_postal)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400
    ruta = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta)
    insertar_foto_en_postal(codigo)
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "✅ Imagen subida correctamente", 200

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def insertar_foto_en_postal(codigo):
    try:
        base = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        base.save(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))
    except Exception as e:
        print(f"❌ Error generando postal: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
