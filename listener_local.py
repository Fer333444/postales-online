import os
import time
import requests
from PIL import Image
from io import BytesIO

print("📡 Listener activo – usando reportlab para impresión en grises reales")

CARPETA_FOTOS = "fotos_nuevas"
URL_SERVIDOR = "https://postales-online.onrender.com/subir_postal"
PROCESADAS = set()

while True:
    archivos = [f for f in os.listdir(CARPETA_FOTOS) if f.endswith(".jpg")]
    nuevos = [f for f in archivos if f not in PROCESADAS]

    for nombre in nuevos:
        path = os.path.join(CARPETA_FOTOS, nombre)
        try:
            with open(path, "rb") as f:
                imagen = f.read()

            timestamp = nombre.split(" ")[-1].replace(".jpg", "")
            codigo = timestamp[-8:]  # genera código único
            archivos_post = {"imagen": (nombre, BytesIO(imagen), "image/jpeg")}
            data = {"codigo": codigo}

            response = requests.post(URL_SERVIDOR, files=archivos_post, data=data)

            if response.status_code == 200:
                print(f"✅ Subida exitosa ({codigo})")
            else:
                print(f"❌ Error al subir Imagen de WhatsApp {nombre}: {response.status_code}")
                print("🔍 Respuesta del servidor:")
                print(response.text)

        except Exception as e:
            print(f"⚠️ Error general: {e}")

        PROCESADAS.add(nombre)

    time.sleep(2)
