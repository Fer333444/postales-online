
# ✅ Versión mejorada de la app con diseño adaptable (responsive) para móviles y escritorio

import os
import json
import time
import datetime
from flask import Flask, request, redirect, render_template_string
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import cloudinary
import cloudinary.uploader
import stripe

cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")
PEDIDOS_FILE = os.path.join(BASE, "pedidos.json")
urls_cloudinary = {}

os.makedirs(os.path.join(BASE, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE, "static", "postales_generadas"), exist_ok=True)

if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

def guardar_pedido(pedido):
    pedidos = []
    if os.path.exists(PEDIDOS_FILE):
        with open(PEDIDOS_FILE) as f:
            pedidos = json.load(f)
    pedidos.append(pedido)
    with open(PEDIDOS_FILE, "w") as f:
        json.dump(pedidos, f, indent=2)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Buscar postal</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                font-family: sans-serif;
            }
            video#bg-video {
                position: fixed;
                right: 0;
                bottom: 0;
                min-width: 100%;
                min-height: 100%;
                object-fit: cover;
                z-index: -1;
                filter: brightness(0.4);
            }
            .contenido {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                text-align: center;
                background-color: rgba(0, 0, 0, 0.6);
                padding: 40px;
                border-radius: 15px;
                width: 90%;
                max-width: 400px;
            }
            input, button {
                padding: 12px;
                font-size: 18px;
                margin-top: 10px;
                border-radius: 8px;
                border: none;
                width: 100%;
            }
            h2 {
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop playsinline id="bg-video">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
        </video>
        <div class="contenido">
            <h2>🔍 Buscar tu postal</h2>
            <form action="/view_image" method="get">
                <input type="text" name="codigo" placeholder="Ej: abc123" required>
                <button type="submit">Ver postales</button>
            </form>
        </div>
    </body>
    </html>
    '''

# Otras rutas siguen como están. Solo debes asegurarte que en cada respuesta HTML agregues:
# <meta name="viewport" content="width=device-width, initial-scale=1.0">
# y usar unidades relativas (%, vw, vh, em) en lugar de fijas (px) para tamaños y márgenes.

# ¿Deseas que pase todas las demás vistas como /view_image o /admin_pedidos al mismo estilo responsive?

@app.route('/search')
def buscar():
    return """
    <form action='/view_image' method='get'>
        <input name='codigo' placeholder='Código'>
        <button type='submit'>Ver postal</button>
    </form>
    """

@app.route('/view_image')
def view_image():
    codigo = request.args.get("codigo", "").strip()

    postales_path = os.path.join(BASE, "static", "postales_generadas")
    vinos_path = os.path.join(BASE, "static", "Vinos")
    archivos = []
    vinos = []

    if os.path.exists(postales_path):
        archivos = [f for f in os.listdir(postales_path) if f.startswith(codigo)]

    if os.path.exists(vinos_path):
        vinos = [f for f in os.listdir(vinos_path) if f.endswith((".jpg", ".png"))]

   html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Postales y Vinos</title>
    <style>
        body {{
            background-color: #111;
            color: white;
            font-family: sans-serif;
            margin: 0;
            padding: 0;
        }}
        h2, h3 {{
            margin-top: 20px;
        }}
        .grid {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 16px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        .item {{
            background-color: #222;
            padding: 10px;
            border-radius: 10px;
            max-width: 240px;
        }}
        .seccion {{
            background-color: #222;
            padding: 20px;
            border-radius: 10px;
            margin: 16px auto;
            width: 90%;
            max-width: 900px;
        }}
        input, select, button {{
            padding: 10px;
            font-size: 16px;
            margin-top: 10px;
            width: 100%;
            border-radius: 5px;
            border: none;
        }}
        button {{
            background-color: gold;
            color: black;
            font-weight: bold;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <form action="/checkout_combined" method="POST">
        <input type="hidden" name="codigo" value="{codigo}">

        <div class="seccion">
            <h2>📸 Selecciona postales</h2>
            <div class="grid">
"""

# Postales generadas
for img in archivos:
    html += f"""
        <div class="item">
            <img src="/static/postales_generadas/{img}">
            <label><input type="checkbox" name="postal" value="{img}"> Seleccionar</label>
        </div>
    """

# Sección de vinos
html += """
        </div>
    </div>

    <div class="seccion">
        <h2>🍷 Selecciona vinos</h2>
        <div class="grid">
"""

for vino in vinos:
    nombre = vino.replace("_", " ").replace(".jpg", "").replace(".png", "").title()
    html += f"""
        <div class="item">
            <img src="/static/Vinos/{vino}">
            <p><strong>{nombre}</strong></p>
            <label><input type="checkbox" name="vino" value="{vino}"> Añadir</label><br>
            <input type="number" name="cantidad_{vino}" min="0" value="0">
        </div>
    """

# Sección de datos del cliente
html += """
        </div>
    </div>

    <div class="seccion">
        <h2>📋 Datos del cliente</h2>
        <input type="text" name="nombre" placeholder="Nombre completo" required>
        <input type="text" name="direccion" placeholder="Dirección completa" required>
        <input type="text" name="telefono" placeholder="Teléfono" required>
        <input type="email" name="email" placeholder="Correo electrónico" required>
        <button type="submit">💳 Pagar y confirmar pedido</button>
    </div>
</form>
</body>
</html>
"""
@app.route('/subir_postal', methods=['GET', 'POST'])
def subir_postal():
    if request.method == 'GET':
        return """
        <h2>Sube tu foto</h2>
        <form method='POST' enctype='multipart/form-data'>
            Código: <input name='codigo' required><br>
            Imagen: <input type='file' name='imagen' accept='image/*' required><br>
            <button type='submit'>Subir</button>
        </form>
        """

    codigo = request.form.get("codigo")
    archivo = request.files.get("imagen")

    if not codigo or not archivo:
        return "❌ Código o imagen faltante", 400

    imagen_bytes = archivo.read()

    try:
        test_image = Image.open(BytesIO(imagen_bytes))
        test_image.verify()
    except UnidentifiedImageError:
        return "❌ Imagen inválida", 502
    except Exception as e:
        return f"❌ Error procesando imagen: {str(e)}", 502

    if len(imagen_bytes) < 100:
        return "❌ Imagen vacía", 400

    timestamp = int(time.time())

    try:
        print(f"📦 Subiendo imagen con código: {codigo}")
        r1 = cloudinary.uploader.upload(
            BytesIO(imagen_bytes),
            public_id=f"postal/{codigo}_{timestamp}_original",
            overwrite=True
        )

        urls_cloudinary[codigo] = {"imagen": r1['secure_url']}

        # Guarda las URLs actualizadas en archivo
        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

        # ✅ Guarda la imagen en disco también (opcional, para mostrarla localmente si deseas)
        output_path = os.path.join(BASE, "static", "postales_generadas", f"{codigo}_original.jpg")
        with open(output_path, "wb") as f:
            f.write(imagen_bytes)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Subida fallida: {str(e)}", 500

    return redirect(f"/view_image?codigo={codigo}")
@app.route('/checkout_multiple', methods=['POST'])
def checkout_multiple():
    codigo = request.form.get("codigo")
    email = request.form.get("email")
    postales = request.form.getlist("postal")

    if not codigo or not email or not postales:
        return "Faltan datos", 400

    try:
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        line_items = [
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Postal {p}"},
                    "unit_amount": 300
                },
                "quantity": 1
            } for p in postales
        ]

        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success",
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "tipo": "postal",
                "codigo": codigo,
                "correo": email,
                "postales": ",".join(postales)
            }
        )
        return redirect(session.url, code=303)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error creando checkout: {str(e)}", 500
@app.route('/checkout_combined', methods=['POST'])
def checkout_combined():
    from dotenv import load_dotenv
    load_dotenv()  # para Render o local
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    codigo = request.form.get("codigo")
    email = request.form.get("email")
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    telefono = request.form.get("telefono")

    postales = request.form.getlist("postal")
    vinos = request.form.getlist("vino")

    productos = []

    line_items = []

    for p in postales:
        productos.append({
            "tipo": "postal",
            "codigo": codigo,
            "plantilla": p
        })
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"Postal {p}"},
                "unit_amount": 300
            },
            "quantity": 1
        })

    for v in vinos:
        cantidad = int(request.form.get(f"cantidad_{v}", 0))
        if cantidad > 0:
            productos.append({
                "tipo": "vino",
                "producto": v,
                "cantidad": cantidad
            })
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": v.replace("_", " ").title()},
                    "unit_amount": 1000
                },
                "quantity": cantidad
            })

    if not line_items:
        return "Debes seleccionar al menos un producto", 400

    session = stripe.checkout.Session.create(
        customer_email=email,
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url="https://postales-online.onrender.com/success",
        cancel_url="https://postales-online.onrender.com/cancel",
        metadata={
            "tipo": "combo",
            "correo": email,
            "productos_json": json.dumps(productos),
            "direccion": direccion,
            "telefono": telefono,
            "nombre": nombre
        }
    )
    return redirect(session.url, code=303)
@app.route('/pedido_vino', methods=['GET', 'POST'])
def pedido_vino():
    if request.method == 'GET':
        return """
        <h2>🍷 Pedido de Vino</h2>
        <form method='POST'>
            Email: <input name='email' type='email' required><br>
            Producto: <select name='producto'>
                <option value='vino_tinto'>Vino Tinto</option>
                <option value='vino_blanco'>Vino Blanco</option>
            </select><br>
            Cantidad: <input name='cantidad' type='number' value='1' min='1'><br>
            <button type='submit'>Pagar Vino</button>
        </form>
        """
    email = request.form.get("email")
    producto = request.form.get("producto")
    cantidad = int(request.form.get("cantidad"))
    precios = {"vino_tinto": 1200, "vino_blanco": 1000}
    if producto not in precios:
        return "Producto inválido"
    session = stripe.checkout.Session.create(
        customer_email=email,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": producto.replace("_", " ").title()},
                "unit_amount": precios[producto]
            },
            "quantity": cantidad
        }],
        mode="payment",
        success_url="https://postales-online.onrender.com/success",
        cancel_url="https://postales-online.onrender.com/cancel",
        metadata={
            "tipo": "vino",
            "correo": email,
            "producto": producto,
            "cantidad": cantidad
        }
    )
    return redirect(session.url, code=303)

@app.route('/webhook_stripe', methods=['POST'])
def webhook_stripe():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return f"Webhook inválido: {e}", 400
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get("metadata", {})
        pedido = {
            "email": session.get("customer_email"),
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": metadata.get("tipo"),
            "productos": metadata.get("postales", metadata.get("producto", "")).split(",")
        }
        guardar_pedido(pedido)
    return '', 200

@app.route('/admin_pedidos')
def admin_pedidos():
    token = request.args.get("token")
    if token != "secreto123":
        return "Acceso denegado", 403

    if not os.path.exists(PEDIDOS_FILE):
        return "No hay pedidos"

    try:
        with open(PEDIDOS_FILE) as f:
            pedidos = json.load(f)
    except Exception as e:
        return f"Error leyendo pedidos: {str(e)}", 500

    html = "<h2>📦 Pedidos registrados</h2><ul>"
    for p in pedidos:
        html += f"<li><strong>{p['fecha']}</strong> - {p.get('tipo_compra', 'N/A')} - {p.get('correo', '')}<br>"

        detalles = ""
        for prod in p.get("productos", []):
            if prod.get("tipo") == "postal":
                detalles += f"📸 Postal: {prod.get('plantilla', '')}<br>"
            elif prod.get("tipo") == "vino":
                detalles += f"🍷 Vino: {prod.get('producto')} x {prod.get('cantidad')}<br>"
            elif prod.get("tipo") == "camiseta":
                detalles += f"👕 Camiseta: {prod.get('modelo')} Talla {prod.get('talla')} x {prod.get('cantidad')}<br>"

        html += detalles
        html += f"<i>📍 {p.get('direccion', '')} / 📞 {p.get('telefono', '')}</i><br>"
        html += f"<i>📝 {p.get('comentarios', '')}</i></li><hr>"
    html += "</ul>"
    return html
@app.route('/cancel')
def cancel():
    return "<h2>⚠️ Pago cancelado</h2><a href='/'>Volver al inicio</a>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
