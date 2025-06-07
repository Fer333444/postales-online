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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Postcard & Shop</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: #f0f0f0;
            }
            .container {
                padding: 20px;
            }
            .grid {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
            }
            .card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                width: 240px;
                padding: 15px;
                text-align: center;
            }
            img {
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 6px;
            }
            select, input {
                margin-top: 8px;
                padding: 6px;
                font-size: 14px;
            }
            button {
                background: black;
                color: white;
                border: none;
                padding: 10px;
                margin-top: 10px;
                cursor: pointer;
                width: 100%;
                border-radius: 5px;
            }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({ name, qty, size });
                alert(`${qty} x ${name} (${size}) added to cart`);
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h2>👕 T-Shirts by Category</h2>
            {% for group in ['Men', 'Women', 'Kids'] %}
                <h3>{{ group }}</h3>
                <div class="grid">
                    {% for color in ['White', 'Black'] %}
                    <div class="card">
                        <img src="/static/{{ color | lower }}_shirt.jpg" alt="{{ color }} Shirt">
                        <p><strong>{{ color }} T-Shirt</strong></p>
                        <label>Size:</label>
                        <select id="size_{{group}}{{color}}">
                            {% for s in ['XS','S','M','L','XL'] %}<option>{{s}}</option>{% endfor %}
                        </select>
                        <label>Qty:</label>
                        <input type="number" id="qty_{{group}}{{color}}" value="1" min="1"><br>
                        <button onclick="addToCart('{{ color }} T-Shirt - {{ group }}', document.getElementById('qty_{{group}}{{color}}').value, document.getElementById('size_{{group}}{{color}}').value)">
                            Add to Cart
                        </button>
                    </div>
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """)

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
