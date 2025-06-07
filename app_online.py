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
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Postcard Finder</title>
        <style>
            body {
                font-family: Arial;
                background: #f4f4f4;
                text-align: center;
                padding: 40px;
            }
            .search-box {
                background: white;
                padding: 30px;
                border-radius: 10px;
                display: inline-block;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            input, button {
                padding: 10px;
                font-size: 16px;
                margin: 5px;
            }
            a { text-decoration: none; margin-top: 10px; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="search-box">
            <h1>🔍 Search Your Postcard</h1>
            <form action="/search">
                <input type="text" name="codigo" placeholder="Enter code" required>
                <button type="submit">Search</button>
            </form>
            <a href="/shop">🛍️ Visit Shop</a>
        </div>
    </body>
    </html>
    """)

@app.route('/search')
def search():
    codigo = request.args.get("codigo", "")
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def view_image(codigo):
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    ruta_postal = f"/galeria/cliente123/postal_{codigo}.jpg"
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Postcard</title>
        <style>
            body { font-family: Arial; background: #fff; padding: 30px; }
            .grid { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
            .card {
                width: 300px;
                padding: 15px;
                background: #f8f8f8;
                border-radius: 10px;
                box-shadow: 0 0 5px rgba(0,0,0,0.1);
                text-align: center;
            }
            img { width: 100%; border-radius: 8px; }
            .cart { position: fixed; top: 20px; right: 20px; }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({name, qty, size});
                localStorage.setItem("cart", JSON.stringify(cart));
                alert(name + " added to cart.");
            }
        </script>
    </head>
    <body>
        <div class="cart"><a href="/cart">🛒 Cart</a></div>
        <h2>Your Postcard & Original</h2>
        <div class="grid">
            <div class="card">
                <img src="{{ ruta_img }}" alt="Original Photo">
                <p>Original</p>
                <input type="number" id="qty1" value="1" min="1">
                <button onclick="addToCart('Original Photo', document.getElementById('qty1').value, '-')">Add to Cart</button>
            </div>
            <div class="card">
                <img src="{{ ruta_postal }}" alt="Postcard">
                <p>Postcard</p>
                <input type="number" id="qty2" value="1" min="1">
                <button onclick="addToCart('Postcard', document.getElementById('qty2').value, '-')">Add to Cart</button>
            </div>
        </div>
    </body>
    </html>
    """, ruta_img=ruta_img, ruta_postal=ruta_postal)

@app.route('/shop')
def shop():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>T-Shirts</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f0f0f0; }
            .grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
            .product {
                width: 250px;
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            img { width: 100%; }
            select, input, button {
                margin-top: 10px;
                padding: 8px;
                width: 90%;
            }
        </style>
        <script>
            let cart = [];
            function addToCart(name, qty, size) {
                cart.push({name, qty, size});
                localStorage.setItem("cart", JSON.stringify(cart));
                alert(name + " added to cart");
            }
        </script>
    </head>
    <body>
        <h2>🛍️ T-Shirt Collection</h2>
        <div class="grid">
            {% for group in ['Men', 'Women', 'Kids'] %}
                {% for color in ['White', 'Black'] %}
                    <div class="product">
                        <img src="/static/{{ color | lower }}_shirt.jpg">
                        <p>{{ color }} T-Shirt - {{ group }}</p>
                        <label>Size:</label>
                        <select id="size_{{ group }}_{{ color }}">
                            {% for s in ['XS','S','M','L','XL'] %}<option>{{s}}</option>{% endfor %}
                        </select>
                        <input type="number" id="qty_{{ group }}_{{ color }}" value="1" min="1">
                        <button onclick="addToCart('{{ color }} T-Shirt - {{ group }}', document.getElementById('qty_{{ group }}_{{ color }}').value, document.getElementById('size_{{ group }}_{{ color }}').value)">Add to Cart</button>
                    </div>
                {% endfor %}
            {% endfor %}
        </div>
    </body>
    </html>
    """)

@app.route('/cart')
def view_cart():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cart</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f0f0f0; }
            .box {
                background: white;
                padding: 20px;
                border-radius: 10px;
                max-width: 700px;
                margin: auto;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            ul { list-style: none; padding: 0; }
            li { padding: 10px; border-bottom: 1px solid #ddd; }
            button { padding: 10px 20px; margin: 10px; background: black; color: white; border-radius: 5px; }
        </style>
        <script>
            function renderCart() {
                const cart = JSON.parse(localStorage.getItem("cart") || "[]");
                const ul = document.getElementById("items");
                let html = "";
                cart.forEach(item => {
                    html += `<li>${item.qty} × ${item.name} [${item.size}]</li>`;
                });
                ul.innerHTML = html;
            }
            window.onload = renderCart;
        </script>
    </head>
    <body>
        <div class="box">
            <h2>Your Shopping Cart</h2>
            <ul id="items"></ul>
            <div>
                <button>Pay with Stripe</button>
                <button>Pay with PayPal</button>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "Missing data", 400
    path = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(path)
    generar_postal(codigo)
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "Uploaded", 200

@app.route('/galeria/cliente123/<archivo>')
def static_image(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def generar_postal(codigo):
    try:
        fondo = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        fondo.paste(foto, (90, 95))
        fondo.save(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
