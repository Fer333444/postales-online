
import os
import json
import time
import datetime
from flask import Flask, request, redirect
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import cloudinary
import cloudinary.uploader
import stripe

# Config
cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)
app = Flask(__name__)

# 📦 Rutas base y archivos
BASE = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")
PEDIDOS_FILE = os.path.join(BASE, "pedidos.json")
urls_cloudinary = {}

# ✅ Asegura que existan las carpetas necesarias
os.makedirs(os.path.join(BASE, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE, "static", "postales_generadas"), exist_ok=True)

# ✅ Cargar URLs si existen
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
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Buscar postal</title>
        <style>
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
                max-width: 400px;
                width: 90%;
            }
            input, button {
                padding: 12px;
                font-size: 18px;
                margin-top: 10px;
                border-radius: 8px;
                border: none;
                width: 100%;
            }
            h2 {{
                margin-bottom: 20px;
            }}
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
                <br>
                <button type="submit">Ver postales</button>
            </form>
        </div>
    </body>
    </html>
    '''

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
        <title>Postales y Vinos</title>
        <style>
            body {{
                background-color: #111;
                color: white;
                font-family: sans-serif;
                text-align: center;
            }}
            .grid {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                margin: 20px auto;
            }}
            img {{
                max-width: 240px;
                border: 2px solid white;
                border-radius: 8px;
            }}
            .seccion {{
                background-color: #222;
                padding: 20px;
                margin: 30px auto;
                border-radius: 10px;
                width: 95%;
                max-width: 900px;
            }}
            input, select, button {{
                padding: 10px;
                font-size: 16px;
                margin: 5px 0;
                width: 100%;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>📸 Tu postal personalizada</h1>
        <form action="/checkout_combined" method="POST">
            <input type="hidden" name="codigo" value="{codigo}">
            <div class="seccion">
                <h2>Postales generadas</h2>
                <div class="grid">
    """

    for img in archivos:
        html += f"""
        <div>
            <img src="/static/postales_generadas/{img}">
            <br><label><input type="checkbox" name="postal" value="{img}"> Seleccionar</label>
        </div>
        """

    html += """
                </div>
            </div>
            <div class="seccion">
                <h2>🍷 Nuestros vinos</h2>
                <div class="grid">
    """

    for vino in vinos:
        html += f"""
        <div>
            <img src="/static/Vinos/{vino}">
            <p>{vino.replace("_", " ").replace(".jpg", "").title()}</p>
            <label>Seleccionar: <input type="checkbox" name="vino" value="{vino}"></label>
            <input type="number" name="cantidad_{vino}" value="0" min="0">
        </div>
        """

    html += """
                </div>
            </div>
            <div class="seccion">
                <h3>💌 Tu correo</h3>
                <input type="email" name="email" placeholder="Tu correo electrónico" required>
                <button type="submit">💳 Pagar selección</button>
            </div>
        </form>
    </body>
    </html>
    """

    return html

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
    codigo = request.form.get("codigo")
    email = request.form.get("email")
    postales = request.form.getlist("postal")
    vinos = request.form.getlist("vino")

    line_items = []

    # Añadir postales seleccionadas
    for p in postales:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"Postal {p}"},
                "unit_amount": 300
            },
            "quantity": 1
        })

    # Añadir vinos seleccionados
    precios = {
        "vino_tinto.jpg": 1200,
        "vino_rosado.jpg": 1000
    }

    for vino in vinos:
        cantidad = int(request.form.get(f"cantidad_{vino}", 0))
        if cantidad > 0 and vino in precios:
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": vino.replace("_", " ").replace(".jpg", "").title()},
                    "unit_amount": precios[vino]
                },
                "quantity": cantidad
            })

    if not line_items:
        return "⚠️ Debes seleccionar al menos un producto", 400

    try:
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success",
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "tipo": "mixto",
                "correo": email,
                "codigo": codigo,
                "postales": ",".join(postales),
                "vinos": ",".join(vinos)
            }
        )
        return redirect(session.url, code=303)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error en checkout combinado: {str(e)}", 500
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
    with open(PEDIDOS_FILE) as f:
        pedidos = json.load(f)
    html = "<h2>📦 Pedidos</h2><ul>"
    for p in pedidos:
        html += f"<li>{p['fecha']} - {p['tipo']} - {p['email']}<br>Productos: {', '.join(p['productos'])}</li><hr>"
    html += "</ul>"
    return html

@app.route('/success')
def success():
    return "<h2>✅ Pago exitoso</h2><p>Tu pedido fue procesado correctamente.</p><a href='/'>Volver al inicio</a>"

@app.route('/cancel')
def cancel():
    return "<h2>⚠️ Pago cancelado</h2><a href='/'>Volver al inicio</a>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
