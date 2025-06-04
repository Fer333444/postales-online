from flask import Flask, request, render_template, send_from_directory, redirect
import os
import uuid
from PIL import Image
import shutil

app = Flask(__name__)

CARPETA_GALERIAS = "galerias"
CARPETA_DESCARGAS = "descargadas"
os.makedirs(CARPETA_GALERIAS, exist_ok=True)
os.makedirs(CARPETA_DESCARGAS, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ver_imagen/<codigo>')
def ver_imagen(codigo):
    carpeta = os.path.join(CARPETA_GALERIAS, "cliente123")
    nombre_archivo = f"imagen_{codigo}.jpg"
    ruta_imagen = os.path.join(carpeta, nombre_archivo)
    if os.path.exists(ruta_imagen):
        return render_template("ver_imagen.html", codigo=codigo)
    else:
        return "Código no encontrado", 404

@app.route('/galeria/cliente123/<filename>')
def galeria_cliente123(filename):
    carpeta = os.path.join(CARPETA_GALERIAS, "cliente123")
    return send_from_directory(carpeta, filename)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    imagen = request.files['imagen']
    codigo = request.form['codigo']
    nombre_archivo = f"imagen_{codigo}.jpg"

    ruta_cliente = os.path.join(CARPETA_GALERIAS, "cliente123")
    ruta_destino = os.path.join(ruta_cliente, nombre_archivo)
    os.makedirs(ruta_cliente, exist_ok=True)
    imagen.save(ruta_destino)

    # Convertir imagen a blanco y negro automático
    im = Image.open(ruta_destino).convert('L')
    im.save(ruta_destino)

    # Copiar a carpeta descargadas y renombrar
    nueva_ruta = os.path.join(CARPETA_DESCARGAS, f"imagen_{codigo}.jpg")
    shutil.copy(ruta_destino, nueva_ruta)

    return f"Imagen subida correctamente con código: {codigo}"

@app.route('/nuevas_postales')
def nuevas_postales():
    ruta = os.path.join(CARPETA_GALERIAS, "cliente123")
    archivos = os.listdir(ruta)
    codigos = [a.replace("imagen_", "").replace(".jpg", "") for a in archivos if a.endswith(".jpg")]
    return {"codigos": codigos}

if __name__ == '__main__':
    app.run(debug=True)
