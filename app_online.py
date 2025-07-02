import os
import json
import time
from flask import Flask, request, jsonify, redirect
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from flask import render_template_string
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
@app.route('/formulario_vino', methods=['POST'])
def formulario_vino():
    vinos_seleccionados = request.form.getlist("vino")
    cantidades = {vino: int(request.form.get(f"cantidad_{vino}", 0)) for vino in vinos_seleccionados}

    if not vinos_seleccionados:
        return "<h2>❌ No se seleccionaron vinos</h2><a href='/'>Volver</a>", 400

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Confirmar pedido de vinos</title>
        <style>
            body { background-color: #111; color: white; font-family: sans-serif; text-align: center; }
            form { max-width: 400px; margin: auto; background-color: #222; padding: 20px; border-radius: 10px; }
            input, button { margin-top: 10px; padding: 10px; width: 100%; border-radius: 5px; border: none; }
            button { background-color: gold; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>🍷 Confirmar pedido de vinos</h2>
        <form method="POST" action="/pagar_vino">
            <input type="hidden" name="vinos_json" value="''' + json.dumps(cantidades).replace('"', '&quot;') + '''">
            <input name="nombre" placeholder="Nombre completo" required><br>
            <input name="direccion" placeholder="Dirección completa" required><br>
            <input name="telefono" placeholder="Teléfono" required><br>
            <input type="email" name="email" placeholder="Correo electrónico" required><br>
            <button type="submit">💳 Pagar pedido de vinos</button>
        </form>
    </body>
    </html>
    '''
    return render_template_string(html)
@app.route('/pagar_vino', methods=['POST'])
def pagar_vino():
    vinos_json = request.form.get("vinos_json")
    email = request.form.get("email")
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    telefono = request.form.get("telefono")

    if not vinos_json or not email:
        return "Faltan datos", 400

    try:
        vinos = json.loads(vinos_json)
    except Exception as e:
        return f"Error leyendo los datos de vinos: {e}", 400

    precios = {
        "vino_tinto.jpg": 1200,     # 12.00 €
        "vino_rosado.jpg": 1100,    # 11.00 €
        "vino_blanco.jpg": 1000     # 10.00 €
    }

    line_items = []
    for vino, cantidad in vinos.items():
        if cantidad > 0 and vino in precios:
            nombre_producto = vino.replace(".jpg", "").replace("_", " ").title()
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"{nombre_producto}"},
                    "unit_amount": precios[vino]
                },
                "quantity": cantidad
            })

    if not line_items:
        return "No hay vinos válidos para pagar", 400

    try:
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success",
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "tipo": "vino",
                "correo": email,
                "direccion": direccion,
                "telefono": telefono,
                "nombre": nombre,
                "productos_json": json.dumps([
                    {"producto": k, "cantidad": v}
                    for k, v in vinos.items() if v > 0
                ])
            }
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"❌ Error creando sesión de pago: {e}", 500

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

@app.route('/checkout', methods=['POST'])
def checkout():
    codigo = request.form.get("codigo")
    email = request.form.get("email")
    postal = request.form.get("postal")  # nombre del archivo seleccionado

    if not codigo or not email or not postal:
        return "Faltan datos para crear el pago", 400

    try:
        session = stripe.checkout.Session.create(
            customer_email=email,
            metadata={
                "codigo": codigo,
                "postal": postal
            },
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"Postal personalizada ({codigo})"
                    },
                    "unit_amount": 100  # Precio en céntimos (1.00€)
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"https://postales-online.onrender.com/success?codigo={codigo}&postal={postal}",
            cancel_url="https://postales-online.onrender.com/cancel"
        )
        return redirect(session.url, code=303)

    except Exception as e:
        return f"Error creando sesión de pago: {str(e)}", 500
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
        postal_filename = session['metadata'].get('postal')  # ✅ la postal seleccionada

        if email and postal_filename:
            enlace = f"https://postales-online.onrender.com/static/postales_generadas/{postal_filename}"
            enviar_email_profesional(email, enlace)

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
def view_image(codigo):
    data = urls_cloudinary.get(codigo)
    if not data:
        return f'''
        <h2>❌ Código <code>{codigo}</code> no encontrado</h2>
        <p><a href="/">Volver al inicio</a></p>
        ''', 404

    postales_path = os.path.join(BASE, "static", "postales_generadas")
    vinos_path = os.path.join(BASE, "static", "Vinos")
    postales_multiples = []
    vinos = []

    if os.path.exists(postales_path):
        for file in os.listdir(postales_path):
            if file.startswith(codigo):
                postales_multiples.append(file)

    if os.path.exists(vinos_path):
        vinos = [f for f in os.listdir(vinos_path) if f.endswith((".jpg", ".png"))]

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tu postal personalizada</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                background-color: #111;
                color: white;
                font-family: sans-serif;
                text-align: center;
                touch-action: manipulation;
                -webkit-user-select: none;
                -webkit-touch-callout: none;
                user-select: none;
            }}
            .grid {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 16px;
                margin-bottom: 40px;
                padding: 10px;
            }}
            .postal-wrapper {{
                background-color: #222;
                border-radius: 12px;
                padding: 8px;
                max-width: 300px;
                width: 90%;
            }}
            img {{
                width: 100%;
                height: auto;
                border-radius: 10px;
                pointer-events: none;
                -webkit-user-drag: none;
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
            input[type="email"], select, input[type="number"] {{
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                margin-top: 10px;
                width: 90%;
                max-width: 300px;
                border: none;
            }}
            form {{ margin-bottom: 40px; }}
        </style>
    </head>
    <body oncontextmenu="return false">
        <h2>📸 Tu postal personalizada</h2>
        <div class="grid">
            {''.join(f'<div class="postal-wrapper"><img src="/static/postales_generadas/{file}" alt="postal {file}"><br><label><input type="radio" name="postal" value="{file}" required> Seleccionar</label></div>' for file in postales_multiples)}
        </div>

        <div>
            <h3>💌 Recibe tu postal seleccionada por email tras el pago</h3>
            <form action="/checkout" method="POST">
                <input type="hidden" name="codigo" value="{codigo}">
                <input type="email" name="email" placeholder="Tu correo electrónico" required><br>
                <button type="submit" class="shopify-button">💳 Pagar y recibir postal</button>
            </form>
        </div>

        <hr style="margin: 40px 0; border-color: #444">

        <h2>🍷 Selecciona vinos</h2>
        <form method="POST" action="/formulario_vino">
            <div class="grid">
    '''

    for vino in vinos:
        nombre = vino.replace(".jpg", "").replace(".png", "").replace("_", " ").title()
        html += f'''
                <div class="postal-wrapper">
                    <img src="/static/Vinos/{vino}" alt="vino {nombre}">
                    <label><input type="checkbox" name="vino" value="{vino}"> {nombre}</label><br>
                    <select name="cantidad_{vino}">
                        {''.join(f'<option value="{i}">{i}</option>' for i in range(0, 11))}
                    </select>
                </div>
        '''

    html += f'''
            </div>
            <button class="shopify-button" type="submit">🍷 Pedir vinos</button>
        </form>

        <script>
            const form = document.querySelector("form[action='/checkout']");
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
@app.route('/admin_pedidos')
def admin_pedidos():
    token = request.args.get("token")
    if token != "secreto123":
        return "Acceso denegado", 403

    if not os.path.exists("pedidos.json"):
        return "<h2>No hay pedidos registrados</h2>"

    with open("pedidos.json") as f:
        pedidos = json.load(f)

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Panel de Pedidos</title>
        <style>
            body { font-family: sans-serif; background-color: #111; color: white; padding: 20px; }
            h2 { text-align: center; color: gold; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #444; padding: 10px; text-align: left; }
            th { background-color: #222; color: white; }
            tr:nth-child(even) { background-color: #222; }
            .producto { margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <h2>📦 Pedidos Recibidos</h2>
        <table>
            <tr>
                <th>Fecha</th>
                <th>Correo</th>
                <th>Tipo</th>
                <th>Productos</th>
                <th>Dirección</th>
                <th>Teléfono</th>
            </tr>
    '''

    for pedido in pedidos:
        html += f'''
        <tr>
            <td>{pedido.get("fecha", "")}</td>
            <td>{pedido.get("correo", "")}</td>
            <td>{pedido.get("tipo", "")}</td>
            <td>
        '''
        for p in pedido.get("productos", []):
            if isinstance(p, str):
                html += f'<div class="producto">{p}</div>'
            elif isinstance(p, dict):
                html += f'<div class="producto">{p.get("producto", "")} x {p.get("cantidad", 1)}</div>'
        html += f'''
            </td>
            <td>{pedido.get("direccion", "")}</td>
            <td>{pedido.get("telefono", "")}</td>
        </tr>
        '''

    html += "</table></body></html>"
    return html
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)