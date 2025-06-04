from flask import Flask, request, redirect, send_from_directory, render_template_string
import os
import hashlib

app = Flask(__name__)

# Rutas base
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
ARCHIVO_CODIGOS = os.path.join(BASE, "codigos_postales.txt")

# HTML con fondo y buscador centrado
HTML_FORM = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Buscar tu Postal</title>
    <style>
        body {{
            margin: 0;
            height: 100vh;
            background: url('/static/staticfondo_oporto.jpg') no-repeat center center fixed;
            background-size: cover;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: sans-serif;
        }}
        .buscador {{
            background: rgba(255, 255, 255, 0.9);
            padding: 25px 40px;
            border-radius: 12px;
            box-shadow: 0 0 12px rgba(0,0,0,0.2);
            text-align: center;
        }}
        input {{
            padding: 10px;
            width: 250px;
            margin-right: 8px;
            border: 1px solid #aaa;
            border-radius: 5px;
        }}
        button {{
            padding: 10px 20px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        button:hover {{
            background: #218838;
        }}
    </style>
</head>
<body>
    <form class="buscador" action="/buscar" method="get">
        <h2>🔍 Buscar tu Postal</h2>
        <input type="text" name="codigo" placeholder="Ej: 7fb1d2ae" required>
        <button type="submit">Buscar</button>
    </form>
</body>
</html>
"""

# Ruta principal
@app.route('/')
def inicio():
    return render_template_string(HTML_FORM)

# Ver PDF directamente
@app.route('/galeria/<cliente>/<archivo>')
def archivo(cliente, archivo):
    return send_from_directory(os.path.join(CARPETA_GALERIAS, cliente), archivo)

# Ver imagen como postal sin código encima
@app.route('/ver_imagen/<codigo>')
def ver_imagen(codigo):
    nombre = f"imagen_{codigo}.jpg"
    ruta = os.path.join(CARPETA_CLIENTE, nombre)
    if os.path.exists(ruta):
        return render_template_string(f"""
        <!DOCTYPE html>
        <html><head><title>Postal {codigo}</title>
        <style>
            body {{
                background: white;
                text-align: center;
                font-family: sans-serif;
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
        </style></head><body>
        <img src="/galeria/cliente123/{nombre}" alt="postal">
        <br><a href="/">⬅ Volver</a>
        </body></html>
        """)
    return "❌ Imagen no encontrada"

# Buscar por código
@app.route('/buscar')
def buscar():
    codigo = request.args.get("codigo", "").replace("#", "").strip()
    with open(ARCHIVO_CODIGOS, "r") as f:
        for linea in f:
            if linea.startswith(codigo):
                _, nombre = linea.strip().split(",")
                return redirect(f"/ver_imagen/{codigo}")
    return "❌ Código no encontrado"

# Ejecutar en modo producción (si necesario)
if __name__ == '__main__':
    app.run(debug=False, port=5000)
