import os
import json
import datetime
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
        # Subida original a Cloudinary
        r1 = cloudinary.uploader.upload(
            BytesIO(imagen_bytes),
            public_id=f"postal/{codigo}_{timestamp}_original",
            overwrite=True
        )

        # Guarda en el diccionario
        urls_cloudinary[codigo] = {
            "imagen": r1['secure_url'],
            "postal": postales_urls[0] if postales_urls else ""
        }

        # Actualiza archivo
        with open(URLS_FILE, "w") as f:
            json.dump(urls_cloudinary, f)

    except Exception as e:
        print(f"❌ Error subiendo a Cloudinary: {e}")
        return f"Subida fallida: {str(e)}", 500

    if codigo not in cola_postales:
        cola_postales.append(codigo)

    return redirect(f"/view_image/{codigo}")
@app.route('/enviar_postal', methods=['POST'])
def enviar_postal():
    email = request.form.get("email")
    codigo = request.form.get("codigo")

    if not email or not codigo:
        return "Faltan datos", 400

    enlace = urls_cloudinary.get(codigo, {}).get("postal")
    if enlace:
        enviar_email_profesional(email, enlace)
        return f'''
        <h2>✅ Postal enviada a {email}</h2>
        <p><a href="/">Volver al inicio</a></p>
        '''
    else:
        return f"<h2>⚠️ No se encontró la postal para el código {codigo}</h2>", 404
@app.route('/pedido_vino', methods=['GET', 'POST'])
def pedido_vino():
    if request.method == 'GET':
        return '''
        <form action="/pedido_vino" method="POST">
            <h2>🍷 Pedido de vino</h2>
            <input name="nombre" placeholder="Nombre completo" required><br>
            <input name="direccion" placeholder="Dirección completa" required><br>
            <input name="telefono" placeholder="Teléfono" required><br>
            <input name="email" type="email" placeholder="Correo electrónico" required><br><br>

            <label>Producto 1:</label>
            <select name="producto1">
                <option value="">-- Seleccionar --</option>
                <option value="vino_tinto">Vino Tinto</option>
                <option value="vino_blanco">Vino Blanco</option>
                <option value="vino_rosado">Vino Rosado</option>
            </select>
            <input name="cantidad1" type="number" min="0" value="0"><br>

            <label>Producto 2:</label>
            <select name="producto2">
                <option value="">-- Seleccionar --</option>
                <option value="vino_tinto">Vino Tinto</option>
                <option value="vino_blanco">Vino Blanco</option>
                <option value="vino_rosado">Vino Rosado</option>
            </select>
            <input name="cantidad2" type="number" min="0" value="0"><br>

            <textarea name="comentarios" placeholder="Comentarios (opcional)"></textarea><br>

            <button type="submit">💳 Pagar y hacer pedido</button>
        </form>
        '''
    else:
        nombre = request.form.get("nombre")
        direccion = request.form.get("direccion")
        telefono = request.form.get("telefono")
        email = request.form.get("email")
        comentarios = request.form.get("comentarios", "")

        precios = {
            "vino_tinto": ("Vino Tinto", 1200),
            "vino_blanco": ("Vino Blanco", 1000),
            "vino_rosado": ("Vino Rosado", 1100)
        }

        items = []
        for i in range(1, 3):
            p = request.form.get(f"producto{i}")
            c = int(request.form.get(f"cantidad{i}", 0))
            if p and p in precios and c > 0:
                nombre_prod, precio = precios[p]
                items.append({
                    "price_data": {
                        "currency": "eur",
                        "product_data": {"name": nombre_prod},
                        "unit_amount": precio
                    },
                    "quantity": c
                })

        if not items:
            return "⚠️ Debes seleccionar al menos un producto", 400

        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success?tipo=vino",
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "tipo": "vino",
                "nombre": nombre,
                "direccion": direccion,
                "telefono": telefono,
                "comentarios": comentarios
            }
        )
        return redirect(session.url, code=303)
@app.route('/checkout_multiple', methods=['POST'])
def checkout_multiple():
    codigo = request.form.get("codigo")
    email = request.form.get("email")
    postales = request.form.getlist("postal")

    if not codigo or not email or not postales:
        return "Faltan datos", 400

    productos = [
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
        line_items=productos,
        mode="payment",
        success_url="https://postales-online.onrender.com/success_multiple",
        cancel_url="https://postales-online.onrender.com/cancel",
        metadata={
            "tipo": "postal",
            "codigo": codigo,
            "correo": email,
            "postales": ",".join(postales)
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
        if session.get("metadata", {}).get("tipo") == "postal":
            registro = {
                "tipo": "postal",
                "codigo": session["metadata"].get("codigo"),
                "correo": session.get("customer_email"),
                "fecha": datetime.utcnow().isoformat(),
                "productos": session["metadata"].get("postales", "").split(",")
            }
            guardar_registro_pedido(registro)

    return '', 200

def guardar_registro_pedido(pedido):
    pedidos_file = os.path.join(BASE, "pedidos.json")
    todos = []
    if os.path.exists(pedidos_file):
        with open(pedidos_file, "r") as f:
            todos = json.load(f)
    todos.append(pedido)
    with open(pedidos_file, "w") as f:
        json.dump(todos, f, indent=2)
@app.route('/webhook_stripe', methods=['POST'])
def webhook_stripe():
    import datetime
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
        metadata = session.get('metadata', {})
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        pedido = {
            "email": email,
            "fecha": fecha,
            "tipo": metadata.get("tipo", "desconocido"),
            "productos": [],
            "codigo_postal": metadata.get("codigo", ""),
            "direccion": metadata.get("direccion", ""),
            "telefono": metadata.get("telefono", ""),
            "comentarios": metadata.get("comentarios", "")
        }

        # Si es una postal personalizada
        if "postal" in metadata:
            enlace = f"https://postales-online.onrender.com/static/postales_generadas/{metadata['postal']}"
            pedido["productos"].append({
                "nombre": "Postal personalizada",
                "archivo": metadata["postal"],
                "descarga": enlace
            })

        # Extraer productos desde Stripe line_items
        try:
            line_items = stripe.checkout.Session.list_line_items(session["id"], limit=10)
            for item in line_items.data:
                pedido["productos"].append({
                    "nombre": item.description,
                    "cantidad": item.quantity,
                    "precio_unitario": item.amount_total / item.quantity / 100
                })
        except Exception as e:
            print("❌ No se pudo leer line_items:", e)

        # Guardar pedido en pedidos.json
        pedidos_file = os.path.join(BASE, "pedidos.json")
        try:
            if os.path.exists(pedidos_file):
                with open(pedidos_file, "r", encoding="utf-8") as f:
                    pedidos = json.load(f)
            else:
                pedidos = []

            pedidos.append(pedido)

            with open(pedidos_file, "w", encoding="utf-8") as f:
                json.dump(pedidos, f, indent=2, ensure_ascii=False)

            print(f"✅ Pedido guardado de {email}")

        except Exception as e:
            print(f"❌ Error guardando pedido: {e}")

    return '', 200

@app.route('/success')
def success():
    codigo = request.args.get("codigo", "")
    postal = request.args.get("postal", "")  # postal seleccionada

    if not postal:
        return f'''
        <h2>✅ ¡Pago exitoso!</h2>
        <p>Tu postal ha sido procesada, pero no se pudo identificar el archivo.</p>
        <a href="/">Volver al inicio</a>
        '''

    enlace = f"/static/postales_generadas/{postal}"

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Postal lista para descargar</title>
        <style>
            body {{ background-color: #111; color: white; text-align: center; font-family: sans-serif; }}
            .descargar {{
                background-color: #2ecc71;
                color: white;
                padding: 12px 25px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 18px;
                display: inline-block;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <h2>✅ ¡Pago exitoso!</h2>
        <p>Tu postal con código <strong>{codigo}</strong> ha sido procesada.</p>
        <img src="{enlace}" style="max-width:300px; border:2px solid white; border-radius:8px;"><br>
        <a class="descargar" href="{enlace}" download>⬇️ Descargar postal</a>
        <p><a href="/">Volver al inicio</a></p>
    </body>
    </html>
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

    postales_path = os.path.join(BASE, "static", "postales_generadas")
    postales_multiples = []
    if os.path.exists(postales_path):
        for file in os.listdir(postales_path):
            if file.startswith(codigo):
                postales_multiples.append(file)  # solo el nombre

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tu postal personalizada</title>
        <style>
            body {{
                background-color: #111;
                color: white;
                text-align: center;
                font-family: sans-serif;
            }}
            .grid {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                margin-bottom: 40px;
            }}
            img {{
                max-width: 280px;
                border: 2px solid white;
                border-radius: 8px;
            }}
            label {{
                display: block;
                margin-top: 10px;
            }}
            .shopify-button {{
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                margin: 10px 0;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
            }}
            input[type="email"], select {{
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h2>📸 Tu postal personalizada</h2>
        <div class="grid">
            {''.join(f'<div><img src="/static/postales_generadas/{file}"><br><label><input type="radio" name="postal" value="{file}" required> Seleccionar</label></div>' for file in postales_multiples)}
        </div>

        <div>
            <h3>💌 Recibe tu postal seleccionada por email tras el pago</h3>
            <form action="/checkout" method="POST">
                <input type="hidden" name="codigo" value="{codigo}">
                <input type="email" name="email" placeholder="Tu correo electrónico" required><br>
                <button type="submit" class="shopify-button">💳 Pagar y recibir postal</button>
            </form>
        </div>

        <script>
            const form = document.querySelector("form");
            form.addEventListener("submit", function(e) {{
                const selected = document.querySelector("input[name='postal']:checked");
                if (selected) {{
                    const input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "postal";
                    input.value = selected.value;
                    form.appendChild(input);
                }}
            }});
        </script>
    </body>
    </html>
    '''
    return html
import datetime

@app.route('/admin_pedidos')
def admin_pedidos():
    token = request.args.get("token", "")
    if token != "secreto123":
        return "🔒 Acceso no autorizado", 403

    pedidos_file = os.path.join(BASE, "pedidos.json")
    if not os.path.exists(pedidos_file):
        return "No hay pedidos registrados aún."

    with open(pedidos_file) as f:
        pedidos = json.load(f)

    html = "<h2>📦 Pedidos registrados</h2><ul>"
    for p in pedidos:
        html += f"<li><strong>{p['tipo'].capitalize()}</strong> - {p['correo']} - {p['fecha']}<br>Productos: {', '.join(p['productos'])}</li><hr>"
    html += "</ul>"
    return html
def registrar_pedido(correo, tipo, productos, detalles={}):
    pedido = {
        "correo": correo,
        "tipo": tipo,
        "productos": productos,
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    pedido.update(detalles)
    pedidos_file = os.path.join(BASE, "pedidos.json")
    todos = []
    if os.path.exists(pedidos_file):
        with open(pedidos_file) as f:
            todos = json.load(f)
    todos.append(pedido)
    with open(pedidos_file, "w") as f:
        json.dump(todos, f, indent=2)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)