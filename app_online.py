import os
from flask import Flask, request, send_from_directory, jsonify

app = Flask(__name__)

# Carpeta base donde se guardarán las postales subidas
BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")

# Crear carpetas si no existen
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

# Cola de impresión en memoria (simple)
cola_postales = []

@app.route('/')
def index():
    return "✅ Sistema Online Activo"

# Ruta para subir una postal desde cada laptop
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

    return "✅ Imagen subida", 200

# Ruta para que las laptops consulten si hay algo nuevo
@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

# Servir postales desde la galería
@app.route('/galeria/cliente123/<archivo>')
def servir_postal(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

# Render lo ejecuta
if __name__ == '__main__':
    app.run(debug=False, port=5000)
