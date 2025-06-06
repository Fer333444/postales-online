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
                overflow: hidden;
                font-family: Arial, sans-serif;
            }

            #bg-video {
                position: fixed;
                top: 0;
                left: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }

            .contenedor {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: rgba(255, 255, 255, 0.92);
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                text-align: center;
                width: 90%;
                max-width: 400px;
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
                transition: background-color 0.3s ease;
            }

            button:hover {
                background-color: #218838;
            }

            @media (max-width: 500px) {
                h1 {
                    font-size: 20px;
                }
                button, input[type="text"] {
                    font-size: 16px;
                }
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id="bg-video">
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
    imagen_path = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    postal_path = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")

    if not os.path.exists(imagen_path):
        return f"<h2>❌ La imagen para el código {codigo} no existe.</h2><a href='/'>Volver</a>"

    if not os.path.exists(postal_path):
        if not insertar_foto_en_postal(codigo):
            return f"<h2>❌ No se pudo generar la postal para {codigo}.</h2><a href='/'>Volver</a>"

    return f"""
    <html>
    <head>
        <title>Postal {codigo}</title>
        <style>
            body {{
                background: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                margin: 0;
                height: 100vh;
            }}
            img {{
                max-width: 90vw;
                max-height: 80vh;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            .boton {{
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <img src="/galeria/cliente123/postal_{codigo}.jpg" alt="postal">
        <a href="/" class="boton">⬅️ Volver</a>
    </body>
    </html>
    """

def insertar_foto_en_postal(codigo):
    try:
        origen = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
        fondo = os.path.join(BASE, "static", "plantilla_postal.jpg")
        destino = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")

        base = Image.open(fondo).convert("RGB")
        imagen = Image.open(origen).convert("RGB")
        imagen = imagen.resize((320, 260))
        base.paste(imagen, (70, 90))
        base.save(destino)
        return True
    except Exception as e:
        print(f"Error generando postal {codigo}: {e}")
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

    imagen.save(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg"))

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Imagen subida correctamente", 200

@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
