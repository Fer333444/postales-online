
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
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")
PEDIDOS_FILE = os.path.join(BASE, "pedidos.json")
urls_cloudinary = {}

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
    return """
    <h2>Bienvenido</h2>
    <a href='/pedido_vino'>Pedir Vino</a><br>
    <a href='/search'>Buscar Postal</a><br>
    <a href='/subir_postal'>Subir Foto</a>
    """

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
    archivos = []

    if os.path.exists(postales_path):
        archivos = [f for f in os.listdir(postales_path) if f.startswith(codigo)]

    if not archivos:
        return f"<h2>❌ No se encontraron postales para el código '{codigo}'</h2><a href='/'>Volver al inicio</a>"

    html = f"""
    <h2>📸 Tu postal personalizada</h2>
    <form action='/checkout_multiple' method='POST'>
        <input type='hidden' name='codigo' value='{codigo}'>
        <div style='display:flex; flex-wrap:wrap; gap:20px; justify-content:center;'>
    """

    for img in archivos:
        html += f"""
        <div style='text-align:center;'>
            <img src='/static/postales_generadas/{img}' width='200'><br>
            <label><input type='checkbox' name='postal' value='{img}'> Seleccionar</label>
        </div>
        """

    html += """
        </div><br>
        <input type='email' name='email' placeholder='Tu correo electrónico' required><br><br>
        <button type='submit'>💳 Pagar y recibir postales</button>
    </form>
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
    line_items = [{
        "price_data": {
            "currency": "eur",
            "product_data": {"name": f"Postal {p}"},
            "unit_amount": 300
        },
        "quantity": 1
    } for p in postales]
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
