# -*- coding: utf-8 -*-
# Faili: app.py
# Logic ya nyuma (Backend Logic) kwa Smart Arena E-commerce
# Imeandikwa kwa kutumia Flask framework
# TOLEO KAMILI LA DEPLOYMENT (GUNICORN TAYARI)

import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash

# --- UTILITY FUNCTIONS ---

PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'

def load_data(file_name):
    """
    Hupakia data kutoka JSON file. 
    Huunda faili na data ya mwanzo ikiwa halipatikani au lina makosa ya JSON.
    Hili linahakikisha programu haifi (crash) wakati wa deployment.
    """
    if not os.path.exists(file_name):
        initial_data = []
        if file_name == PRODUCTS_FILE:
            initial_data = {
                'products': [
                    {'id': 1, 'name': 'Laptop DELL Vostro', 'price': 1200000, 'description': 'Laptop yenye kasi kubwa na RAM 16GB.', 'image_url': 'https://placehold.co/400x300/3c0b0b/FFFFFF?text=DELL+Vostro'},
                    {'id': 2, 'name': 'Simu Samsung A54', 'price': 750000, 'description': 'Simu mpya yenye kamera kali na betri yenye nguvu.', 'image_url': 'https://placehold.co/400x300/083d1c/FFFFFF?text=SAMSUNG+A54'}
                ],
                'posts': [
                    {'id': 1, 'title': 'Punguzo la 20% kwa Laptops zote!', 'content': 'Ofa hii ni kwa wiki moja tu. Usikose!', 'file_url': 'https://placehold.co/600x200/520138/FFFFFF?text=OFA+KUBWA!'}
                ]
            }
        
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)
            return initial_data
        except Exception:
            # Rejesha dictionary tupu ikiwa kushindwa kuunda faili
            return {'products': [], 'posts': []} if file_name == PRODUCTS_FILE else []
            
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Rejesha dictionary tupu ikiwa faili lipo lakini lina makosa ya JSON
        return {'products': [], 'posts': []} if file_name == PRODUCTS_FILE else []
    except Exception:
        # Catch errors nyingine (kama permissions)
        return {'products': [], 'posts': []} if file_name == PRODUCTS_FILE else []

def save_data(data, file_name):
    """Huhifadhi data kwenye JSON file. Inatumia try/except kuhakikisha stability."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Failed to save data to {file_name}: {e}")
        # Hatutumi flash hapa kwa sababu saving inafanyika kwenye POST requests

def get_next_id(data_list):
    """Hutafuta ID inayofuata kwa ajili ya bidhaa/maagizo mapya."""
    if not data_list:
        return 1
    # Hakikisha 'id' inapatikana kabla ya kutafuta max
    return max(item.get('id', 0) for item in data_list if isinstance(item, dict) and 'id' in item) + 1

def get_product_by_id(product_id):
    """Hutafuta bidhaa kwa ID yake."""
    data = load_data(PRODUCTS_FILE)
    for product in data.get('products', []):
        if product.get('id') == product_id:
            return product
    return None

def authenticate(username, password):
    """Mfumo wa uthibitisho (authentication) rahisi kwa Admin."""
    return username == "admin" and password == "12345"

# --- FLASK APP INITIALIZATION ---

app = Flask(__name__)
# SECRET_KEY NI MUHIMU KWA FLASH MESSAGES
app.secret_key = 'smart_arena_super_secret_key_2025'

# Tumia dictionary rahisi kuhifadhi hali ya kuingia
ADMIN_SESSION = {}

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
    """Ukurasa wa Maelezo ya Bidhaa: Huonyesha maelezo na fomu ya agizo."""
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

            # Tumia datetime kwa tarehe (salama kuliko os.popen)
            import datetime
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
            ADMIN_SESSION['logged_in'] = True 
            flash('Karibu Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Jina au Neno la Siri Sio Sahihi.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """Dashboard ya Admin: Huonyesha bidhaa na maagizo."""
    if not ADMIN_SESSION.get('logged_in'):
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
    if ADMIN_SESSION.get('logged_in'):
        ADMIN_SESSION['logged_in'] = False
        flash('Umetoka Admin Dashboard salama.', 'success')
    return redirect(url_for('smart_arena_home'))


# --- INITALIZATION (Inafanya kazi mara moja kwenye Gunicorn) ---

# Hakikisha faili za data zinaundwa mara moja server inapoanza.
load_data(PRODUCTS_FILE)
load_data(ORDERS_FILE)
