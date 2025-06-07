import os
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)

cola_postales = []

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Postcard Shop</title></head>
    <body style="font-family:Arial;text-align:center;padding:50px;">
        <h1>🔍 Search Your Postcard</h1>
        <form action="/search" method="get">
            <input name="codigo" required placeholder="Enter code" style="padding:10px;width:300px;">
            <button type="submit" style="padding:10px 20px;">Search</button>
        </form>
        <br><a href="/shop">🛍️ Visit Shop</a>
    </body></html>
    """)

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    ruta_postal = f"/galeria/cliente123/postal_{codigo}.jpg"
    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Postcard View</title></head>
    <body style="font-family:Arial;text-align:center;padding:40px;">
        <h2>Your Postcard & Original</h2>
        <div style="display:flex;justify-content:center;gap:40px;flex-wrap:wrap;">
            <div><img src="{ruta_img}" width="300"><p>Original</p></div>
            <div><img src="{ruta_postal}" width="300"><p>Postcard</p></div>
        </div>
        <br><a href="/">← Back</a>
    </body></html>
    """)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400

    path_img = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    path_postal = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
    imagen.save(path_img)

    insertar_foto_en_postal(codigo)
    if codigo not in cola_postales:
        cola_postales.append(codigo)

    imprimir_postal(path_postal)
    return "✅ Imagen subida correctamente", 200

@app.route('/shop')
def tienda():
    return render_template_string("""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Shop</title></head>
    <body style="font-family:Arial;padding:30px;">
        <h2>👕 T-Shirts</h2>
        <div style="display:flex;gap:20px;flex-wrap:wrap;">
            {% for color in ['White','Black'] %}
            <div style="border:1px solid #ccc;padding:15px;width:200px;">
                <img src="/static/{{ color | lower }}_shirt.jpg" width="180"><br><br>
                <b>{{ color }} Shirt</b><br>
                <select>{% for s in ['XS','S','M','L','XL'] %}<option>{{s}}</option>{% endfor %}</select><br>
                <input type="number" min="1" value="1" style="width:50px;margin-top:5px;"><br>
                <button style="margin-top:10px;">Add to Cart</button>
            </div>
            {% endfor %}
        </div>
        <br><a href="/">← Back</a>
    </body></html>
    """)

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def insertar_foto_en_postal(codigo):
    try:
        base = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        base.save(os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg"))
    except Exception as e:
        print(f"❌ Error generando postal: {e}")

def imprimir_postal(path_postal):
    try:
        full_path = os.path.abspath(path_postal)
        os.system(f'start /min "" "{full_path}"')
        # o usa SumatraPDF si lo tienes instalado: os.system(f'start /min SumatraPDF.exe -print-to-default "{full_path}"')
    except Exception as e:
        print(f"❌ Error imprimiendo postal: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
