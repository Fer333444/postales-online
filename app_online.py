import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# Rutas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

# Cola de postales
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
            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
            }

            #background-video {
                position: fixed;
                top: 0;
                left: 0;
                min-width: 100vw;
                min-height: 100vh;
                width: auto;
                height: auto;
                object-fit: contain;
                z-index: -1;
                background: black;
            }

            .contenedor {
                background-color: rgba(255, 255, 255, 0.92);
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                max-width: 400px;
                width: 90%;
                text-align: center;
                position: relative;
                margin: 10vh auto;
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

            @media (max-width: 768px) {
                .contenedor {
                    margin-top: 40px;
                    border-radius: 0;
                    width: 100%;
                    box-shadow: none;
                }
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id="background-video">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
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
    archivo = f"postal_{codigo}.jpg"
    ruta = os.path.join(CARPETA_CLIENTE, archivo)
    if not os.path.exists(ruta):
        return "❌ Postal no encontrada", 404
    return render_template_string(f"""
    <html>
    <head>
        <title>Postal {codigo}</title>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                background: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-family: Arial, sans-serif;
            }}
            img {{
                max-width: 90vw;
                max-height: 80vh;
                object-fit: contain;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            .boton {{
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <img src="/galeria/cliente123/{archivo}" alt="postal">
        <a href="/" class="boton">⬅️ Volver</a>
    </body>
    </html>
    """)

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        return jsonify({"codigo": cola_postales[0]})
    return jsonify({"codigo": None})

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get('codigo')
    imagen = request.files.get('imagen')

    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400

    ruta_jpg = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta_jpg)

    generar_postal(codigo)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Imagen subida correctamente", 200

def generar_postal(codigo):
    try:
        base = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        base.save(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))
    except Exception as e:
        print(f"Error generando postal para {codigo}: {e}")

@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)