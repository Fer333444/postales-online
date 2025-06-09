import os
import time
import requests
import subprocess
from pathlib import Path
from fpdf import FPDF

# CONFIGURACIÓN
URL_SERVIDOR = "https://postales-online.onrender.com"  # ✅ VERIFICA que esté en línea
SUMATRA = "SumatraPDFPortable/SumatraPDF.exe"
CARPETA_DESCARGAS = "descargadas"

Path(CARPETA_DESCARGAS).mkdir(exist_ok=True)

print("🖥️ Listener activo. Consultando servidor...")

postales_procesadas = set()

while True:
    try:
        r = requests.get(f"{URL_SERVIDOR}/nuevas_postales")
        if r.status_code == 200:
            codigo = r.json().get("codigo")
            if codigo and codigo not in postales_procesadas:
                print(f"📥 Nueva postal detectada: {codigo}")

                url_imagen = f"{URL_SERVIDOR}/galeria/cliente123/imagen_{codigo}.jpg"
                archivo_local = os.path.join(CARPETA_DESCARGAS, f"imagen_{codigo}.jpg")

                img = requests.get(url_imagen)
                if img.status_code != 200:
                    print(f"❌ Imagen no disponible todavía: {url_imagen}")
                    time.sleep(5)
                    continue

                with open(archivo_local, "wb") as f:
                    f.write(img.content)

                # Crear PDF para impresión
                pdf_path = os.path.join(CARPETA_DESCARGAS, f"postal_{codigo}.pdf")
                pdf = FPDF(unit="cm", format="A4")
                pdf.add_page()
                pdf.image(archivo_local, x=3.8, y=2.1, w=5.6, h=8.0)
                pdf.output(pdf_path)

                # Imprimir automáticamente con SumatraPDF
                if os.path.exists(SUMATRA):
                    subprocess.run([SUMATRA, "-print-to-default", "-silent", pdf_path])
                    print(f"🖨️ Postal {codigo} enviada a impresión")
                    postales_procesadas.add(codigo)
                else:
                    print("❌ SumatraPDF no encontrado. Verifica la ruta.")
        else:
            print("⚠️ Error consultando el servidor:", r.status_code)
    except Exception as e:
        print("❌ Error en ejecución:", e)
    time.sleep(5)
