import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string

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
        <title>Search your Postcard</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                height: 100%;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }
            video#bgvid {
                position: fixed;
                right: 0;
                bottom: 0;
                min-width: 100%;
                min-height: 100%;
                z-index: -1;
                object-fit: cover;
            }
            .overlay {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: rgba(255, 255, 255, 0.5);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                backdrop-filter: blur(8px);
            }
            .overlay h1 {
                margin-bottom: 20px;
                font-size: 24px;
                color: #333;
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
            button:hover {
                background-color: #444;
            }
            .corner-title {
                position: absolute;
                top: 20px;
                left: 20px;
                font-size: 30px;
                font-weight: bold;
                color: white;
                text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.7);
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id="bgvid">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
        </video>
        <div class="corner-title">Post Card</div>
        <div class="overlay">
            <h1>🔍 Search your Postcard</h1>
            <form action="/buscar" method="get">
                <input type="text" name="codigo" placeholder="Ex: 7fb1d2ae" pattern="[A-Za-z0-9]{5,}" required>
                <button type="submit">Search</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/buscar')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/ver_imagen/{codigo}")

@app.route('/ver_imagen/<codigo>')
def ver_imagen(codigo):
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Postcard {codigo}</title>
        <style>
            body {{
                margin: 0;
                background: #fff;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                height: 100vh;
            }}
            img {{
                max-width: 90vw;
                max-height: 80vh;
                object-fit: contain;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            a {{
                text-decoration: none;
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <img src="{ruta_img}" alt="postcard">
        <a href="/">⬅️ Go Back</a>
    </body>
    </html>
    """
    return html

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
        return "❌ Missing code or image", 400

    nombre_archivo = f"imagen_{codigo}.jpg"
    ruta_destino = os.path.join(CARPETA_CLIENTE, nombre_archivo)
    imagen.save(ruta_destino)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Image uploaded successfully", 200

@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
