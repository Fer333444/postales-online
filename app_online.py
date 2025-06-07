
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
        <title>Shop</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 20px; background: #f0f0f0; }
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
            .sidebar {
                position: fixed;
                top: 0; right: -400px;
                width: 350px; height: 100%;
                background: white; box-shadow: -3px 0 6px rgba(0,0,0,0.2);
                z-index: 999; overflow-y: auto; padding: 20px;
                transition: right 0.3s ease-in-out;
            }
            .sidebar.active { right: 0; }
            .sidebar-header {
                display: flex; justify-content: space-between; font-weight: bold;
            }
            .cart-button {
                position: fixed;
                top: 20px; right: 20px;
                background: #000; color: white;
                padding: 12px 18px; border: none;
                z-index: 1000;
            }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({ name, qty: parseInt(qty), size });
                renderCart();
            }

            function renderCart() {
                let html = "<h3>🛒 Your Cart</h3><ul>";
                let total = 0;
                cart.forEach(item => {
                    html += `<li>${item.qty} × ${item.name} [${item.size}]</li>`;
                    total += item.qty;
                });
                html += "</ul><p>Total Items: " + total + "</p>";
                html += "<button style='background:#635BFF;'>Pay with Stripe</button> ";
                html += "<button style='background:#FFC439;color:black;'>Pay with PayPal</button>";
                document.getElementById("sidebarContent").innerHTML = html;
            }

            function toggleSidebar() {
                document.getElementById("sidebar").classList.toggle("active");
            }
        </script>
    </head>
    <body>
        <button class="cart-button" onclick="toggleSidebar()">🛒 Cart</button>
        <div id="sidebar" class="sidebar">
            <div class="sidebar-header">
                <span>Your Cart</span>
                <button onclick="toggleSidebar()">✖</button>
            </div>
            <div id="sidebarContent"></div>
        </div>
        <h2>📸 Your Photo & Postcard</h2>
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
    </body>
    </html>
    """, ruta_img=ruta_img, ruta_postal=ruta_postal)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "Faltan datos", 400
    path = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(path)
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
        print("❌ Error:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
