# -*- coding: utf-8 -*-
# Faili: app.py
# Logic ya nyuma (Backend Logic) ya Smart Arena E-commerce
# TOLEO KAMILI NA SALAMA KWA DEPLOYMENT YA RENDER/GUNICORN

import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- UTILITY FUNCTIONS ---

PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'

def load_data(file_name):
    """Hupakia data kutoka JSON file, inarejesha dictionary au list tupu ikiwa faili lina matatizo."""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Ikiwa kuna tatizo, rudisha muundo wa data tupu sahihi
        print(f"INFO: Failed to load {file_name}. Returning safe empty structure.")
        if file_name == PRODUCTS_FILE:
            return {'products': [], 'posts': []}
        return []

def save_data(data, file_name):
    """Huhifadhi data kwenye JSON file."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Failed to save data to {file_name}: {e}")

def get_next_id(data_list):
    """Hutafuta ID inayofuata kwa ajili ya bidhaa/maagizo mapya."""
    if not data_list:
        return 1
    # Huhesabu ID kubwa zaidi kutoka kwenye orodha
    return max(item.get('id', 0) for item in data_list if isinstance(item, dict) and 'id' in item) + 1

def get_product_by_id(product_id):
    """Hutafuta bidhaa kwa ID yake."""
    data = load_data(PRODUCTS_FILE)
    # Tafuta bidhaa kwa uhakika
    for product in data.get('products', []):
        # Hakikisha ID zinalinganishwa kwa aina (int)
        if product.get('id') == product_id:
            return product
    return None

def authenticate(username, password):
    """Mfumo wa uthibitisho rahisi kwa Admin."""
    return username == "admin" and password == "12345"

# --- FLASK APP INITIALIZATION ---

app = Flask(__name__)
# SECRET_KEY NI MUHIMU KWA FLASK SESSION. Inafanya kazi kwenye Render.
app.secret_key = os.environ.get('SECRET_KEY', 'default_strong_secret_key_1234567890') 
app.config['SESSION_COOKIE_SECURE'] = True # Muhimu kwa HTTPS kwenye Render

# --- INITIALIZATION YA DATA (Kufanya data ianze kupakiwa mara moja) ---
load_data(PRODUCTS_FILE)
load_data(ORDERS_FILE)

# --- CUSTOM FILTERS (Inatatua UndefinedError kwenye templates) ---
def format_currency_filter(value):
    """Huongeza koma (,) kwenye namba na kuongeza ' TZS'."""
    try:
        value = int(value) # Hakikisha ni namba kamili
        # Fomati namba kwa koma (e.g., 1,000,000)
        formatted_value = "{:,.0f}".format(value)
        # Badilisha koma za kiingereza (,) na nukta za Kitanzania (.) na kinyume chake
        formatted_value = formatted_value.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted_value} TZS"
    except (TypeError, ValueError):
        return value

# KUSANIFU: Kuweka filter iweze kutumika kwenye templates zote
app.jinja_env.filters['format_currency'] = format_currency_filter


# --- ROUTES ZA MTUMIAJI (PUBLIC ROUTES) ---

@app.route('/')
def smart_arena_home():
    """Ukurasa wa Nyumbani: Huonyesha bidhaa na matangazo yote."""
    data = load_data(PRODUCTS_FILE)
    return render_template('index.html', 
                           products=data.get('products', []),
                           posts=data.get('posts', []))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    """Ukurasa wa Maelezo ya Bidhaa."""
    product = get_product_by_id(product_id) 
    
    # Hili linazuia 500 Error ikiwa bidhaa haipo
    if not product:
        flash('Bidhaa haipatikani.', 'error')
        return redirect(url_for('smart_arena_home'))

    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        phone = request.form.get('phone')

        if customer_name and phone:
            orders = load_data(ORDERS_FILE)
            if not isinstance(orders, list): orders = []

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            new_order = {
                'id': get_next_id(orders),
                'product_id': product_id,
                'product_name': product.get('name', 'N/A'),
                'price': product.get('price', 0),
                'customer_name': customer_name,
                'phone': phone,
                'status': 'Pending', 
                'date': now 
            }
            orders.append(new_order)
            save_data(orders, ORDERS_FILE)
            
            flash(f'Agizo la {product.get("name")} limewekwa! Tutakupigia simu hivi karibuni.', 'success')
            return redirect(url_for('smart_arena_home'))
        else:
            flash('Tafadhali jaza Jina Kamili na Namba ya Simu.', 'error')

    return render_template('product_details.html', product=product)

# --- ROUTES ZA ADMIN (ADMIN ROUTES) ---

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Ukurasa wa Kuingia kwa Admin."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if authenticate(username, password):
            session['logged_in'] = True 
            flash('Karibu Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Jina au Neno la Siri Sio Sahihi.', 'error')
    
    # Hili linaweza kusababisha 500 kama template admin_login.html haipo au ina kosa
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """Dashboard ya Admin: Huonyesha bidhaa na maagizo."""
    # Angalia session ya Flask - inatatua 500 error ya session
    if not session.get('logged_in'): 
        flash('Tafadhali ingia kama Admin kwanza.', 'error')
        return redirect(url_for('admin_login'))

    product_data = load_data(PRODUCTS_FILE)
    orders = load_data(ORDERS_FILE)
    
    products = product_data.get('products', [])
    posts = product_data.get('posts', [])

    if not isinstance(orders, list): orders = []

    order_summary = {
        'total_orders': len(orders),
        'pending': sum(1 for order in orders if order.get('status') == 'Pending'),
        'delivered': sum(1 for order in orders if order.get('status') == 'Delivered')
    }

    # Hii inahitaji admin.html kutumia format_currency_filter
    return render_template('admin.html', 
                           products=products, 
                           orders=orders, 
                           posts=posts, 
                           order_summary=order_summary)

@app.route('/admin/logout')
def admin_logout():
    """Admin Logout."""
    if session.get('logged_in'):
        session.pop('logged_in', None)
        flash('Umetoka Admin Dashboard salama.', 'success')
    return redirect(url_for('smart_arena_home'))
