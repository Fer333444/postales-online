import os
import json
import time
from flask import Flask, request, jsonify, redirect
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from datetime import datetime
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

    vinos_json = json.dumps(cantidades)

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Confirmar pedido de vinos</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            html, body {{
                background-color: #111;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                overflow: hidden;
            }}
            .formulario {{
                background-color: #222;
                padding: 25px 20px;
                border-radius: 15px;
                box-shadow: 0 0 12px rgba(255, 255, 255, 0.08);
                width: 90%;
                max-width: 400px;
                opacity: 0;
                transform: translateY(20px);
                animation: fadeInSlide 0.7s ease-out forwards;
            }}
            @keyframes fadeInSlide {{
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            .formulario h2 {{
                margin-top: 0;
                margin-bottom: 20px;
                color: #ffcc00;
                font-size: 22px;
            }}
            input, button {{
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border-radius: 8px;
                border: none;
                font-size: 16px;
                box-sizing: border-box;
            }}
            input {{
                background-color: #333;
                color: white;
            }}
            input:focus {{
                outline: 2px solid #2ecc71;
            }}
            button {{
                background-color: gold;
                color: black;
                font-weight: bold;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #f5d100;
            }}
        </style>
    </head>
    <body>
        <form method="POST" action="/pagar_vino" class="formulario">
            <h2>🍷 Confirmar pedido de vinos</h2>
            <input type="hidden" name="vinos_json" value='{vinos_json}'>
            <input name="nombre" placeholder="Nombre completo" required>
            <input name="direccion" placeholder="Dirección completa" required>
            <input name="telefono" placeholder="Teléfono" required>
            <input type="email" name="email" placeholder="Correo electrónico" required>
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
        "vino_tinto.jpg": 120,     # 12.00 €
        "vino_rosado.jpg": 110,    # 11.00 €
        "vino_blanco.jpg": 100     # 10.00 €
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
            success_url="https://postales-online.onrender.com/success_vino",
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
@app.route('/checkout_multiple_postales', methods=['POST'])
def checkout_multiple_postales():
    codigo = request.form.get("codigo")
    postales = request.form.getlist("postales")

    if not codigo or not postales:
        return "Faltan datos para procesar el pago", 400

    line_items = []
    for postal in postales:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": f"Postal personalizada ({postal})"
                },
                "unit_amount": 300  # 3.00 €
            },
            "quantity": 1
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success_paquete",
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "codigo": codigo,
                "tipo": "postales_multiple",
                "postales": json.dumps(postales)
            }
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"❌ Error creando sesión de pago: {e}", 500
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
        metadata = session.get('metadata', {})

        tipo = metadata.get("tipo")
        try:
            productos = json.loads(metadata.get("productos_json", "[]"))
        except:
            productos = []

        pedido_id = str(randint(10000000, 99999999))  # ID de 8 dígitos numérico

        pedido = {
            "id": pedido_id,
            "fecha": datetime.utcnow().isoformat(),
            "correo": metadata.get("correo", email),
            "tipo": tipo,
            "productos": productos,
            "direccion": metadata.get("direccion", ""),
            "telefono": metadata.get("telefono", ""),
            "nombre": metadata.get("nombre", ""),
            "estado": "🕓 En proceso"
        }

        pedidos_path = os.path.join(BASE, "pedidos.json")
        pedidos_actuales = []

        if os.path.exists(pedidos_path):
            with open(pedidos_path) as f:
                try:
                    pedidos_actuales = json.load(f)
                except:
                    pedidos_actuales = []

        pedidos_actuales.append(pedido)
        with open(pedidos_path, "w") as f:
            json.dump(pedidos_actuales, f, indent=2)

    return '', 200
@app.route('/success')
def success():
    codigo = request.args.get("codigo", "")
    postal = request.args.get("postal", "")
    postales_json = request.args.get("postales_json", "")
    pedido_id = request.args.get("pedido_id", "")

    descarga_html = ""
    if postales_json:
        try:
            postales = json.loads(postales_json)
            if len(postales) == 1:
                enlace = f"/static/postales_generadas/{postales[0]}"
                descarga_html = f'''
                    <div class="preview">
                        <img src="{enlace}">
                        <br>
                        <a class="button" href="{enlace}" download>⬇️ Descargar postal</a>
                    </div>
                '''
            elif len(postales) > 1:
                descarga_html = f'''
                    <form method="POST" action="/descargar_postales">
                        <input type="hidden" name="postales_json" value='{json.dumps(postales)}'>
                        <button class="button" type="submit">⬇️ Descargar todas las postales (ZIP)</button>
                    </form>
                '''
        except:
            descarga_html = "<p>⚠️ No se pudo procesar el archivo correctamente.</p>"
    elif postal:
        enlace = f"/static/postales_generadas/{postal}"
        descarga_html = f'''
            <div class="preview">
                <img src="{enlace}">
                <br>
                <a class="button" href="{enlace}" download>⬇️ Descargar postal</a>
            </div>
        '''
    else:
        descarga_html = "<p>Pero no se pudo identificar el archivo.</p>"

    seguimiento_html = ""
    if pedido_id:
        seguimiento_html = f'''<p><a class="button" href="/ver_pedido/{pedido_id}">🔎 Ver estado de tu pedido</a></p>'''

    return f'''
    <html>
    <head>
        <meta charset="utf-8">
        <title>✅ Pago exitoso</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                background-color: #111;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .card {{
                background-color: #1e1e1e;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 0 20px rgba(46, 204, 113, 0.3);
                border: 2px solid #2ecc71;
            }}
            .button {{
                margin-top: 20px;
                background: #2ecc71;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                cursor: pointer;
                display: inline-block;
            }}
            .preview img {{
                max-width: 280px;
                border-radius: 10px;
                border: 2px solid white;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>✅ ¡Pago exitoso!</h2>
            <p>Tu pedido ha sido procesado correctamente.</p>
            {descarga_html}
            {seguimiento_html}
            <p><a class="button" href="/">↩️ Volver al inicio</a></p>
        </div>
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
        <title>Buscar postal o pedido</title>
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
            <hr style="margin: 30px 0;">
            <h2>🔎 Ver estado de tu pedido</h2>
            <form action="/pedido" method="get">
                <input type="text" name="id" placeholder="ID de pedido" required />
                <br>
                <button type="submit">Ver estado</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

# ✅ MODIFICACIÓN 1: Vista /view_image/<codigo> con diseño responsive profesional

# ✅ Bloque HTML actualizado para enviar camisetas + vinos a /pagar_productos_seleccionados
# Incluye los datos completos, y `productos_json` bien formado para el backend

# ✅ Vista actualizada de /view_image/<codigo> con formulario en página aparte y todas las funciones integradas

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
    camisetas_path = os.path.join(BASE, "static", "camisetas")

    postales_multiples = []
    vinos = []
    camisetas = []

    if os.path.exists(postales_path):
        postales_multiples = [f for f in os.listdir(postales_path) if f.startswith(codigo)]

    if os.path.exists(vinos_path):
        vinos = [f for f in os.listdir(vinos_path) if f.endswith((".jpg", ".png"))]

    if os.path.exists(camisetas_path):
        camisetas = [f for f in os.listdir(camisetas_path) if f.endswith((".jpg", ".png"))]

    html = render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Tu postal personalizada</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { background-color: #111; color: white; font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 20px; }
            h2 { color: #ffcc00; margin-bottom: 10px; }
            .scroll-container { display: flex; justify-content: center; flex-wrap: wrap; gap: 16px; margin: 20px 0; }
            .postal-wrapper { background-color: #222; border-radius: 12px; padding: 12px; width: 200px; border: 2px solid transparent; }
            .postal-wrapper.selected { border-color: #2ecc71; box-shadow: 0 0 12px #2ecc71; }
            img { width: 100%; height: auto; border-radius: 8px; }
            label { display: block; margin-top: 6px; }
            .shopify-button { background-color: #2ecc71; color: white; padding: 10px 20px; margin: 15px 10px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>📸 Elige tus postales favoritas</h2>

        <form method="POST" action="/pagar_postales_directo" id="form_postales">
            <input type="hidden" name="codigo" value="{{ codigo }}">
            <input type="hidden" name="postales_json" id="postales_json">
            <div class="scroll-container">
                {% for file in postales %}
                    <div class="postal-wrapper" onclick="seleccionarPostal('{{ file }}')">
                        <img src="/static/postales_generadas/{{ file }}">
                        <label><input type="checkbox" name="postal" value="{{ file }}"> ✔️ 3 €</label>
                    </div>
                {% endfor %}
            </div>
            <button class="shopify-button" type="submit">💳 Pagar postales seleccionadas</button>
        </form>

        <h2>🍷 Vinos</h2>
        <form method="POST" action="/formulario_pago" id="form_productos">
            <input type="hidden" name="codigo" value="{{ codigo }}">
            <input type="hidden" name="productos_json" id="productos_json">
            <div class="scroll-container">
                {% for vino in vinos %}
                    <div class="postal-wrapper">
                        <img src="/static/Vinos/{{ vino }}">
                        <label><input type="checkbox" name="vino" value="{{ vino }}"> {{ vino.replace('.jpg', '').replace('_', ' ').title() }}</label>
                        <select name="cantidad_{{ vino }}">
                            {% for i in range(11) %}<option value="{{ i }}">{{ i }}</option>{% endfor %}
                        </select>
                    </div>
                {% endfor %}
            </div>

            <h2>👕 Camisetas</h2>
            <div class="scroll-container">
                {% for c in camisetas %}
                    <div class="postal-wrapper">
                        <img src="/static/camisetas/{{ c }}">
                        <label><input type="checkbox" name="camiseta" value="{{ c }}"> {{ c.replace('.jpg', '').replace('_', ' ').title() }}</label>
                        <select name="talla_{{ c }}">
                            <option value="S">S</option>
                            <option value="M">M</option>
                            <option value="L">L</option>
                            <option value="XL">XL</option>
                        </select>
                        <select name="cantidad_{{ c }}">
                            {% for i in range(11) %}<option value="{{ i }}">{{ i }}</option>{% endfor %}
                        </select>
                    </div>
                {% endfor %}
            </div>
            <br>
            <button type="submit" class="shopify-button">💳 Pagar productos seleccionados</button>
        </form>

        <script>
            function seleccionarPostal(nombre) {
                const cb = document.querySelector(`input[value='${nombre}']`);
                if (cb) {
                    cb.checked = !cb.checked;
                    cb.closest('.postal-wrapper').classList.toggle("selected");
                }
            }

            document.getElementById("form_postales").addEventListener("submit", function(e) {
                const seleccionadas = Array.from(document.querySelectorAll("input[name='postal']:checked")).map(p => p.value);
                if (seleccionadas.length === 0) {
                    e.preventDefault();
                    alert("Selecciona al menos una postal para pagar.");
                    return;
                }
                document.getElementById("postales_json").value = JSON.stringify(seleccionadas);
            });

            document.getElementById("form_productos").addEventListener("submit", function(e) {
                const vinos = Array.from(document.querySelectorAll("input[name='vino']:checked")).map(v => {
                    const cantidad = parseInt(document.querySelector(`select[name='cantidad_${v.value}']`).value || 0);
                    return { producto: v.value, cantidad };
                }).filter(v => v.cantidad > 0);
                const camisetas = Array.from(document.querySelectorAll("input[name='camiseta']:checked")).map(c => {
                    const cantidad = parseInt(document.querySelector(`select[name='cantidad_${c.value}']`).value || 0);
                    const talla = document.querySelector(`select[name='talla_${c.value}']`).value;
                    return { producto: c.value, cantidad, talla };
                }).filter(c => c.cantidad > 0);
                const todos = [...vinos, ...camisetas];
                if (todos.length === 0) {
                    e.preventDefault();
                    alert("Selecciona al menos un vino o una camiseta para pagar.");
                    return;
                }
                document.getElementById("productos_json").value = JSON.stringify(todos);
            });
        </script>
    </body>
    </html>
    ''', codigo=codigo, postales=postales_multiples, vinos=vinos, camisetas=camisetas)

    return html
# ✅ Código completo actualizado para mostrar talla y cantidad de camisetas y vinos en el panel de pedidos

@app.route('/admin_pedidos')
def admin_pedidos():
    token = request.args.get("token")
    if token != os.getenv("ADMIN_TOKEN", "secreto123"):
        return "Acceso denegado", 403

    PEDIDOS_FILE = os.path.join(BASE, "pedidos.json")

    if not os.path.exists(PEDIDOS_FILE):
        return "<h2>No hay pedidos registrados</h2>"

    try:
        with open(PEDIDOS_FILE) as f:
            pedidos = json.load(f)
    except Exception as e:
        return f"<h2>Error leyendo pedidos:</h2><pre>{str(e)}</pre>"

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Panel de Pedidos</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #111; color: white; padding: 20px; }
            h2 { text-align: center; color: gold; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; font-size: 14px; }
            th, td { border: 1px solid #444; padding: 10px; text-align: left; }
            th { background-color: #222; color: #ffcc00; }
            tr:nth-child(even) { background-color: #1a1a1a; }
            .producto { background-color: #2c2c2c; margin: 3px 0; padding: 4px 8px; border-radius: 4px; display: inline-block; color: #fff; }
            select.estado { padding: 6px; border-radius: 5px; background: #333; color: white; }
        </style>
        <script>
            async function actualizarEstado(id) {
                const select = document.getElementById('estado_' + id);
                const estado = select.value;
                await fetch('/actualizar_estado_pedido', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id, estado })
                });
            }
        </script>
    </head>
    <body>
        <h2>📦 Pedidos Recibidos</h2>
        <table>
            <tr>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Tipo</th>
                <th>Productos</th>
                <th>Dirección</th>
                <th>Teléfono</th>
                <th>Estado</th>
            </tr>
    '''

    for pedido in pedidos:
        fecha_hora = pedido.get("fecha", "")
        fecha, hora = fecha_hora.split("T")[0], fecha_hora.split("T")[1][:8]
        productos = pedido.get("productos", [])
        productos_html = ""
        for p in productos:
            if isinstance(p, dict):
                nombre = normalizar_nombre(p.get("producto", ""))
                cantidad = int(p.get("cantidad", 1))
                talla = p.get("talla")
                descripcion = f"{nombre} x {cantidad}"
                if talla:
                    descripcion += f" (Talla {talla})"
                productos_html += f'<div class="producto">{descripcion}</div>'

        id_pedido = pedido.get("id", "")
        estado_actual = pedido.get("estado", "🕓 En proceso")

        html += f'''
        <tr>
            <td>{fecha}</td>
            <td>{hora}</td>
            <td>{pedido.get("nombre", "")}</td>
            <td>{pedido.get("correo", "")}</td>
            <td>{pedido.get("tipo", "")}</td>
            <td>{productos_html}</td>
            <td>{pedido.get("direccion", "")}</td>
            <td>{pedido.get("telefono", "")}</td>
            <td>
                <select id="estado_{id_pedido}" class="estado" onchange="actualizarEstado('{id_pedido}')">
                    <option value="🕓 En proceso" {'selected' if estado_actual == '🕓 En proceso' else ''}>🕓 En proceso</option>
                    <option value="✅ Enviado" {'selected' if estado_actual == '✅ Enviado' else ''}>✅ Enviado</option>
                    <option value="📦 Listo para recoger" {'selected' if estado_actual == '📦 Listo para recoger' else ''}>📦 Listo para recoger</option>
                </select>
            </td>
        </tr>
        '''

    html += "</table></body></html>"
    return html
@app.route('/success_vino')
def success_vino():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>✅ Pedido confirmado</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                background-color: #111;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background-color: #1e1e1e;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 0 20px rgba(46, 204, 113, 0.3);
                border: 2px solid #2ecc71;
            }
            h2 {
                color: #2ecc71;
                font-size: 24px;
                margin-bottom: 10px;
            }
            p {
                margin: 10px 0;
            }
            a.button {
                display: inline-block;
                margin-top: 20px;
                background: #2ecc71;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>✅ ¡Pago exitoso!</h2>
            <p>Tu pedido de vinos ha sido recibido correctamente.</p>
            <p>Te contactaremos pronto para confirmar el envío.</p>
            <a class="button" href="/">↩️ Volver al inicio</a>
        </div>
    </body>
    </html>
    '''
@app.route('/pagar_postales_seleccionadas', methods=['POST'])
def pagar_postales_seleccionadas():
    codigo = request.form.get("codigo")
    postales_json = request.form.get("postales_json")
    email = request.form.get("email", "anonimo@postales.com")

    if not codigo or not postales_json:
        return "❌ Faltan datos para procesar el pago", 400

    try:
        postales = json.loads(postales_json)
    except Exception as e:
        return f"❌ Error leyendo postales seleccionadas: {e}", 400

    if not postales:
        return "❌ No se seleccionaron postales", 400

    line_items = []
    precio_unitario = 300  # 3€ por defecto

    if len(postales) == 5:
        precio_unitario = 100  # aplica descuento a 1€/unidad

    for p in postales:
        nombre_limpio = p.replace(".jpg", "").replace(".png", "").replace("_", " ").title()
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"Postal {nombre_limpio}"},
                "unit_amount": precio_unitario
            },
            "quantity": 1
        })

    success_params = f"?codigo={codigo}&postales_json={json.dumps(postales)}"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success" + success_params,
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "codigo": codigo,
                "tipo": "postales",
                "productos_json": json.dumps([
                    {"producto": p, "cantidad": 1} for p in postales
                ])
            }
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"❌ Error creando sesión de Stripe: {e}", 500

@app.route('/descargar_postales', methods=['POST'])
def descargar_postales():
    postales_json = request.form.get("postales_json")
    if not postales_json:
        return "No se recibieron postales", 400

    try:
        postales = json.loads(postales_json)
    except:
        return "Formato de datos inválido", 400

    import zipfile
    from flask import send_file

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for p in postales:
            p_path = os.path.join(BASE, "static", "postales_generadas", p)
            if os.path.exists(p_path):
                zip_file.write(p_path, arcname=p)
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='postales_seleccionadas.zip'
    )
@app.route('/pagar_paquete_cinco', methods=['POST'])
def pagar_paquete_cinco():
    codigo = request.form.get("codigo")
    postales_json = request.form.get("postales_json")

    if not codigo or not postales_json:
        return "❌ Faltan datos", 400

    try:
        postales = json.loads(postales_json)
    except:
        return "❌ Error en formato de postales", 400

    if len(postales) != 5:
        return "❌ Deben ser exactamente 5 postales", 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Paquete 5 postales ({codigo})"},
                    "unit_amount": 500
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"https://postales-online.onrender.com/success?codigo={codigo}&postales_json={json.dumps(postales)}",
            cancel_url="https://postales-online.onrender.com/cancel"
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"❌ Error creando pago: {e}", 500
# Agregar ruta para pagar camisetas con tallas y cantidad
@app.route('/pagar_camisetas', methods=['POST'])
def pagar_camisetas():
    camisetas_seleccionadas = request.form.getlist("camiseta")
    if not camisetas_seleccionadas:
        return "<h2 style='color:red'>❌ No se recibieron camisetas</h2>", 400

    productos = []
    for camiseta in camisetas_seleccionadas:
        talla = request.form.get(f"talla_{camiseta}", "")
        cantidad = int(request.form.get(f"cantidad_{camiseta}", 0))
        if cantidad > 0:
            productos.append({
                "producto": camiseta,
                "cantidad": cantidad,
                "talla": talla
            })

    if not productos:
        return "<h2 style='color:red'>❌ No hay camisetas válidas</h2>", 400

    line_items = []
    for p in productos:
        nombre_limpio = p['producto'].replace(".jpg", "").replace(".png", "").replace("_", " ").title()
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": f"{nombre_limpio} - Talla {p['talla']}"
                },
                "unit_amount": 150  # 15.00 €
            },
            "quantity": p['cantidad']
        })

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url="https://postales-online.onrender.com/success",
        cancel_url="https://postales-online.onrender.com/cancel",
        metadata={
            "tipo": "camisetas",
            "productos_json": json.dumps(productos)
        }
    )
    return redirect(session.url, code=303)
@app.route('/pagar_productos_seleccionados', methods=['POST'])
def pagar_productos_seleccionados():
    email = request.form.get("email", "anonimo@postales.com")
    nombre = request.form.get("nombre", "")
    direccion = request.form.get("direccion", "")
    telefono = request.form.get("telefono", "")
    codigo = request.form.get("codigo", "")

    productos_json = request.form.get("productos_json")
    if not productos_json:
        return "❌ No se seleccionó ningún producto", 400

    try:
        productos_dict = json.loads(productos_json)
    except Exception as e:
        return f"❌ Formato de productos inválido: {e}", 400

    productos = []

    # 🔸 Vinos
    for vino, cantidad in productos_dict.get("vinos", {}).items():
        productos.append({"producto": vino, "cantidad": cantidad})

    # 🔸 Camisetas
    for c in productos_dict.get("camisetas", []):
        productos.append({
            "producto": c["nombre"],
            "cantidad": c["cantidad"],
            "talla": c["talla"]
        })

    # 🔸 Postales
    for p in productos_dict.get("postales", []):
        productos.append({"producto": p, "cantidad": 1})

    if not productos:
        return "❌ No se seleccionó ningún producto válido", 400

    precios_vino = {
        "vino_tinto.jpg": 120,
        "vino_rosado.jpg": 110,
        "vino_blanco.jpg": 100
    }

    line_items = []
    for p in productos:
        nombre = p.get("producto", "")
        cantidad = int(p.get("cantidad", 0))
        talla = p.get("talla", None)

        if cantidad <= 0 or not nombre:
            continue

        if nombre.startswith("vino_") or "vino" in nombre.lower():
            precio = precios_vino.get(nombre, 100)
            nombre_limpio = nombre.replace(".jpg", "").replace("_", " ").title()
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Vino {nombre_limpio}"},
                    "unit_amount": precio
                },
                "quantity": cantidad
            })
        elif talla:
            nombre_limpio = nombre.replace(".jpg", "").replace(".png", "").replace("_", " ").title()
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Camiseta {nombre_limpio} (Talla {talla})"},
                    "unit_amount": 1500
                },
                "quantity": cantidad
            })
        else:
            nombre_limpio = nombre.replace(".jpg", "").replace(".png", "").replace("_", " ").title()
            precio_unitario = 300
            if len(productos_dict.get("postales", [])) == 5:
                precio_unitario = 100
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Postal {nombre_limpio}"},
                    "unit_amount": precio_unitario
                },
                "quantity": 1
            })

    if not line_items:
        return "❌ No hay productos válidos para pagar", 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success",
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "tipo": "productos",
                "correo": email,
                "direccion": direccion,
                "telefono": telefono,
                "nombre": nombre,
                "productos_json": json.dumps(productos)
            }
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"❌ Error creando sesión de Stripe: {e}", 500
@app.route('/formulario_pago', methods=['POST'])
def formulario_pago():
    codigo = request.form.get("codigo")
    productos_json = request.form.get("productos_json")

    try:
        productos = json.loads(productos_json)
    except Exception as e:
        return f"❌ Error leyendo productos: {e}", 400

    vinos = {}
    camisetas = []
    postales = []

    for p in productos:
        nombre = p.get("producto")
        cantidad = int(p.get("cantidad", 0))
        talla = p.get("talla", None)

        if not nombre or cantidad <= 0:
            continue

        if nombre.startswith("vino_"):
            vinos[nombre] = cantidad
        elif nombre.lower().endswith(".jpg") or nombre.lower().endswith(".png"):
            if talla:
                camisetas.append({"nombre": nombre, "talla": talla, "cantidad": cantidad})
            else:
                postales.append(nombre)

    productos_json_final = json.dumps({
        "vinos": vinos,
        "camisetas": camisetas,
        "postales": postales
    })

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Confirmar pedido</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background: #111; color: white; font-family: sans-serif; text-align: center; }}
            .formulario {{ max-width: 400px; margin: auto; padding: 20px; background: #222; border-radius: 12px; }}
            input, button {{ width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; font-size: 16px; }}
            button {{ background-color: #2ecc71; color: white; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <form method="POST" action="/pagar_productos_seleccionados" class="formulario">
            <h2>✅ Confirmar productos</h2>
            <input type="hidden" name="productos_json" value='{productos_json_final}'>
            <input type="hidden" name="codigo" value="{codigo}">
            <input name="nombre" placeholder="Tu nombre" required>
            <input name="direccion" placeholder="Dirección" required>
            <input name="telefono" placeholder="Teléfono" required>
            <input type="email" name="email" placeholder="Correo electrónico" required>
            <button type="submit">💳 Confirmar y pagar</button>
        </form>
    </body>
    </html>
    '''
    return render_template_string(html)
def normalizar_nombre(nombre):
    return nombre.replace(".jpg", "").replace(".png", "").replace("_", " ").title()
@app.route('/pagar_postales_directo', methods=['POST'])
def pagar_postales_directo():
    codigo = request.form.get("codigo")
    postales_json = request.form.get("postales_json")
    email = request.form.get("email", "anonimo@postales.com")

    if not codigo or not postales_json:
        return "❌ Faltan datos para procesar el pago", 400

    try:
        postales = json.loads(postales_json)
    except Exception as e:
        return f"❌ Error leyendo postales seleccionadas: {e}", 400

    if not postales:
        return "❌ No se seleccionaron postales", 400

    line_items = []
    precio_unitario = 300
    if len(postales) == 5:
        precio_unitario = 100

    for p in postales:
        nombre_limpio = normalizar_nombre(p)
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"Postal {nombre_limpio}"},
                "unit_amount": precio_unitario
            },
            "quantity": 1
        })

    success_params = f"?codigo={codigo}&postales_json={json.dumps(postales)}"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=line_items,
            mode="payment",
            success_url="https://postales-online.onrender.com/success" + success_params,
            cancel_url="https://postales-online.onrender.com/cancel",
            metadata={
                "codigo": codigo,
                "tipo": "postales",
                "productos_json": json.dumps([
                    {"producto": p, "cantidad": 1} for p in postales
                ])
            }
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"❌ Error creando sesión de Stripe: {e}", 500
@app.route('/estado_pedido/<pedido_id>')
def estado_pedido(pedido_id):
    pedidos_path = os.path.join(BASE, "pedidos.json")
    if not os.path.exists(pedidos_path):
        return f"<h2>❌ No se encontró el pedido con ID {pedido_id}</h2>", 404

    try:
        with open(pedidos_path) as f:
            pedidos = json.load(f)
    except:
        return f"<h2>⚠️ Error leyendo el archivo de pedidos</h2>", 500

    pedido = next((p for p in pedidos if p.get("id") == pedido_id), None)
    if not pedido:
        return f"<h2>❌ Pedido con ID {pedido_id} no encontrado</h2>", 404

    productos_html = ""
    for p in pedido.get("productos", []):
        nombre = normalizar_nombre(p.get("producto", ""))
        cantidad = int(p.get("cantidad", 1))
        talla = p.get("talla")
        descripcion = f"{nombre} x {cantidad}"
        if talla:
            descripcion += f" (Talla {talla})"
        productos_html += f'<div style="margin-bottom: 8px">{descripcion}</div>'

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>📦 Estado del Pedido</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background: #111; color: white; font-family: sans-serif; padding: 30px; text-align: center; }}
            .card {{ background: #222; padding: 25px; border-radius: 12px; max-width: 500px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
            .card h2 {{ color: #2ecc71; }}
            .card .producto {{ background: #333; padding: 10px; margin: 5px 0; border-radius: 6px; }}
            .info {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📦 Estado del Pedido</h2>
            <div class="info">ID del pedido: <code>{pedido_id}</code></div>
            <div class="info">Nombre: {pedido.get("nombre", "")}</div>
            <div class="info">Correo: {pedido.get("correo", "")}</div>
            <div class="info">Dirección: {pedido.get("direccion", "")}</div>
            <div class="info">Teléfono: {pedido.get("telefono", "")}</div>
            <h3>🛍 Productos</h3>
            {productos_html}
            <div class="info">Estado: <b>🕓 En proceso</b></div>
            <div style="margin-top: 20px;"><a href="/" style="color:#2ecc71">↩️ Volver al inicio</a></div>
        </div>
    </body>
    </html>
    '''

@app.route('/pedido')
def ver_pedido():
    pedido_id = request.args.get("id", "").strip()
    pedidos_path = os.path.join(BASE, "pedidos.json")

    if not os.path.exists(pedidos_path):
        return "<h2>No hay pedidos registrados</h2>"

    try:
        with open(pedidos_path) as f:
            pedidos = json.load(f)
    except Exception as e:
        return f"<h2>Error leyendo pedidos:</h2><pre>{str(e)}</pre>"

    pedido = next((p for p in pedidos if p.get("id") == pedido_id), None)
    if not pedido:
        return f"<h2>❌ Pedido con ID <code>{pedido_id}</code> no encontrado</h2>"

    productos_html = ""
    for p in pedido.get("productos", []):
        nombre = p.get("producto", "")
        cantidad = p.get("cantidad", 1)
        talla = p.get("talla", None)
        desc = f"{nombre} x{cantidad}"
        if talla:
            desc += f" (Talla {talla})"
        productos_html += f"<li>{desc}</li>"

    return f'''
    <html>
    <head>
        <meta charset="utf-8">
        <title>Pedido {pedido_id}</title>
        <style>
            body {{ background: #111; color: white; font-family: sans-serif; text-align: center; padding: 20px; }}
            .card {{ background: #222; border-radius: 10px; padding: 20px; max-width: 500px; margin: auto; }}
            ul {{ text-align: left; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🧾 Pedido #{pedido_id}</h2>
            <p><b>Estado:</b> {pedido.get("estado")}</p>
            <p><b>Nombre:</b> {pedido.get("nombre")}</p>
            <p><b>Dirección:</b> {pedido.get("direccion")}</p>
            <p><b>Correo:</b> {pedido.get("correo")}</p>
            <p><b>Teléfono:</b> {pedido.get("telefono")}</p>
            <p><b>Fecha:</b> {pedido.get("fecha")}</p>
            <h3>🛍 Productos:</h3>
            <ul>{productos_html}</ul>
            <p><a href="/">↩️ Volver al inicio</a></p>
        </div>
    </body>
    </html>
    '''
@app.route('/buscar_pedido')
def buscar_pedido():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Buscar Pedido</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                background-color: #111;
                color: white;
                font-family: sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .card {{
                background-color: #222;
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 0 10px rgba(255,255,255,0.05);
            }}
            input, button {{
                padding: 12px;
                margin: 10px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }}
            input {{ background: #333; color: white; }}
            button {{ background: #2ecc71; color: white; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🔎 Busca tu Pedido</h2>
            <form method="GET" action="/ver_pedido_redirect">
                <input name="id" placeholder="Ingresa tu número de pedido" required />
                <br>
                <button type="submit">📦 Ver Estado</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/ver_pedido_redirect')
def ver_pedido_redirect():
    pedido_id = request.args.get("id", "").strip()
    return redirect(f"/ver_pedido/{pedido_id}")
@app.route('/actualizar_estado_pedido', methods=['POST'])
def actualizar_estado_pedido():
    data = request.get_json()
    pedido_id = data.get("id")
    nuevo_estado = data.get("estado")

    pedidos_path = os.path.join(BASE, "pedidos.json")
    if not os.path.exists(pedidos_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    try:
        with open(pedidos_path) as f:
            pedidos = json.load(f)
    except:
        return jsonify({"error": "Error leyendo pedidos"}), 500

    for p in pedidos:
        if p.get("id") == pedido_id:
            p["estado"] = nuevo_estado

    with open(pedidos_path, "w") as f:
        json.dump(pedidos, f, indent=2)

    return jsonify({"status": "ok"})
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)