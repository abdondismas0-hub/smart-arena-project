import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- CONFIGURATION ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siri_yangu_ya_duka_123')
PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'

# --- DATA FUNCTIONS ---
def load_data(file_name):
    """Hupakia data bila kuleta error."""
    if not os.path.exists(file_name):
        return [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except:
        return [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}

def save_data(data, file_name):
    """Huhifadhi data."""
    try:
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def get_next_id(items):
    if not items: return 1
    # Hakikisha tunapata ID hata kama items ni dict au list
    if isinstance(items, dict): items = items.get('products', [])
    return max([i.get('id', 0) for i in items]) + 1

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
    # Hakikisha tunatuma data sahihi kwa template
    return render_template('index.html', 
                         products=data.get('products', []), 
                         posts=data.get('posts', []))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    data = load_data(PRODUCTS_FILE)
    products = data.get('products', [])
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return "Bidhaa haikupatikana", 404

    if request.method == 'POST':
        orders = load_data(ORDERS_FILE)
        if not isinstance(orders, list): orders = []
        
        new_order = {
            'id': get_next_id(orders),
            'product_name': product['name'],
            'customer': request.form.get('customer_name'),
            'phone': request.form.get('phone'),
            'status': 'Pending',
            'date': str(datetime.datetime.now())
        }
        orders.append(new_order)
        save_data(orders, ORDERS_FILE)
        flash('Agizo limetumwa!', 'success')
        return redirect(url_for('smart_arena_home'))

    # HAPA: Jina la faili lazima liwe 'product_details.html'
    return render_template('product_details.html', product=product)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '12345':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Kosea!', 'error')
    
    # HAPA: Jina la faili lazima liwe 'admin_login.html'
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data(PRODUCTS_FILE)
    orders = load_data(ORDERS_FILE)
    if not isinstance(orders, list): orders = []

    # HAPA: Jina la faili lazima liwe 'admin.html'
    return render_template('admin.html', 
                         products=data.get('products', []), 
                         orders=orders,
                         posts=data.get('posts', []),
                         order_summary={'total': len(orders)})

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('smart_arena_home'))

if __name__ == '__main__':
    app.run(debug=True)
