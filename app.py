# -*- coding: utf-8 -*-
# Faili: app.py
# Logic ya nyuma (Backend Logic) ya Smart Arena E-commerce
# TOLEO KAMILI NA SALAMA KWA DEPLOYMENT YA RENDER/GUNICORN NA JSON SALAMA

import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- UTILITY FUNCTIONS ---

PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'

def load_data(file_name):
    """Hupakia data kutoka JSON file kwa usalama, inarejesha muundo tupu ikiwa kuna hitilafu."""
    try:
        # Jaribu kufungua na kusoma faili
        with open(file_name, 'r', encoding='utf-8') as f:
            # Soma yaliyomo yote ya faili
            content = f.read()
            # Ikiwa faili ni tupu, rudisha muundo salama wa kuanzia
            if not content:
                raise ValueError("Faili ni tupu.")
            # Jaribu kuparsing yaliyomo kama JSON
            return json.loads(content)
    except (FileNotFoundError):
        # Ikiwa faili halipo, rudisha muundo wa kuanzia
        print(f"INFO: {file_name} haipatikani. Inarejesha muundo salama.")
    except (json.JSONDecodeError, ValueError) as e:
        # Ikiwa kuna kosa la muundo wa JSON au faili ni tupu
        print(f"WARNING: Kosa la JSON Decode kwenye {file_name}: {e}. Inarejesha muundo salama.")
    except Exception as e:
        # Hitilafu nyingine zozote
        print(f"ERROR: Hitilafu isiyotarajiwa kwenye {file_name}: {e}. Inarejesha muundo salama.")
    
    # Rejesha muundo wa data tupu sahihi kwa kila faili
    if file_name == PRODUCTS_FILE:
        return {'products': [], 'posts': []}
    return []

def save_data(data, file_name):
    """Huhifadhi data kwenye JSON file kwa usalama."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Ilishindwa kuhifadhi data kwenye {file_name}: {e}")

def get_next_id(data_list):
    """Hutafuta ID inayofuata kwa ajili ya bidhaa/maagizo mapya."""
    if not data_list:
        return 1
    return max(item.get('id', 0) for item in data_list if isinstance(item, dict) and 'id' in item) + 1

def get_product_by_id(product_id):
    """Hutafuta bidhaa kwa ID yake."""
    data = load_data(PRODUCTS_FILE)
    for product in data.get('products', []):
        if product.get('id') == product_id:
            return product
    return None

def authenticate(username, password):
    """Mfumo wa uthibitisho rahisi kwa Admin."""
    return username == "admin" and password == "12345"

# --- FLASK APP INITIALIZATION ---

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_strong_secret_key_1234567890') 
app.config['SESSION_COOKIE_SECURE'] = True 

# --- INITIALIZATION YA DATA ---
load_data(PRODUCTS_FILE)
load_data(ORDERS_FILE)

# --- CUSTOM FILTERS (Inaongeza format_currency) ---
def format_currency_filter(value):
    """Huongeza koma (,) kwenye namba na kuongeza ' TZS'."""
    try:
        value = int(value) 
        formatted_value = "{:,.0f}".format(value)
        # Badilisha koma za kiingereza (,) na nukta za Kitanzania (.) na kinyume chake
        formatted_value = formatted_value.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted_value} TZS"
    except (TypeError, ValueError):
        return str(value) # Rudisha kama string ikiwa imeshindwa

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
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """Dashboard ya Admin: Huonyesha bidhaa na maagizo."""
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
