import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# Rutas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

# Cola en memoria
cola_postales = []

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Buscar tu Postal</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                height: 100%;
                font-family: Arial, sans-serif;
                overflow: hidden;
            }
            video.fondo {
                position: fixed;
                top: 0;
                left: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .contenedor {
                position: relative;
                z-index: 1;
                background-color: rgba(255, 255, 255, 0.9);
                max-width: 400px;
                width: 90%;
                padding: 30px;
                margin: 80px auto;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            h1 {
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
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }
            @media (max-width: 600px) {
                .contenedor {
                    margin-top: 40px;
                }
            }
        </style>
    </head>
    <body>
        <video class="fondo" autoplay muted loop playsinline>
            <source src="/static/background.mp4" type="video/mp4">
        </video>

        <div class="contenedor">
            <h1>🔍 Buscar tu Postal</h1>
            <form action="/buscar" method="get">
                <input type="text" name="codigo" placeholder="Ej: 7fb1d2ae" pattern="[A-Za-z0-9]{5,}" required>
                <button type="submit">Buscar</button>
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
    ruta_img = f"/galeria/cliente123/postal_{codigo}.jpg"
    html = f"""
    <html>
    <head>
        <title>Postal {codigo}</title>
        <style>
            body {{
                margin: 0;
                background: white;
                display: flex;
                flex-direction: column;
                align-items: center;
                font-family: Arial;
                height: 100vh;
                justify-content: center;
            }}
            img {{
                max-width: 90vw;
                max-height: 80vh;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
                margin-bottom: 20px;
            }}
            a {{
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <img src="{ruta_img}" alt="postal">
        <a href="/">⬅️ Volver</a>
    </body>
    </html>
    """
    return html

def insertar_foto_en_postal(codigo):
    entrada = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    salida = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
    marco = os.path.join(BASE, "static", "plantilla_postal.jpg")

    try:
        base = Image.open(marco).convert("RGB")
        foto = Image.open(entrada).convert("RGB")
        tamaño = (430, 330)
        posicion = (90, 95)
        foto = foto.resize(tamaño)
        base.paste(foto, posicion)
        base.save(salida)
        return True
    except Exception as e:
        print(f"Error al generar postal: {e}")
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
        return "Faltan datos", 400

    nombre = f"imagen_{codigo}.jpg"
    ruta = os.path.join(CARPETA_CLIENTE, nombre)
    imagen.save(ruta)

    insertar_foto_en_postal(codigo)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Postal subida", 200

@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
