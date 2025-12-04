# -*- coding: utf-8 -*-
# Faili: app.py
# Logic ya nyuma (Backend Logic) ya Smart Arena E-commerce
# MAREKEBISHO: Kuhakikisha majina ya template ni sahihi na load_data ni imara.

import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- UTILITY CONSTANTS AND FUNCTIONS ---

PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345" 

def load_data(file_name):
    """Hupakia data kutoka JSON file kwa usalama, ikirudisha muundo wa default ({} au []) ikiwa kuna kosa."""
    # Muundo wa default: product.json ni dictionary, orders.json ni list
    default_structure = [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}
    
    try:
        if not os.path.exists(file_name):
            print(f"INFO: {file_name} haipatikani. Inarejesha muundo salama.")
            return default_structure
            
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"INFO: {file_name} ni tupu. Inarejesha muundo salama.")
                return default_structure
            
            data = json.loads(content)
            
            # Kufanya uhakika wa muundo
            if file_name == ORDERS_FILE and not isinstance(data, list):
                print(f"WARNING: {ORDERS_FILE} haikurudisha List. Inarudisha default List.")
                return []
            if file_name == PRODUCTS_FILE and not isinstance(data, dict):
                print(f"WARNING: {PRODUCTS_FILE} haikurudisha Dictionary. Inarudisha default Dictionary.")
                return {'products': [], 'posts': []}
                
            return data
            
    except (json.JSONDecodeError, ValueError) as e:
        print(f"CRITICAL ERROR: Kosa la JSON Decode kwenye {file_name}: {e}. Inarejesha muundo salama.")
    except Exception as e:
        print(f"ERROR: Hitilafu isiyotarajiwa kwenye {file_name}: {e}.")
    
    return default_structure

def save_data(data, file_name):
    """Huhifadhi data kwenye JSON file kwa usalama."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Ilishindwa kuhifadhi data kwenye {file_name}: {e}")

# Function rahisi ya kupata ID mpya
def get_next_id(items):
    # Inaboreshwa ili kufanya kazi kwa dictionaries/lists zinazopokelewa
    if isinstance(items, dict) and 'products' in items:
        items = items['products'] 
    
    return max([item.get('id', 0) for item in items], default=0) + 1

def get_product_by_id(product_id):
    """Hutafuta bidhaa kwa ID yake."""
    data = load_data(PRODUCTS_FILE)
    product_id_int = int(product_id) if isinstance(product_id, str) and product_id.isdigit() else product_id
    for product in data.get('products', []):
        if product.get('id') == product_id_int:
            return product
    return None

def authenticate(username, password):
    """Mfumo wa uthibitisho rahisi kwa Admin."""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

# --- FLASK APP INITIALIZATION ---

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static') 
            
app.secret_key = os.environ.get('SECRET_KEY', 'default_strong_secret_key_1234567890') 
app.config['SESSION_COOKIE_SECURE'] = True 
app.logger.setLevel('DEBUG') 

# --- CUSTOM FILTERS ---
def format_currency_filter(value):
    """Huongeza koma (,) kwenye namba na kuongeza ' TZS'."""
    try:
        value = int(value) 
        formatted_value = "{:,.0f}".format(value)
        return f"{formatted_value} TZS"
    except (TypeError, ValueError):
        return str(value) 

app.jinja_env.filters['format_currency'] = format_currency_filter

# --- ROUTES ZA MTUMIAJI (PUBLIC ROUTES) ---

@app.route('/')
def smart_arena_home():
    """Ukurasa wa Nyumbani."""
    data = load_data(PRODUCTS_FILE)
    return render_template('index.html', 
                           products=data.get('products', []),
                           posts=data.get('posts', []))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    """Ukurasa wa Maelezo ya Bidhaa. (Inatumia product_detail.html)"""
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

    # Hapa tunatumia product_detail.html
    return render_template('product_detail.html', product=product)

# --- ROUTES ZA ADMIN (ADMIN ROUTES) ---

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Ukurasa wa Kuingia kwa Admin. (Inatumia admin_login.html)"""
    if session.get('logged_in'): 
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if authenticate(username, password):
            session['logged_in'] = True 
            flash('Karibu Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Jina au Neno la Siri Sio Sahihi.', 'error')
    
    # Hapa tunatumia admin_login.html
    return render_template('admin_login.html') 

@app.route('/admin')
def admin_dashboard():
    """Dashboard ya Admin: Huonyesha bidhaa na maagizo. (Inatumia admin.html)"""
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

    # Hapa tunatumia admin.html
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


# --- INAONGEZA APPLICATION KWA GUNICORN ---
application = app

# --- KUANZA APP (KWA MAENDELEO TU) ---
if __name__ == '__main__':
    app.run(debug=True)
