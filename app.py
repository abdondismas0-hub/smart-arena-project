# -*- coding: utf-8 -*-
import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- CONFIGURATION ---
app = Flask(__name__)
# Neno la siri: admin / 12345
app.secret_key = os.environ.get('SECRET_KEY', 'siri_yangu_ya_duka_123')
PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"

# --- DATA FUNCTIONS ---
def load_data(file_name):
    """Hupakia data kwa usalama."""
    default = [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}
    if not os.path.exists(file_name): return default
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read()
            return json.loads(content) if content else default
    except:
        return default

def save_data(data, file_name):
    """Huhifadhi data."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def get_next_id(items):
    # Logic ya kupata ID mpya
    if isinstance(items, dict): items = items.get('products', [])
    if not items: return 1
    return max([i.get('id', 0) for i in items]) + 1

# --- HELPER KWA TEMPLATES (Hapa ndipo tunatua tatizo lako) ---
def smart_render(template_name_1, template_name_2, **kwargs):
    """Inajaribu template ya kwanza, ikishindwa inajaribu ya pili."""
    try:
        return render_template(template_name_1, **kwargs)
    except Exception:
        # Jaribu jina la pili (backup)
        return render_template(template_name_2, **kwargs)

# --- FILTERS ---
@app.template_filter('format_currency')
def format_currency(value):
    try:
        return "{:,.0f} TZS".format(int(value))
    except:
        return "0 TZS"

# --- ROUTES ---

@app.route('/')
def smart_arena_home():
    data = load_data(PRODUCTS_FILE)
    return render_template('index.html', 
                         products=data.get('products', []), 
                         posts=data.get('posts', []))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    data = load_data(PRODUCTS_FILE)
    products = data.get('products', [])
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash("Bidhaa haikupatikana.", 'error')
        return redirect(url_for('smart_arena_home'))

    if request.method == 'POST':
        orders = load_data(ORDERS_FILE)
        if not isinstance(orders, list): orders = []
        
        new_order = {
            'id': get_next_id(orders),
            'product_name': product.get('name', 'Bidhaa'),
            'price': product.get('price', 0),
            'customer_name': request.form.get('customer_name'),
            'phone': request.form.get('phone'),
            'status': 'Pending',
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        orders.append(new_order)
        save_data(orders, ORDERS_FILE)
        flash('Agizo limetumwa!', 'success')
        return redirect(url_for('smart_arena_home'))

    # UJANJA: Inajaribu 'product_details.html' NA 'product_detail.html'
    return smart_render('product_details.html', 'product_detail.html', product=product)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Karibu Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Kosea jina au neno la siri!', 'error')
    
    # UJANJA: Inajaribu 'admin_login.html' NA 'add_login.html'
    return smart_render('admin_login.html', 'add_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data(PRODUCTS_FILE)
    orders = load_data(ORDERS_FILE)
    if not isinstance(orders, list): orders = []

    order_summary = {
        'total': len(orders),
        'pending': len([o for o in orders if o.get('status') == 'Pending']),
        'delivered': len([o for o in orders if o.get('status') == 'Delivered'])
    }

    return render_template('admin.html', 
                         products=data.get('products', []), 
                         orders=orders, 
                         posts=data.get('posts', []),
                         order_summary=order_summary)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Umetoka salama.', 'success')
    return redirect(url_for('smart_arena_home'))

# --- ROUTES ZA KUONGEZA/KUHARIRI ---
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        data = load_data(PRODUCTS_FILE)
        products = data.get('products', [])
        new_product = {
            'id': get_next_id(products),
            'name': request.form.get('name'),
            'price': float(request.form.get('price', 0)),
            'category': request.form.get('category'),
            'description': request.form.get('description'),
            'image_url': request.form.get('image_url')
        }
        products.append(new_product)
        data['products'] = products
        save_data(data, PRODUCTS_FILE)
        flash('Bidhaa imeongezwa', 'success')
        return redirect(url_for('admin_dashboard'))

    return smart_render('add_product.html', 'add_edit_product.html')

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    data = load_data(PRODUCTS_FILE)
    data['products'] = [p for p in data.get('products', []) if p.get('id') != product_id]
    save_data(data, PRODUCTS_FILE)
    flash('Bidhaa imefutwa', 'success')
    return redirect(url_for('admin_dashboard'))

# --- APP RUNNER ---
if __name__ == '__main__':
    app.run(debug=True)
