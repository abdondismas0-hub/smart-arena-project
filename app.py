import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- CONFIGURATION ---
app = Flask(__name__)
# Neno la siri: admin / 12345
app.secret_key = os.environ.get('SECRET_KEY', 'siri_yangu_ya_duka_123')

# Majina ya faili za Data
PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'

# --- DATA FUNCTIONS ---
def load_data(file_name):
    """Hupakia data bila kuleta error. Inarudisha muundo sahihi."""
    default_data = [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}
    
    if not os.path.exists(file_name):
        return default_data
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Hakikisha data ina muundo sahihi
            if file_name == ORDERS_FILE and not isinstance(data, list): return []
            if file_name == PRODUCTS_FILE and not isinstance(data, dict): return default_data
            return data
    except:
        return default_data

def save_data(data, file_name):
    """Huhifadhi data."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def get_next_id(items):
    # Logic salama ya kupata ID mpya
    if not items: return 1
    if isinstance(items, dict): items = items.get('products', [])
    if not items: return 1
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
            'product_name': product.get('name', 'Unknown'),
            'price': product.get('price', 0),
            'customer_name': request.form.get('customer_name'),
            'phone': request.form.get('phone'),
            'status': 'Pending',
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        orders.append(new_order)
        save_data(orders, ORDERS_FILE)
        flash('Agizo limetumwa kikamilifu!', 'success')
        return redirect(url_for('smart_arena_home'))

    # MUHIMU: Hapa tunatumia jina 'product_detail.html' (bila 's') kama ilivyo kwenye GitHub yako
    # Kama utabadilisha jina la faili, badilisha na hapa.
    try:
        return render_template('product_detail.html', product=product)
    except:
        # Fallback ikiwa jina lina 's'
        return render_template('product_details.html', product=product)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '12345':
            session['logged_in'] = True
            flash('Karibu Admin', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Umekosea jina au neno la siri!', 'error')
    
    # MUHIMU: Tunajaribu majina yote mawili yanayowezekana ili kuepuka error
    try:
        return render_template('admin_login.html')
    except:
        return render_template('add_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data(PRODUCTS_FILE)
    orders = load_data(ORDERS_FILE)
    
    # Hakikisha tunapitisha vigezo vyote vinavyohitajika na admin.html
    return render_template('admin.html', 
                         products=data.get('products', []), 
                         orders=orders,
                         posts=data.get('posts', []),
                         order_summary={
                             'total_orders': len(orders),
                             'pending': sum(1 for o in orders if o.get('status') == 'Pending'),
                             'delivered': sum(1 for o in orders if o.get('status') == 'Delivered')
                         })

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('smart_arena_home'))

# Hii inahitajika kwa routes za kuongeza bidhaa (kama unazo kwenye template)
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
            'image_url': request.form.get('image_url') or "https://placehold.co/400"
        }
        products.append(new_product)
        data['products'] = products
        save_data(data, PRODUCTS_FILE)
        flash('Bidhaa imeongezwa', 'success')
        return redirect(url_for('admin_dashboard'))

    # Jaribu majina yote mawili ya template
    try:
        return render_template('add_product.html')
    except:
        return render_template('add_edit_product.html')

# --- CONFIG KWA GUNICORN ---
if __name__ == '__main__':
    app.run(debug=True)
