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
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-image: url("/static/staticfondo_oporto.jpg");
            background-size: cover;
            background-position: center;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .search-container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 30px 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 400px;
        }

        .search-container h1 {
            margin-bottom: 20px;
            font-size: 22px;
            color: #333;
        }

        .search-container input[type="text"] {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 6px;
            margin-bottom: 15px;
        }

        .search-container button {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .search-container button:hover {
            background-color: #218838;
        }

        .icon {
            font-size: 18px;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="search-container">
        <h1><span class="icon">🔍</span>Buscar tu Postal</h1>
        <form method="GET" action="/ver_imagen">
            <input type="text" name="codigo" placeholder="Ej: 7fb1d2ae" required>
            <button type="submit">Buscar</button>
        </form>
    </div>
</body>
</html>

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
