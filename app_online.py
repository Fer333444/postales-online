import os
import json
import time
from flask import Flask, request, jsonify, redirect
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import cloudinary
import cloudinary.uploader
import stripe
import sendgrid
from sendgrid.helpers.mail import Mail

# Configuración
cloudinary.config(
    cloud_name='dlcbxtcin',
    api_key='453723362245378',
    api_secret='Fn3h6rp_oG6lvaDRk7i6Dil1oQw'
)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE, "urls_cloudinary.json")
cola_postales = []
urls_cloudinary = {}

if os.path.exists(URLS_FILE):
    with open(URLS_FILE) as f:
        urls_cloudinary = json.load(f)

def generar_postales_multiples(imagen_bytes, codigo):
    plantillas_dir = os.path.join(BASE, "static", "plantillas_postal")
    salida_urls = []
    if not os.path.exists(plantillas_dir):
        print("❌ No se encontró la carpeta de plantillas")
        return []
    try:
        for plantilla_nombre in os.listdir(plantillas_dir):
            if plantilla_nombre.endswith(".jpg"):
                plantilla_path = os.path.join(plantillas_dir, plantilla_nombre)
                base = Image.open(plantilla_path).convert("RGB")
                foto = Image.open(BytesIO(imagen_bytes)).convert("RGB")
                foto = foto.resize((430, 330))
                base.paste(foto, (90, 95))
                salida = BytesIO()
                base.save(salida, format='JPEG')
                salida.seek(0)
                filename = f"{codigo}_{plantilla_nombre}"
                output_path = os.path.join(BASE, "static", "postales_generadas", filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(salida.read())
                salida_urls.append(f"/static/postales_generadas/{filename}")
    except Exception as e:
        print("❌ Error generando múltiples postales:", e)
    return salida_urls

def enviar_email_profesional(destinatario, enlace):
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
    mensaje = Mail(
        from_email=os.getenv("EMAIL_FROM"),
        to_emails=destinatario,
        subject='Tu postal personalizada está lista 📩',
        html_content=f'''
        <p>Gracias por tu compra.</p>
        <p>Haz clic aquí para <a href="{enlace}" target="_blank">descargar tu postal</a>.</p>
        <p>Saludos,<br>Equipo Postales Online</p>
        '''
    )
    try:
        response = sg.send(mensaje)
        print(f"✅ Email enviado a {destinatario} ({response.status_code})")
    except Exception as e:
        print(f"❌ Error enviando email: {e}")

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    archivo = request.files.get("imagen")
    if not codigo or not archivo:
        return "❌ Código o imagen faltante", 400
    imagen_bytes = archivo.read()
    try:
        test_image = Image.open(BytesIO(imagen_bytes))
        test_image.verify()
    except UnidentifiedImageError:
        return "❌ Imagen inválida o corrupta", 502
    if len(imagen_bytes) < 100:
        return "❌ Imagen vacía", 400
    postales_urls = generar_postales_multiples(imagen_bytes, codigo)
    timestamp = int(time.time())
    try:
        r1 = cloudinary.uploader.upload(BytesIO(imagen_bytes), public_id=f"postal/{codigo}_{timestamp}_original", overwrite=True)
        urls_cloudinary[codigo] = {
            "imagen": r1['secure_url'],
            "postal": postales_urls[0] if postales_urls else ""
        }
        with open("urls_cloudinary.json", "w") as f:
            json.dump(urls_cloudinary, f)
    except Exception as e:
        print(f"❌ Error en subida: {e}")
        return f"Subida fallida: {str(e)}", 500
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return redirect(f"/checkout?codigo={codigo}")

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        codigo = request.args.get("codigo")
        return f'''
        <form action="/checkout" method="POST">
            <input type="hidden" name="codigo" value="{codigo}" />
            <input type="email" name="email" placeholder="Tu correo" required />
            <button type="submit">Pagar con Stripe (Apple Pay incluido)</button>
        </form>
        '''
    else:
        codigo = request.form.get("codigo")
        email = request.form.get("email")
        if not codigo or not email:
            return "Código o email faltante", 400
        try:
            session = stripe.checkout.Session.create(
                customer_email=email,
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Postal personalizada ({codigo})"
                        },
                        "unit_amount": 300
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=f"/success?codigo={codigo}",
                cancel_url="/cancel",
                metadata={"codigo": codigo}
            )
            return redirect(session.url, code=303)
        except Exception as e:
            return f"Error en checkout: {e}", 500

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
        email = session.get('customer_email')
        codigo = session['metadata'].get('codigo')
        enlace = urls_cloudinary.get(codigo, {}).get('postal')
        if email and enlace:
            enviar_email_profesional(email, enlace)
    return '', 200

@app.route('/success')
def success():
    codigo = request.args.get("codigo", "")
    return f'''
    <h2>✅ ¡Pago exitoso!</h2>
    <p>Tu postal con código <strong>{codigo}</strong> ha sido procesada.</p>
    <p>Revisa tu correo para descargarla.</p>
    <p><a href="/">Volver al inicio</a></p>
    '''

@app.route('/cancel')
def cancel():
    return '''
    <h2>⚠️ Pago cancelado</h2>
    <p>No se ha realizado ningún cargo.</p>
    <p><a href="/">Volver al inicio</a></p>
    '''
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
            }
            input, button {
                padding: 10px;
                font-size: 16px;
                margin-top: 10px;
                border-radius: 5px;
                border: none;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop playsinline id="bg-video">
            <source src="/static/douro_sunset.mp4" type="video/mp4">
        </video>
        <div class="contenido">
            <h2>🔍 Buscar tu postal</h2>
            <form action="/search" method="get">
                <input type="text" name="codigo" placeholder="Ej: abc123" required />
                <br>
                <button type="submit">Ver postal</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    data = urls_cloudinary.get(codigo)
    if not data:
        return f'''
        <h2>❌ Código <code>{codigo}</code> no encontrado</h2>
        <p><a href="/">Volver al inicio</a></p>
        ''', 404

    # Enlaces de compra
    link_postal = "https://buy.stripe.com/00w3cu64DbCWa1Bbut4ZG01"
    link_camiseta = "https://www.pattseries.com/products/inclinacion-de-pecho"

    boton_postal = f'<a class="shopify-button" href="{link_postal}" target="_blank">Comprar postal</a>'
    boton_camiseta = f'<a class="shopify-button" href="{link_camiseta}" target="_blank">Comprar camiseta</a>'

    # Camisetas generadas
    previews = []
    base_previews = os.path.join(BASE, "static", "previews")
    if os.path.exists(base_previews):
        for file in os.listdir(base_previews):
            if file.startswith(f"preview_camiseta_{codigo}"):
                previews.append(f"/static/previews/{file}")

    # Postales múltiples generadas
    postales_path = os.path.join(BASE, "static", "postales_generadas")
    postales_multiples = []
    if os.path.exists(postales_path):
        for file in os.listdir(postales_path):
            if file.startswith(codigo):
                postales_multiples.append(f"/static/postales_generadas/{file}")

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vista de postal y camisetas</title>
        <style>
            body {{ background-color: #111; color: white; text-align: center; font-family: sans-serif; }}
            img {{ max-width: 280px; margin: 10px; cursor: pointer; border: 2px solid white; border-radius: 8px; }}
            .grid {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
            .shopify-button {{
                background-color: #2ecc71; color: white; padding: 10px 20px;
                margin: 5px auto; border: none; border-radius: 5px;
                text-decoration: none; display: inline-block;
            }}
        </style>
    </head>
    <body>
        <h2>📸 Tu postal personalizada</h2>
        <div class="grid">
            <div>
                <img src="{data.get('imagen', '')}">
                <br>{boton_postal}
            </div>
            {''.join(f'<div><img src="{url}"><br>{boton_postal}</div>' for url in postales_multiples)}
            {''.join(f'<div><img src="{preview}"><br>{boton_camiseta}</div>' for preview in previews)}
        </div>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)