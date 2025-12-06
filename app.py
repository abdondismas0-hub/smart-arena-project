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

# --- DATA FUNCTIONS (Ulinzi Dhidi ya JSON Isiyo Sahihi) ---
def load_data(file_name):
    """
    Hupakia data kutoka JSON file kwa usalama. 
    Inarudisha muundo wa default ({} au []) ikiwa kuna kosa au faili ni tupu.
    """
    default_structure = [] if file_name == ORDERS_FILE else {'products': [], 'posts': []}
    
    if not os.path.exists(file_name):
        return default_structure
        
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"INFO: {file_name} ni tupu.")
                return default_structure
            
            data = json.loads(content)
            
            # Ukaguzi wa muundo wa kimsingi
            if file_name == ORDERS_FILE and not isinstance(data, list):
                print(f"WARNING: {ORDERS_FILE} haikurudisha List.")
                return []
            if file_name == PRODUCTS_FILE and not isinstance(data, dict):
                print(f"WARNING: {PRODUCTS_FILE} haikurudisha Dictionary.")
                return {'products': [], 'posts': []}
                
            return data
            
    except (json.JSONDecodeError, ValueError) as e:
        # Hii ndiyo chanzo kikuu cha 500 Internal Server Error
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

def get_next_id(items):
    # Logic ya kupata ID mpya
    if isinstance(items, dict): items = items.get('products', []) 
    return max([item.get('id', 0) for item in items], default=0) + 1

# --- FILTERS ---
@app.template_filter('format_currency')
def format_currency(value):
    try:
        return "{:,.0f} TZS".format(int(value))
    except:
        return str(value)

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
            'product_name': product.get('name', 'Bidhaa Isiyojulikana'), # Salama
            'customer_name': request.form.get('customer_name'),
            'phone': request.form.get('phone'),
            'status': 'Pending',
            'date': str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        }
        orders.append(new_order)
        save_data(orders, ORDERS_FILE)
        flash('Agizo limetumwa!', 'success')
        return redirect(url_for('smart_arena_home'))

    return render_template('product_details.html', product=product)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '12345':
            session['logged_in'] = True
            flash('Karibu Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Jina au Neno la Siri Sio Sahihi.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        flash('Tafadhali ingia kama Admin kwanza.', 'error')
        return redirect(url_for('admin_login'))
    
    product_data = load_data(PRODUCTS_FILE)
    orders = load_data(ORDERS_FILE)
    
    # Hakikisha vigezo hivi ni vya aina inayofaa kabla ya kutuma kwenye template
    products = product_data.get('products', []) if isinstance(product_data, dict) else []
    posts = product_data.get('posts', []) if isinstance(product_data, dict) else []
    orders = orders if isinstance(orders, list) else []

    # Hapa ndipo Logic iliyokuwa ikifeli: inahitaji orders kuwa List safi
    order_summary = {
        'total': len(orders),
        'pending': sum(1 for order in orders if order.get('status', 'Unknown') == 'Pending'),
        'delivered': sum(1 for order in orders if order.get('status', 'Unknown') == 'Delivered')
    }

    # HAPA: Jina la faili lazima liwe 'admin.html'
    return render_template('admin.html', 
                         products=products, 
                         orders=orders,
                         posts=posts,
                         order_summary=order_summary)

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('Umetoka Admin Dashboard salama.', 'success')
    return redirect(url_for('smart_arena_home'))

if __name__ == '__main__':
    app.run(debug=True)
