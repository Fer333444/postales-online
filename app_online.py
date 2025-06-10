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
        <title>Search</title>
        <style>
            body { font-family: Arial; text-align: center; background: #f8f8f8; padding-top: 60px; }
            input, button { padding: 12px; font-size: 16px; margin: 5px; }
            a { display: block; margin-top: 20px; color: #000; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>🔍 Search Your Postcard</h2>
        <form action="/search" method="get">
            <input name="codigo" placeholder="Enter code" required>
            <button type="submit">Search</button>
        </form>
        <a href="/shop">🛍️ Visit Shop</a>
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
        <title>Postcard {{codigo}}</title>
        <style>
            body { font-family: Arial; background: #f7f7f7; margin: 0; padding: 20px; }
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
            select, input { margin-top: 8px; padding: 6px; border-radius: 4px; width: 80%; }
            button { margin-top: 8px; padding: 10px 16px; background: black; color: white; border: none; border-radius: 6px; width: 80%; }
            .cart-button {
                position: fixed;
                top: 20px; right: 20px;
                background: black;
                color: white;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
            }
            .cart-panel {
                position: fixed;
                top: 60px; right: 20px;
                background: #fff;
                border: 1px solid #ccc;
                border-radius: 10px;
                width: 300px;
                padding: 20px;
                display: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            .cart-panel.visible { display: block; }
            .pay-buttons button {
                margin: 5px 10px;
                padding: 10px 16px;
                border: none;
                border-radius: 5px;
                color: white;
                font-weight: bold;
            }
            .pay-buttons .stripe { background: #6772e5; }
            .pay-buttons .paypal { background: #ffc439; color: black; }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({ name, qty, size });
                updateCartView();
            }

            function updateCartView() {
                const box = document.getElementById("cartItems");
                box.innerHTML = "";
                cart.forEach(item => {
                    const li = document.createElement("li");
                    li.innerText = `${item.qty} × ${item.name} (${item.size})`;
                    box.appendChild(li);
                });
                document.getElementById("cartPanel").classList.add("visible");
            }

            function toggleCart() {
                document.getElementById("cartPanel").classList.toggle("visible");
            }
        </script>
    </head>
    <body>
        <div class="cart-button" onclick="toggleCart()">🛒 Cart</div>
        <div class="cart-panel" id="cartPanel">
            <h3>Your Cart</h3>
            <ul id="cartItems"></ul>
            <div class="pay-buttons">
                <button class="stripe">Stripe</button>
                <button class="paypal">PayPal</button>
            </div>
        </div>

        <h2>📸 Your Postcard & Original</h2>
        <div class="grid">
            <div class="product">
                <img src="{{ ruta_img }}" alt="Original Photo">
                <p>Original Photo</p>
                <input type="number" id="qty1" value="1" min="1" />
                <button onclick="addToCart('Original Photo', document.getElementById('qty1').value, '-')">Add to Cart</button>
            </div>
            <div class="product">
                <img src="{{ ruta_postal }}" alt="Postcard">
                <p>Postcard</p>
                <input type="number" id="qty2" value="1" min="1" />
                <button onclick="addToCart('Postcard', document.getElementById('qty2').value, '-')">Add to Cart</button>
            </div>
        </div>

        <h2>👕 T-Shirts by Category</h2>
        {% for group in ['Men', 'Women', 'Boys', 'Girls'] %}
            <h3>{{ group }}</h3>
            <div class="grid">
                {% for color in ['White', 'Black'] %}
                    <div class="product">
                        <img src="/static/{{ color | lower }}_shirt.jpg">
                        <p>{{ color }} T-Shirt</p>
                        <select id="size_{{group}}{{color}}">
                            {% for s in ['XS','S','M','L','XL'] %}<option>{{s}}</option>{% endfor %}
                        </select>
                        <input type="number" id="qty_{{group}}{{color}}" value="1" min="1"/>
                        <button onclick="addToCart('{{ color }} T-Shirt - {{ group }}', document.getElementById('qty_{{group}}{{color}}').value, document.getElementById('size_{{group}}{{color}}').value)">Add to Cart</button>
                    </div>
                {% endfor %}
            </div>
        {% endfor %}
        <br><a href="/">← Back</a>
    </body>
    </html>
    """, codigo=codigo, ruta_img=ruta_img, ruta_postal=ruta_postal)

@app.route('/shop')
def shop_redirect():
    return redirect("/view_image/demo")

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        return jsonify({"codigo": cola_postales[0]})
    return jsonify({"codigo": None})

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
        print("❌ Error generando postal:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
