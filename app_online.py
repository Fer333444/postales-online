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
                margin: 0;
                padding: 0;
                height: 100vh;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }
            video#bgVideo {
                position: fixed;
                right: 0;
                bottom: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .title-overlay {
                position: absolute;
                top: 20px;
                left: 20px;
                font-size: 28px;
                color: white;
                background: rgba(0,0,0,0.3);
                padding: 8px 15px;
                border-radius: 8px;
                font-weight: bold;
            }
            .contenedor {
                background: rgba(255, 255, 255, 0.6);
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                max-width: 400px;
                margin: 20vh auto 0;
                backdrop-filter: blur(8px);
            }
            input[type="text"], button {
                padding: 12px;
                font-size: 18px;
                border-radius: 6px;
                border: none;
                margin: 5px;
            }
            button {
                background-color: #000;
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
                <input type="text" name="codigo" placeholder="Ex: 7fb1d2ae" required>
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
        <title>Postcard {{codigo}}</title>
        <style>
            body {
                font-family: Arial;
                background: #f8f9fa;
                margin: 0;
                padding: 40px;
                text-align: center;
            }
            .grid {
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
            }
            .item {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                width: 250px;
            }
            img {
                max-width: 100%;
                border-radius: 6px;
                margin-bottom: 10px;
            }
            .shop-grid {
                margin-top: 40px;
                display: flex;
                flex-direction: column;
                gap: 30px;
            }
            .category h3 {
                text-align: left;
                margin-left: 10px;
            }
            .items {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                justify-content: center;
            }
            .item select, .item button {
                width: 100%;
                padding: 8px;
                margin-top: 8px;
            }
        </style>
    </head>
    <body>
        <h2>🖼️ Your Photo & Postcard</h2>
        <div class="grid">
            <div class="item">
                <img src="{{ ruta_img }}" alt="Original">
                <p><strong>Original Photo</strong></p>
                <button>Buy with Stripe</button>
                <button>Buy with PayPal</button>
            </div>
            <div class="item">
                <img src="{{ ruta_postal }}" alt="Postcard">
                <p><strong>Postcard</strong></p>
                <button>Buy with Stripe</button>
                <button>Buy with PayPal</button>
            </div>
        </div>

        <h2>🛍️ T-Shirt Shop</h2>
        <div class="shop-grid">
        {% for group in ['Men', 'Women', 'Boys', 'Girls'] %}
            <div class="category">
                <h3>{{ group }}</h3>
                <div class="items">
                    {% for color in ['White', 'Black'] %}
                        <div class="item">
                            <img src="/static/{{ color | lower }}_shirt.jpg" alt="{{ color }} Shirt">
                            <p><strong>{{ color }} T-Shirt</strong></p>
                            <label>Size:</label>
                            <select>
                                {% for size in ['XS', 'S', 'M', 'L', 'XL'] %}
                                    <option>{{ size }}</option>
                                {% endfor %}
                            </select>
                            <button>Buy Now</button>
                        </div>
                    {% endfor %}
                </div>
            </div>
        {% endfor %}
        </div>
        <br><a href="/">⬅ Back</a>
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
        print(f"Error generando postal para {codigo}: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
