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
    <!DOCTYPE html><html><head>
    <meta charset="UTF-8">
    <title>Postcard Finder</title>
    <style>
        body, html {margin:0;padding:0;height:100vh;overflow:hidden;font-family:Arial}
        video#bg {position:fixed;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:-1}
        .overlay {position:absolute;top:20px;left:20px;color:white;font-size:28px;background:rgba(0,0,0,0.4);padding:8px 12px;border-radius:8px}
        .center {position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,0.6);padding:30px;border-radius:12px;text-align:center}
    </style>
    </head><body>
    <video autoplay muted loop id="bg"><source src="/static/douro_sunset.mp4" type="video/mp4"></video>
    <div class="overlay">Post Card</div>
    <div class="center">
        <h1>🔍 Search your Postcard</h1>
        <form action="/search"><input type="text" name="codigo" placeholder="Ex: 7fb1d2ae" required>
        <button>Search</button></form>
    </div>
    </body></html>
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
            body {font-family:Arial;background:#f0f0f0;padding:20px}
            h2 {text-align:center}
            .grid {display:flex;flex-wrap:wrap;justify-content:center;gap:20px;margin-bottom:30px}
            .product {
                background:white;border-radius:10px;padding:20px;width:240px;text-align:center;
                box-shadow:0 2px 8px rgba(0,0,0,0.1)
            }
            img {max-width:100%;border-radius:8px}
            select, input[type=number], button {
                margin-top:8px;padding:6px;width:80%;border-radius:5px
            }
            .cart-button {
                position:fixed;top:20px;right:20px;background:black;color:white;padding:10px;border-radius:6px;
                cursor:pointer;z-index:999
            }
            #cartPanel {
                display:none;position:fixed;top:60px;right:20px;width:300px;background:white;padding:20px;border-radius:10px;
                box-shadow:0 0 10px rgba(0,0,0,0.3);z-index:999
            }
            #cartPanel h3 {margin-top:0}
            #cartPanel ul {list-style:none;padding:0}
            #cartPanel ul li {margin-bottom:10px}
            .checkout {margin-top:10px;text-align:center}
            .checkout button {margin:5px;width:120px}
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size="-") {
                cart.push({name, qty, size});
                alert(name + " added to cart.");
                updateCartPanel();
            }

            function updateCartPanel() {
                const list = document.getElementById("cartItems");
                list.innerHTML = "";
                cart.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = `${item.qty} × ${item.name} (${item.size})`;
                    list.appendChild(li);
                });
                document.getElementById("cartPanel").style.display = "block";
            }
        </script>
    </head>
    <body>
        <div class="cart-button" onclick="document.getElementById('cartPanel').style.display='block'">🛒 Cart</div>
        <div id="cartPanel">
            <h3>Your Cart</h3>
            <ul id="cartItems"></ul>
            <div class="checkout">
                <button style="background:#6772e5;color:white">Stripe</button>
                <button style="background:#ffc439">PayPal</button>
            </div>
        </div>

        <h2>📸 Your Postcard & Original</h2>
        <div class="grid">
            <div class="product">
                <img src="{{ ruta_img }}" alt="Original Photo" />
                <p>Original Photo</p>
                <input type="number" id="qty1" value="1" min="1" />
                <button onclick="addToCart('Original Photo', document.getElementById('qty1').value)">Add to Cart</button>
            </div>
            <div class="product">
                <img src="{{ ruta_postal }}" alt="Postcard" />
                <p>Postcard</p>
                <input type="number" id="qty2" value="1" min="1" />
                <button onclick="addToCart('Postcard', document.getElementById('qty2').value)">Add to Cart</button>
            </div>
        </div>

        <h2>👕 T-Shirts by Category</h2>
        {% for category in ['Men', 'Women', 'Boys', 'Girls'] %}
        <h3 style="text-align:center">{{ category }}</h3>
        <div class="grid">
            {% for color in ['White', 'Black'] %}
            <div class="product">
                <img src="/static/{{ color | lower }}_shirt.jpg" />
                <p>{{ color }} T-Shirt</p>
                <select id="size_{{category}}_{{color}}">
                    {% for size in ['XS','S','M','L','XL'] %}
                        <option>{{ size }}</option>
                    {% endfor %}
                </select>
                <input type="number" id="qty_{{category}}_{{color}}" value="1" min="1" />
                <button onclick="addToCart('{{ color }} T-Shirt - {{ category }}', document.getElementById('qty_{{category}}_{{color}}').value, document.getElementById('size_{{category}}_{{color}}').value)">Add to Cart</button>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        <br><a href="/">← Back</a>
    </body>
    </html>
    """, codigo=codigo, ruta_img=ruta_img, ruta_postal=ruta_postal)

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
