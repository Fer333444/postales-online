import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# Rutas de carpetas
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
        <title>Post Card</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                height: 100%;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }
            video.bg-video {
                position: fixed;
                top: 0;
                left: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .search-container {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: rgba(255, 255, 255, 0.4);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            }
            h1 {
                margin: 0 0 15px 0;
                font-size: 24px;
                color: #000;
            }
            input[type="text"] {
                padding: 12px;
                width: 250px;
                border: none;
                border-radius: 5px 0 0 5px;
                font-size: 16px;
            }
            button {
                padding: 12px 20px;
                background-color: #000;
                color: white;
                border: none;
                border-radius: 0 5px 5px 0;
                font-size: 16px;
                cursor: pointer;
            }
            .title-tag {
                position: absolute;
                top: 15px;
                left: 20px;
                background: rgba(0, 0, 0, 0.5);
                color: white;
                padding: 6px 16px;
                font-size: 20px;
                font-weight: bold;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <video autoplay loop muted class="bg-video">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
        </video>
        <div class="title-tag">Post Card</div>
        <div class="search-container">
            <h1>🔍 Search your Postcard</h1>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="e.g. 7fb1d2ae" required>
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
    html = f"""
    <html>
    <head>
        <title>Postcard {codigo}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 30px;
                background-color: #f7f7f7;
                text-align: center;
            }}
            .grid {{
                display: flex;
                justify-content: center;
                gap: 40px;
                margin-top: 30px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                width: 300px;
            }}
            .card img {{
                width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            .card h3 {{
                margin: 10px 0 15px 0;
            }}
            .actions {{
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .actions button {{
                padding: 10px;
                background-color: black;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }}
            .back {{
                margin-top: 30px;
                display: inline-block;
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 6px;
            }}
        </style>
    </head>
    <body>
        <h2>Original Photo & Postcard</h2>
        <div class="grid">
            <div class="card">
                <img src="{original}" alt="original">
                <div class="actions">
                    <button>Buy Print</button>
                    <button>Download JPG</button>
                </div>
            </div>
            <div class="card">
                <img src="{postal}" alt="postcard">
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
    return html

@app.route('/new_postcards')
def new_postcards():
    if cola_postales:
        codigo = cola_postales[0]  # 🟢 Ya no se elimina
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

@app.route('/upload_postcard', methods=['POST'])
def upload_postcard():
    codigo = request.form.get('codigo')
    imagen = request.files.get('imagen')

    if not codigo or not imagen:
        return "❌ Missing code or image", 400

    img_name = f"image_{codigo}.jpg"
    save_path = os.path.join(CARPETA_CLIENTE, img_name)
    imagen.save(save_path)

    generar_postal(codigo)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Image uploaded successfully", 200

@app.route('/gallery/cliente123/<archivo>')
def serve_image(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def generar_postal(codigo):
    try:
        original = Image.open(os.path.join(CARPETA_CLIENTE, f"image_{codigo}.jpg")).convert("RGB")
        marco = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        marco = marco.copy()
        original = original.resize((430, 330))
        marco.paste(original, (90, 95))
        salida = os.path.join(CARPETA_CLIENTE, f"postcard_{codigo}.jpg")
        marco.save(salida)
    except Exception as e:
        print(f"Error creating postcard for {codigo}: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
