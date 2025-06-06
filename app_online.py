import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

# Rutas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

# Cola de códigos
cola_postales = []

# ⬇️ HTML de página principal con buscador y fondo animado
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
            * {
                box-sizing: border-box;
            }
            body, html {
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
                font-family: Georgia, serif;
                background: rgba(0,0,0,0.3);
                padding: 5px 15px;
                border-radius: 8px;
            }
            .contenedor {
                background-color: rgba(255, 255, 255, 0.6);
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                max-width: 400px;
                margin: auto;
                margin-top: 20vh;
                backdrop-filter: blur(8px);
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
                background-color: #000;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }
            button:hover {
                background-color: #444;
            }
            @media (max-width: 600px) {
                .contenedor {
                    width: 90%;
                    margin-top: 10vh;
                }
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
                <input type="text" name="codigo" placeholder="Ex: 7fb1d2ae" pattern="[A-Za-z0-9]{5,}" required>
                <button type="submit">Search</button>
            </form>
        </div>
    </body>
    </html>
    """)

# Redirección a /view_image
@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

# Vista de imagen original + postal
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
                background: white;
                margin: 0;
                padding: 20px;
                text-align: center;
            }}
            img {{
                max-width: 90%;
                max-height: 60vh;
                margin: 10px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
            }}
            .boton {{
                margin-top: 20px;
                background: #007bff;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <h2>Original Photo & Postcard</h2>
        <img src="{ruta_img}" alt="original">
        <img src="{ruta_postal}" alt="postcard">
        <br>
        <a href="/" class="boton">🔙 Go Back</a>
    </body>
    </html>
    """

# Crear postal combinada
def insertar_foto_en_postal(codigo):
    try:
        path_foto = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
        path_postal = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
        marco_path = os.path.join(BASE, "static", "plantilla_postal.jpg")

        base = Image.open(marco_path).convert("RGB")
        foto = Image.open(path_foto).convert("RGB")

        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        base.save(path_postal)
        return True
    except Exception as e:
        print(f"Error generando postal para {codigo}: {e}")
        return False

# Nueva postal disponible
@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        return jsonify({"codigo": cola_postales[0]})
    return jsonify({"codigo": None})

# Subir postal
@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get('codigo')
    imagen = request.files.get('imagen')

    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400

    archivo_nombre = f"imagen_{codigo}.jpg"
    ruta = os.path.join(CARPETA_CLIENTE, archivo_nombre)
    imagen.save(ruta)

    insertar_foto_en_postal(codigo)
    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Imagen subida correctamente", 200

# Servir imagenes
@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

# Lanzamiento Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
