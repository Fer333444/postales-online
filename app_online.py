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
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Postcard Finder</title>
        <style>
            body {
                font-family: Arial;
                margin: 0;
                padding: 40px;
                text-align: center;
                background: #fff;
            }
            h2 {
                font-size: 24px;
                margin-bottom: 20px;
            }
            input[type=text] {
                padding: 10px;
                font-size: 16px;
                width: 250px;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <h2>🔍 Search Your Postcard</h2>
        <form action="/search" method="get">
            <input type="text" name="codigo" placeholder="Enter code" required />
            <button type="submit">Search</button>
        </form>
        <br><br>
        <a href="/shop">🛒 Visit Shop</a>
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

    if not os.path.exists(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")):
        return "<h2>❌ Código inválido o postal no generada.</h2><a href='/'>← Back</a>"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Postcard {{codigo}}</title>
        <style>
            body {
                font-family: Arial;
                padding: 30px;
                background: #f9f9f9;
                text-align: center;
            }
            .grid {
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
            }
            .product {
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 15px;
                width: 280px;
            }
            img {
                max-width: 100%;
                border-radius: 6px;
            }
            select, input {
                width: 100%;
                margin-top: 10px;
                padding: 8px;
                font-size: 14px;
            }
            button {
                width: 100%;
                margin-top: 10px;
                padding: 10px;
                font-size: 16px;
                background: black;
                color: white;
                border: none;
                border-radius: 5px;
            }
            .cart {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
            }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size="-") {
                cart.push({ name, qty, size });
                renderCart();
            }

            function renderCart() {
                const div = document.getElementById("cart");
                let html = "<h4>Your Cart</h4><ul>";
                cart.forEach(item => {
                    html += `<li>${item.qty} × ${item.name} ${item.size !== '-' ? '(' + item.size + ')' : ''}</li>`;
                });
                html += "</ul><button style='background:#6366f1'>Stripe</button> <button style='background:#fbbf24'>PayPal</button>";
                div.innerHTML = html;
            }
        </script>
    </head>
    <body>
        <h2>📸 Your Postcard & Original</h2>
        <div class="grid">
            <div class="product">
                <img src="{{ ruta_img }}" alt="Original Photo">
                <p>Original Photo</p>
                <input type="number" id="qty1" value="1" min="1">
                <button onclick="addToCart('Original Photo', document.getElementById('qty1').value)">Add to Cart</button>
            </div>
            <div class="product">
                <img src="{{ ruta_postal }}" alt="Postcard">
                <p>Postcard</p>
                <input type="number" id="qty2" value="1" min="1">
                <button onclick="addToCart('Postcard', document.getElementById('qty2').value)">Add to Cart</button>
            </div>
        </div>
        <h2>👕 T-Shirts by Category</h2>
        {% for group in ['Men', 'Women', 'Boys', 'Girls'] %}
            <h3>{{ group }}</h3>
            <div class="grid">
                {% for color in ['White', 'Black'] %}
                    <div class="product">
                        <img src="/static/{{ color | lower }}_shirt.jpg" alt="{{ color }} T-Shirt">
                        <p>{{ color }} T-Shirt</p>
                        <select id="size_{{ group }}_{{ color }}">
                            {% for s in ['XS','S','M','L','XL'] %}
                                <option value="{{ s }}">{{ s }}</option>
                            {% endfor %}
                        </select>
                        <input type="number" id="qty_{{ group }}_{{ color }}" value="1" min="1">
                        <button onclick="addToCart('{{ color }} T-Shirt ({{ group }})', document.getElementById('qty_{{ group }}_{{ color }}').value, document.getElementById('size_{{ group }}_{{ color }}').value)">Add to Cart</button>
                    </div>
                {% endfor %}
            </div>
        {% endfor %}
        <div class="cart" id="cart"></div>
        <br><a href="/">← Back</a>
    </body>
    </html>
    """, codigo=codigo, ruta_img=ruta_img, ruta_postal=ruta_postal)

@app.route('/shop')
def shop():
    return redirect("/view_image/demo")

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        return jsonify({"codigo": cola_postales.pop(0)})
    return jsonify({"codigo": None})

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400
    ruta = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta)
    insertar_foto_en_postal(codigo)
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
        print("❌ Error generando postal:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
