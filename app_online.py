import os
import subprocess
from flask import Flask, request, send_from_directory, jsonify, redirect, render_template_string
from PIL import Image
from fpdf import FPDF

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_GALERIAS = os.path.join(BASE, "galerias")
CARPETA_CLIENTE = os.path.join(CARPETA_GALERIAS, "cliente123")
os.makedirs(CARPETA_CLIENTE, exist_ok=True)
cola_postales = []

SUMATRA = os.path.join(BASE, "SumatraPDF.exe")

def imprimir_postal(path_pdf):
    try:
        if os.path.exists(SUMATRA):
            subprocess.run([SUMATRA, '-print-to-default', '-silent', path_pdf])
    except Exception as e:
        print("❌ Error imprimiendo:", e)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Postcard Search</title>
        <style>
            html, body {
                margin: 0; padding: 0;
                height: 100vh;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }
            video#bgVideo {
                position: fixed;
                top: 0; left: 0;
                min-width: 100%; min-height: 100%;
                object-fit: cover;
                z-index: -1;
            }
            .contenedor {
                background-color: rgba(255,255,255,0.8);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                width: 90%;
                max-width: 400px;
                margin: 20vh auto;
            }
            input, button {
                width: 100%;
                padding: 12px;
                font-size: 18px;
                margin-top: 10px;
                border: none;
                border-radius: 6px;
            }
            button {
                background: black;
                color: white;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <video autoplay muted loop id='bgVideo'>
            <source src='/static/douro_sunset.mp4' type='video/mp4'>
        </video>
        <div class='contenedor'>
            <h2>🔍 Search your Postcard</h2>
            <form action='/search' method='get'>
                <input type='text' name='codigo' placeholder='Ex: abc123' required />
                <button type='submit'>Search</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/search')
def buscar():
    codigo = request.args.get("codigo", "").strip()
    return redirect(f"/view_image/{codigo}")

@app.route('/view_image/<codigo>')
def ver_imagen(codigo):
    ruta_img = f"/galeria/cliente123/imagen_{codigo}.jpg"
    ruta_postal = f"/galeria/cliente123/postal_{codigo}.jpg"
    path_img = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    path_postal = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")

    imagen_existe = os.path.exists(path_img)
    postal_existe = os.path.exists(path_postal)

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Postcard {codigo}</title>
        <style>
            body {{ font-family: Arial; background: #f4f4f4; padding: 40px; text-align: center; }}
            img {{ max-width: 400px; margin: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.2); }}
            .error {{ color: red; font-weight: bold; }}
            .back {{ margin-top: 30px; display: inline-block; padding: 10px 20px; background: #007bff; color: white; border-radius: 6px; text-decoration: none; }}
            .store {{ margin-top: 40px; }}
            #cartIcon {{ position: fixed; top: 20px; right: 20px; background: #333; color: white; padding: 10px 20px; border-radius: 30px; cursor: pointer; z-index: 999; }}
            #cartPanel {{ position: fixed; top: 0; right: -400px; width: 300px; height: 100%; background: white; box-shadow: -2px 0 10px rgba(0,0,0,0.2); padding: 20px; transition: right 0.3s ease; z-index: 998; overflow-y: auto; }}
            #cartPanel.active {{ right: 0; }}
            .checkout {{ margin-top: 20px; }}
            .checkout button {{ width: 100%; padding: 10px; margin-top: 10px; }}
        </style>
        <script>
            let cartItems = [];

            function toggleCart() {{
                document.getElementById('cartPanel').classList.toggle('active');
                renderCart();
            }}

            function addToCart() {{
                const product = document.getElementById('product').value;
                const quantity = parseInt(document.getElementById('quantity').value);
                cartItems.push({{ product, quantity }});
                renderCart();
                alert('Product added to cart!');
            }}

            function renderCart() {{
                const panel = document.getElementById('cartPanel');
                let html = '<h3>Your Cart</h3>';
                if (cartItems.length === 0) {{
                    html += '<p>No items yet.</p>';
                }} else {{
                    html += '<ul>' + cartItems.map(item => `<li>${{item.quantity}}x ${{item.product}}</li>`).join('') + '</ul>';
                }}
                html += `
                <div class='checkout'>
                    <button onclick="alert('🟦 Simulando pago con Stripe')">Pay with Stripe</button>
                    <button onclick="alert('🟨 Simulando pago con PayPal')">Pay with PayPal</button>
                </div>`;
                panel.innerHTML = html;
            }}
        </script>
    </head>
    <body>
        <div id='cartIcon' onclick='toggleCart()'>🛒 Cart</div>
        <div id='cartPanel'></div>

        <h2>📸 Your Postcard & Original</h2>
        {"<img src='" + ruta_img + "' alt='Original Photo'>" if imagen_existe else "<p class='error'>❌ Original photo not found.</p>"}
        {"<img src='" + ruta_postal + "' alt='Postcard'>" if postal_existe else "<p class='error'>❌ Postcard not generated yet.</p>"}

        <br><a class='back' href='/'>← Back</a>

        <div class='store'>
            <h3>🛍️ Products inspired by your photo</h3>
            <form onsubmit='event.preventDefault(); addToCart();'>
                <select id='product'>
                    <option>T-shirt - White (Men)</option>
                    <option>T-shirt - Black (Women)</option>
                    <option>Mug - Custom Photo</option>
                    <option>Cap - Embroidered</option>
                </select>
                <br><br>
                <input type='number' id='quantity' value='1' min='1' style='padding:10px; width:100px;'>
                <br><br>
                <button type='submit'>Add to Cart</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route('/subir_postal', methods=['POST'])
def subir_postal():
    codigo = request.form.get("codigo")
    imagen = request.files.get("imagen")
    if not codigo or not imagen:
        return "❌ Código o imagen faltante", 400
    ruta_img = os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")
    imagen.save(ruta_img)
    ruta_pdf = insertar_foto_en_postal(codigo)
    if ruta_pdf and os.path.exists(ruta_pdf):
        imprimir_postal(ruta_pdf)
    if codigo not in cola_postales:
        cola_postales.append(codigo)
    return "✅ Imagen subida correctamente", 200

@app.route('/nuevas_postales')
def nuevas_postales():
    if cola_postales:
        codigo = cola_postales.pop(0)
        return jsonify({"codigo": codigo})
    return jsonify({"codigo": None})

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

def insertar_foto_en_postal(codigo):
    try:
        base = Image.open(os.path.join(BASE, "static", "plantilla_postal.jpg")).convert("RGB")
        foto = Image.open(os.path.join(CARPETA_CLIENTE, f"imagen_{codigo}.jpg")).convert("RGB")
        foto = foto.resize((430, 330))
        base.paste(foto, (90, 95))
        salida = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.jpg")
        base.save(salida)

        pdf = FPDF(unit="cm", format="A4")
        pdf.add_page()
        pdf.image(salida, x=5, y=5, w=10)
        ruta_pdf = os.path.join(CARPETA_CLIENTE, f"postal_{codigo}.pdf")
        pdf.output(ruta_pdf)
        return ruta_pdf
    except Exception as e:
        print(f"❌ Error generando postal: {e}")
        return None

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
