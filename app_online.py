import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string

app = Flask(__name__)

# Rutas de carpetas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

# Cola en memoria
cola_postales = []

# Página principal: buscador con fondo de Oporto
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
            background: url('/static/nuevo_fondo_oporto.jpg') no-repeat center center;
            background-size: cover;
            background-attachment: scroll;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .contenedor {
            background-color: rgba(255, 255, 255, 0.92);
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
        <form action="/buscar" method="get">
            <input type="text" name="codigo" placeholder="Ej: 7fb1d2ae" pattern="[A-Za-z0-9]{5,}" required>
            <button type="submit">Buscar</button>
        </form>
    </div>
</body>
</html>
# Buscar postal redirecciona a /ver_imagen/<codigo>
@app.route('/buscar')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/ver_imagen/{codigo}")

# Vista de postal por código
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

# API: laptop consulta si hay nuevas postales
@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

# API: laptop sube nueva postal
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

# Servir imágenes de cliente
@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

# Render: puerto dinámico
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
