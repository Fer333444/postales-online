import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# Rutas
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
        <title>Post Card</title>
        <style>
            html, body {
                margin: 0;
                padding: 0;
                height: 100%;
                font-family: Arial, sans-serif;
                overflow: hidden;
            }
            video {
                position: fixed;
                top: 0;
                left: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .overlay {
                position: absolute;
                top: 15px;
                left: 20px;
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: rgba(0, 0, 0, 0.5);
                padding: 10px 20px;
                border-radius: 8px;
            }
            .center-box {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(255,255,255,0.4);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
            }
            h1 {
                margin-bottom: 20px;
            }
            input[type="text"] {
                padding: 12px;
                width: 250px;
                font-size: 16px;
                border-radius: 6px 0 0 6px;
                border: none;
            }
            button {
                padding: 12px 24px;
                background: black;
                color: white;
                border: none;
                font-size: 16px;
                border-radius: 0 6px 6px 0;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <video autoplay loop muted>
            <source src="/static/douro_sunset.mp4" type="video/mp4" />
        </video>
        <div class="overlay">Post Card</div>
        <div class="center-box">
            <h1>🔍 Search your Postcard</h1>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="e.g. 7fb1d2ae" required />
                <button type="submit">Search</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/search')
def search():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def view_image(codigo):
    original = f"/gallery/cliente123/image_{codigo}.jpg"
    postal = f"/gallery/cliente123/postcard_{codigo}.jpg"
    return f"""
    <html>
    <head>
        <title>Postcard {codigo}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 40px;
                background-color: #f0f0f0;
                text-align: center;
            }}
            .grid {{
                display: flex;
                justify-content: center;
                gap: 30px;
            }}
            .item {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            img {{
                max-width: 300px;
                border-radius: 6px;
            }}
            .actions {{
                margin-top: 10px;
            }}
            button {{
                padding: 10px;
                background: black;
                color: white;
                border: none;
                margin: 5px;
                border-radius: 5px;
                cursor: pointer;
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
        <h2>Original Photo & Postcard</h2>
        <div class="grid">
            <div class="item">
                <img src="{original}" alt="Original Photo" />
                <div class="actions">
                    <button>Buy Print</button>
                    <button>Download JPG</button>
                </div>
            </div>
            <div class="item">
                <img src="{postal}" alt="Postcard" />
                <div class="actions">
                    <button>Buy Postcard</button>
                    <button>Send by Mail</button>
                </div>
            </div>
        </div>
        <a class="back" href="/">⬅ Go Back</a>
    </body>
    </html>
    """

@app.route('/new_postcards')
def new_postcards():
    if cola_postales:
        return jsonify({"codigo": cola_postales[0]})
    return jsonify({"codigo": None})

@app.route('/upload_postcard', methods=['POST'])
def upload_postcard():
    codigo = request.form.get('codigo')
    imagen = request.files.get('imagen')

    if not codigo or not imagen:
        return "❌ Missing code or image", 400

    ruta_imagen = os.path.join(CARPETA_CLIENTE, f"image_{codigo}.jpg")
    imagen.save(ruta_imagen)

    generar_postal(codigo)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Image uploaded successfully", 200

@app.route('/gallery/cliente123/<archivo>')
def serve_image(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def generar_postal(codigo):
    try:
        imagen = Image.open(os.path.join(CARPETA_CLIENTE, f"image_{codigo}.jpg")).convert("RGB")
        marco = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        imagen = imagen.resize((430, 330))
        marco.paste(imagen, (90, 95))
        salida = os.path.join(CARPETA_CLIENTE, f"postcard_{codigo}.jpg")
        marco.save(salida)
    except Exception as e:
        print(f"❌ Error generating postcard: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
