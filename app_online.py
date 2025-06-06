import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# Carpetas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

# Página principal
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
            * { box-sizing: border-box; }
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
            input[type="text"] {
                width: 100%;
                padding: 12px;
                margin-bottom: 15px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 18px;
            }
            button {
                padding: 12px 24px;
                font-size: 18px;
                background-color: #000;
                color: white;
                border: none;
                border-radius: 6px;
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
    return f"""
    <html>
    <head>
        <title>Postcard {codigo}</title>
        <style>
            body {{
                font-family: Arial;
                background: #f0f0f0;
                margin: 0;
                padding: 20px;
                text-align: center;
            }}
            .grid {{
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 30px;
                margin-top: 20px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                width: 280px;
            }}
            .card img {{
                width: 100%;
                border-radius: 8px;
            }}
            .price {{
                margin: 10px 0;
                font-size: 18px;
                font-weight: bold;
            }}
            .stripe {{
                background-color: #6772e5;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                width: 100%;
                margin-bottom: 8px;
            }}
            .paypal {{
                background-color: #ffc439;
                color: #111;
                border: none;
                padding: 10px;
                border-radius: 6px;
                width: 100%;
            }}
            .back {{
                display: inline-block;
                margin-top: 30px;
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h2>🖼️ Your Photo & Postcard</h2>
        <div class="grid">
            <div class="card">
                <img src="{ruta_img}" alt="Original">
                <div class="price">€4.99</div>
                <button class="stripe">Pay with Stripe</button>
                <button class="paypal">Pay with PayPal</button>
            </div>
            <div class="card">
                <img src="{ruta_postal}" alt="Postcard">
                <div class="price">€3.50</div>
                <button class="stripe">Pay with Stripe</button>
                <button class="paypal">Pay with PayPal</button>
            </div>
        </div>
        <a href="/" class="back">⬅ Back</a>
    </body>
    </html>
    """

def insertar_foto_en_postal(codigo):
    try:
        path_foto = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
        path_postal = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
        marco_path = os.path.join(BASE, "static", "plantilla_postal.jpg")
        base = Image.open(marco_path).convert("RGB")
        foto = Image.open(path_foto).convert("RGB").resize((430, 330))
        base.paste(foto, (90, 95))
        base.save(path_postal)
        return True
    except Exception as e:
        print(f"Error generando postal: {e}")
        return False

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
    archivo = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(archivo)
    insertar_foto_en_postal(codigo)
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "✅ Imagen subida correctamente", 200

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
