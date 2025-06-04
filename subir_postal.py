import requests

# URL de tu servidor Render
url = "https://postales-online.onrender.com/subir_postal"

# Cambia este nombre por el nombre real de tu imagen
codigo = "49d53e05"
archivo = "descargadas/imagen_49d53e05.jpg"

try:
    with open(archivo, 'rb') as img:
        files = {'imagen': img}
        data = {'codigo': codigo}

        r = requests.post(url, files=files, data=data)

        if r.status_code == 200:
            print(f"✅ Imagen {archivo} subida correctamente con código: {codigo}")
        else:
            print(f"❌ Error al subir: {r.status_code} - {r.text}")

except FileNotFoundError:
    print(f"❌ El archivo '{archivo}' no fue encontrado.")
