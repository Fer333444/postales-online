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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Postcard Shop</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: #f7f7f7;
            }
            header {
                background: #000;
                color: white;
                padding: 10px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            header a {
                color: white;
                text-decoration: none;
                font-weight: bold;
            }
            .container {
                padding: 20px;
            }
            .grid {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
            }
            .product {
                background: white;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                width: 250px;
                text-align: center;
            }
            img {
                max-width: 100%;
                border-radius: 8px;
            }
            select, input {
                margin-top: 8px;
                padding: 6px;
                border-radius: 4px;
                width: 80%;
            }
            button {
                margin-top: 8px;
                padding: 10px 16px;
                background: black;
                color: white;
                border: none;
                border-radius: 6px;
                width: 80%;
            }
        </style>
        <script>
            let cart = [];

            function addToCart(name, qty, size) {
                cart.push({ name, qty, size });
                alert(name + " added to cart!");
                localStorage.setItem("cart", JSON.stringify(cart));
            }

            function loadCart() {
                return JSON.parse(localStorage.getItem("cart") || "[]");
            }
        </script>
    </head>
    <body>
        <header>
            <span>🛍️ Postcard Shop</span>
            <a href="/cart">🛒 View Cart</a>
        </header>
        <div class="container">
            <h2>👕 T-Shirts</h2>
            <div class="grid">
                {% for group in ['Men', 'Women', 'Kids'] %}
                    {% for color in ['White', 'Black'] %}
                        <div class="product">
                            <img src="/static/{{ color | lower }}_shirt.jpg" />
                            <p>{{ color }} T-Shirt ({{ group }})</p>
                            <label>Size:</label>
                            <select id="size_{{group}}{{color}}">
                                {% for s in ['XS','S','M','L','XL'] %}<option>{{s}}</option>{% endfor %}
                            </select>
                            <label>Qty:</label>
                            <input type="number" id="qty_{{group}}{{color}}" value="1" min="1"/><br>
                            <button onclick="addToCart('{{ color }} T-Shirt - {{ group }}', document.getElementById('qty_{{group}}{{color}}').value, document.getElementById('size_{{group}}{{color}}').value)">Add to Cart</button>
                        </div>
                    {% endfor %}
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/cart')
def view_cart():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Cart</title>
        <style>
            body {
                font-family: Arial;
                margin: 0;
                padding: 20px;
                background: #f0f0f0;
            }
            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h2 {
                text-align: center;
            }
            ul {
                list-style: none;
                padding: 0;
            }
            li {
                padding: 10px;
                border-bottom: 1px solid #ccc;
            }
            .buttons {
                text-align: center;
                margin-top: 20px;
            }
            .buttons button {
                margin: 0 10px;
                padding: 10px 20px;
                border: none;
                background: black;
                color: white;
                border-radius: 6px;
            }
        </style>
        <script>
            function loadCartItems() {
                const cart = JSON.parse(localStorage.getItem("cart") || "[]");
                const list = document.getElementById("cartItems");
                let html = "";
                cart.forEach(item => {
                    html += `<li>🛒 ${item.qty} × ${item.name} (${item.size})</li>`;
                });
                list.innerHTML = html;
            }

            window.onload = loadCartItems;
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Your Shopping Cart</h2>
            <ul id="cartItems"></ul>
            <div class="buttons">
                <button>Pay with Stripe</button>
                <button>Pay with PayPal</button>
            </div>
            <br><a href="/">← Back to Shop</a>
        </div>
    </body>
    </html>
    """)

@app.route('/galeria/cliente123/<archivo>')
def servir_imagen(archivo):
    return send_from_directory(CARPETA_CLIENTE, archivo)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)