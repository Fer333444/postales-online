from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for
import os

app = Flask(__name__)

# Configuración de carpetas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_DESCARGADAS = os.path.join(BASE_DIR, "descargadas")
os.makedirs(CARPETA_DESCARGADAS, exist_ok=True)

# HTML incrustado para el buscador
HTML_INDEX = """
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
            <input type="text" name="codigo" placeholder="Ej: 12345" required>
            <br>
            <button type="submit">Buscar</button>
        </form>
    </div>
</body>
</html>
"""

# Página principal con buscador
@app.route("/")
def inicio():
    return render_template_string(HTML_INDEX)

# Página que muestra la postal
@app.route("/ver_imagen")
def ver_imagen():
    codigo = request.args.get("codigo", "").strip().lower()
    if not codigo:
        return redirect(url_for("inicio"))

    archivo = f"imagen_{codigo}.jpg"
    ruta = os.path.join(CARPETA_DESCARGADAS, archivo)
    if os.path.exists(ruta):
        return render_template_string(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Postal {codigo}</title>
            <style>
                body {{
                    background-color: white;
                    text-align: center;
                    font-family: Arial;
                }}
                img {{
                    margin-top: 60px;
                    max-width: 85vw;
                    height: auto;
                    box-shadow: 0 0 12px rgba(0,0,0,0.3);
                }}
                a {{
                    display: inline-block;
                    margin-top: 30px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                }}
            </style>
        </head>
        <body>
            <img src="/descargadas/{archivo}" alt="postal">
            <br><a href="/">⬅ Volver</a>
        </body>
        </html>
        """)
    else:
        return f"❌ No se encontró la postal con código: {codigo}", 404

# Ruta para servir imágenes
@app.route("/descargadas/<filename>")
def descargar_imagen(filename):
    return send_from_directory(CARPETA_DESCARGADAS, filename)

# Mostrar códigos disponibles
@app.route("/nuevas_postales")
def nuevas_postales():
    archivos = [f for f in os.listdir(CARPETA_DESCARGADAS) if f.endswith(".jpg")]
    return {"postales": archivos}

# Ejecutar app
if __name__ == "__main__":
    app.run(debug=True)
