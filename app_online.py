import os
from flask import Flask, request, send_from_directory, jsonify, redirect

app = Flask(__name__)

# Rutas de carpetas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

# Cola de códigos en memoria
cola_postales = []

# ✅ Página principal con buscador
@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Buscar tu Postal</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-image: url('https://images.unsplash.com/photo-1596398783965-fb78bbf4a458?auto=format&fit=crop&w=1600&q=80'); /* Imagen de Oporto */
                background-size: cover;
                background-position: center;
                font-family: Arial, sans-serif;
            }
            .search-box {
                position: absolute;
                top: 30px;
                right: 40px;
                background: rgba(255, 255, 255, 0.9);
                padding: 20px 25px;
                border-radius: 12px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                text-align: right;
            }
            .search-box h2 {
                margin: 0 0 15px 0;
                font-size: 20px;
                color: #333;
            }
            .search-box input[type="text"] {
                padding: 10px;
                width: 250px;
                border: 1px solid #ccc;
                border-radius: 5px 0 0 5px;
                outline: none;
            }
            .search-box button {
                padding: 10px 18px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 0 5px 5px 0;
                cursor: pointer;
            }
            .search-box button:hover {
                background-color: #218838;
            }
        </style>
    </head>
    <body>
        <div class="search-box">
            <h2>🔍 Buscar tu Postal</h2>
            <form action="/buscar" method="get">
                <input type="text" name="codigo" placeholder="Ej: 7fb1d2ae" required>
                <button type="submit">Buscar</button>
            </form>
        </div>
    </body>
    </html>
    """

# ✅ Buscar postal por código
@app.route('/buscar')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/ver_imagen/{codigo}")

# ✅ Vista de imagen limpia por código
@app.route('/ver_imagen/<codigo>')
def ver_imagen(codigo):
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    html = f"""
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
        <img src="{ruta_img}" alt="postal">
        <a href="/" class="boton">⬅️ Volver</a>
    </body>
    </html>
    """
    return html

# ✅ Ruta para que laptops consulten nuevas postales
@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

# ✅ Subir una nueva postal desde la laptop
@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get('codigo')
    imagen = request.files.get('imagen')

    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400

    nombre_archivo = f"imagen_{codigo}.jpg"
    ruta_destino = os.path.join(CARPETA_CLIENTE, nombre_archivo)
    imagen.save(ruta_destino)

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return "✅ Imagen subida correctamente", 200

# ✅ Servir archivos desde galería
@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

# ✅ Puerto dinámico para Render
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
