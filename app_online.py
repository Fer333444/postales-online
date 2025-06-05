import os
import uuid
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_DESCARGADAS = os.path.join(BASE_DIR, "descargadas")
CARPETA_STATIC = os.path.join(BASE_DIR, "static")
IMAGEN_DEFECTO = "imagen_no_encontrada.jpg"

# Asegurar carpeta de imágenes
os.makedirs(CARPETA_DESCARGADAS, exist_ok=True)
os.makedirs(CARPETA_STATIC, exist_ok=True)

@app.route('/')
def index():
    return render_template_string("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buscar tu Postal</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: url('/static/fondo_rio_douro.jpg') no-repeat center center fixed;
            background-size: cover;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .contenedor {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            max-width: 400px;
            width: 90%;
            text-align: center;
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
    <div class="contenedor">
        <h1>🔍 Buscar tu Postal</h1>
        <form action="/ver_imagen" method="get">
            <input type="text" name="codigo" placeholder="Ej: 7fb1d2ae" pattern="[A-Za-z0-9]{5,}" required>
            <br>
            <button type="submit">Buscar</button>
        </form>
    </div>
</body>
</html>""")

@app.route('/ver_imagen/<codigo>')
def ver_imagen(codigo):
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        nombre_archivo = f"imagen_{codigo}{ext}"
        ruta = os.path.join(CARPETA_DESCARGADAS, nombre_archivo)
        if os.path.isfile(ruta):
            return render_template_string(f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Postal {codigo}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f0f0f0;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .contenedor {{
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 20px rgba(0,0,0,0.2);
                        text-align: center;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        border-radius: 8px;
                    }}
                    a {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="contenedor">
                    <img src="/descargadas/{nombre_archivo}" alt="postal">
                    <br>
                    <a href="/">← Volver</a>
                </div>
            </body>
            </html>
            """)
    return "Imagen no encontrada", 404

@app.route('/descargadas/<path:filename>')
def imagenes(filename):
    return send_from_directory(CARPETA_DESCARGADAS, filename)

