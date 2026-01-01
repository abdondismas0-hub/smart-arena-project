import json
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- CONFIGURATION ---
app = Flask(__name__)
# Neno la siri: admin / 12345 (Badilisha kwa production!)
app.secret_key = os.environ.get('SECRET_KEY', 'dijorama_smart_arena_secure_key_2025')
PRODUCTS_FILE = 'product.json'
ORDERS_FILE = 'orders.json'
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"

# --- DATA FUNCTIONS (Safe Handling) ---
def load_data(file_name):
    """Hupakia data kwa usalama na kurudisha muundo sahihi."""
    default = [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}
    if not os.path.exists(file_name): return default
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read()
            return json.loads(content) if content else default
    except Exception as e:
        print(f"Error loading {file_name}: {e}")
        return default

def save_data(data, file_name):
    """Huhifadhi data kwenye faili."""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {file_name}: {e}")

def get_next_id(items):
    """Inazalisha ID mpya ya kipekee."""
    if not items: return 1
    # Hakikisha tunapata ID hata kama items ni dict au list
    if isinstance(items, dict): items = items.get('products', [])
    return max([int(i.get('id', 0)) for i in items]) + 1

# --- FILTERS ---
@app.template_filter('format_currency')
def format_currency(value):
    try:
        return "{:,.0f} TZS".format(int(value))
    except:
        return "0 TZS"

# --- AUTHENTICATION DECORATOR ---
# Hii inatumika kulinda routes za Admin
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Tafadhali ingia kama Admin kwanza.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- PUBLIC ROUTES ---

@app.route('/')
def smart_arena_home():
    """Ukurasa wa Nyumbani."""
    data = load_data(PRODUCTS_FILE)
    # Tuma pia status ya admin ili kuficha/kuonesha link
    return render_template('index.html', 
                         products=data.get('products', []), 
                         posts=data.get('posts', []),
                         is_admin=session.get('logged_in'))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    """Ukurasa wa Maelezo ya Bidhaa na Kuagiza."""
    data = load_data(PRODUCTS_FILE)
    products = data.get('products', [])
    product = next((p for p in products if int(p.get('id', 0)) == product_id), None)
    
    if not product:
        flash("Bidhaa haikupatikana.", 'error')
        return redirect(url_for('smart_arena_home'))

    if request.method == 'POST':
        # Logic ya Mfumo wa Malipo/Agizo (Simulated)
        orders = load_data(ORDERS_FILE)
        if not isinstance(orders, list): orders = []
        
        new_order = {
            'id': get_next_id(orders),
            'product_name': product.get('name', 'Bidhaa'),
            'price': product.get('price', 0),
            'customer_name': request.form.get('customer_name'),
            'phone': request.form.get('phone'),
            'status': 'Pending', # Hali ya awali ya agizo
            'payment_method': request.form.get('payment_method', 'Cash'), # Njia ya malipo
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        orders.append(new_order)
        save_data(orders, ORDERS_FILE)
        flash('Agizo limetumwa kikamilifu! Tutawasiliana nawe kwa malipo.', 'success')
        return redirect(url_for('smart_arena_home'))

    return render_template('product_details.html', product=product)

# --- ADMIN ROUTES ---

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Ukurasa wa Login kwa Admin."""
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Karibu Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Umekosea jina au neno la siri!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    """Dashibodi kuu ya Admin - Imeonekana na Admin tu."""
    data = load_data(PRODUCTS_FILE)
    orders = load_data(ORDERS_FILE)
    if not isinstance(orders, list): orders = []

    # Takwimu za haraka
    summary = {
        'products': len(data.get('products', [])),
        'orders': len(orders),
        'posts': len(data.get('posts', []))
    }

    return render_template('admin.html', 
                         products=data.get('products', []), 
                         orders=orders,
                         posts=data.get('posts', []),
                         summary=summary)

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    """Kuongeza Bidhaa Mpya."""
    if request.method == 'POST':
        try:
            data = load_data(PRODUCTS_FILE)
            products = data.get('products', [])
            
            # Picha: Tumia URL au Placeholder kama hakuna upload server
            img_url = request.form.get('image_url')
            if not img_url:
                img_url = "https://placehold.co/600x400/007bff/ffffff?text=Smart+Arena"

            new_product = {
                'id': get_next_id(products),
                'name': request.form.get('name'),
                'price': float(request.form.get('price', 0)),
                'category': request.form.get('category'),
                'description': request.form.get('description'),
                'image_url': img_url,
                'specs': request.form.get('specs') # Specifications
            }
            products.append(new_product)
            data['products'] = products
            save_data(data, PRODUCTS_FILE)
            flash('Bidhaa imeongezwa kikamilifu.', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f'Kosa: {e}', 'error')

    return render_template('add_product.html')

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Kufuta Bidhaa."""
    data = load_data(PRODUCTS_FILE)
    # Chuja bidhaa kuondoa yenye ID husika
    data['products'] = [p for p in data.get('products', []) if int(p.get('id')) != product_id]
    save_data(data, PRODUCTS_FILE)
    flash('Bidhaa imefutwa.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Umetoka salama.', 'success')
    return redirect(url_for('smart_arena_home'))

# --- APP RUNNER ---
if __name__ == '__main__':
    app.run(debug=True)
