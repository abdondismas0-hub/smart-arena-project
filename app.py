import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)

# TAFADHALI BADILISHA HII KWA AJILI YA USALAMA WA Mfumo
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_change_me')

# Data ya Admin (Credentials)
ADMIN_USERNAME = 'admin_smart'
ADMIN_PASSWORD = 'password_123' 

# Data ya Duka (Data Store) - Kama huna database halisi, tutatumia hizi
products = [
    {'id': 1, 'name': 'iPhone 13 Pro Max (Used)', 'price': 1850000, 'category': 'Simu Used', 'description': 'Simu safi, betri health 95%, 256GB, Grey.', 'image_url': 'https://placehold.co/400x400/000/FFF?text=iPhone+13+Pro+Max'},
    {'id': 2, 'name': 'Samsung S24 Ultra (New)', 'price': 3500000, 'category': 'Simu Mpya', 'description': 'Toleo jipya kabisa la Samsung, 512GB, Black.', 'image_url': 'https://placehold.co/400x400/000/FFF?text=Samsung+S24+Ultra'},
    {'id': 3, 'name': 'AirPods Pro (2nd Gen)', 'price': 450000, 'category': 'Accessories', 'description': 'Earphones safi, Noise Cancellation bora.', 'image_url': 'https://placehold.co/400x400/000/FFF?text=AirPods+Pro'},
    {'id': 4, 'name': 'Tecno Camon 20', 'price': 600000, 'category': 'Simu Mpya', 'description': 'Kamera kali, 8GB RAM, 128GB storage.', 'image_url': 'https://placehold.co/400x400/000/FFF?text=Tecno+Camon+20'},
]

posts = [
    {'id': 1, 'title': 'Punguzo la Bei kwa Simu Used!', 'content': 'Pata 10% discount kwa simu zote used kwa wiki hii pekee!'},
    {'id': 2, 'title': 'Accessories Mpya Zimeingia', 'content': 'Tuna stock mpya ya Smart Watches na Power Banks. Tembelea duka letu sasa.'},
]

orders = [
    {'id': 1, 'customer_name': 'Jane Doe', 'product_name': 'iPhone 13 Pro Max (Used)', 'quantity': 1, 'phone': '0712345678', 'status': 'Pending'},
]


# =================================================================
# FUNCTIONS ZA MSAADA
# =================================================================

def get_product_by_id(product_id):
    """Kutafuta bidhaa kwa ID yake."""
    try:
        product_id = int(product_id)
        for product in products:
            if product['id'] == product_id:
                return product
    except ValueError:
        return None
    return None

def is_admin():
    """Kuangalia kama mtumiaji ame-login kama admin."""
    return session.get('logged_in')


# =================================================================
# ROUTE ZA WATUMIAJI (PUBLIC ROUTES)
# =================================================================

@app.route('/', methods=['GET', 'POST'])
def smart_arena_home():
    """Ukurasa Mkuu wa Duka - Huonyesha bidhaa na kuruhusu utafutaji."""
    search_query = request.args.get('search_query', '').lower()
    
    # Kazi ya Utafutaji
    if search_query:
        filtered_products = [p for p in products if search_query in p['name'].lower() or search_query in p['category'].lower()]
    else:
        filtered_products = products
        
    # Bidhaa Zinazoongoza (Hapa tunatumia bidhaa 4 za kwanza kama mfano)
    featured_products = products[:4]
    
    return render_template('index.html', 
                           products=filtered_products, 
                           featured_products=featured_products,
                           posts=posts,
                           current_query=search_query,
                           is_admin=is_admin())

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    """Ukurasa wa Maelezo ya Bidhaa na Fomu ya Agizo."""
    product = get_product_by_id(product_id)
    
    if not product:
        flash('Bidhaa haikupatikana.', 'error')
        return redirect(url_for('smart_arena_home'))

    if request.method == 'POST':
        # Kuthibitisha Agizo
        customer_name = request.form.get('customer_name')
        phone = request.form.get('phone')
        
        if not customer_name or not phone:
            flash('Tafadhali jaza majina yako na namba ya simu.', 'error')
            return render_template('product_details.html', product=product, is_admin=is_admin())
            
        # Kufanya Agizo Jipya
        new_order_id = len(orders) + 1
        new_order = {
            'id': new_order_id,
            'customer_name': customer_name,
            'product_name': product['name'],
            'quantity': 1, # Kwa sasa tunafanya iwe 1
            'phone': phone,
            'status': 'Pending'
        }
        orders.append(new_order)
        flash(f'Agizo lako la {product["name"]} limetumwa kwa mafanikio. Tutawasiliana nawe!', 'success')
        return redirect(url_for('smart_arena_home'))
        
    return render_template('product_details.html', product=product, is_admin=is_admin())


# =================================================================
# ROUTE ZA ADMIN (ADMIN ROUTES)
# =================================================================

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Ukurasa wa Ku-login kwa Admin."""
    if is_admin():
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Karibu! Umefanikiwa kuingia kama Admin.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Jina la mtumiaji au neno la siri si sahihi.', 'error')
            
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    """Kutoka (Logout) kwa Admin."""
    session.pop('logged_in', None)
    flash('Umetoka (Logged out) kwa mafanikio.', 'success')
    return redirect(url_for('smart_arena_home'))

@app.route('/admin')
def admin_dashboard():
    """Dashboard Kuu ya Admin (Ulinzi unaotumia session)."""
    if not is_admin():
        flash('Huna ruhusa ya kufikia ukurasa huu.', 'error')
        return redirect(url_for('admin_login'))
        
    return render_template('admin.html', 
                           products=products, 
                           posts=posts, 
                           orders=orders,
                           is_admin=is_admin())

# == KAZI ZA BIDHAA (PRODUCTS) ==

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    """Kuongeza Bidhaa Mpya (Admin Only)."""
    if not is_admin():
        flash('Huna ruhusa.', 'error')
        return redirect(url_for('admin_login'))
        
    try:
        new_id = len(products) + 1
        name = request.form.get('name')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        
        if not all([name, price, category, description, image_url]):
            flash('Tafadhali jaza taarifa zote za bidhaa.', 'error')
            return redirect(url_for('admin_dashboard'))

        products.append({
            'id': new_id,
            'name': name,
            'price': price,
            'category': category,
            'description': description,
            'image_url': image_url
        })
        flash(f'Bidhaa "{name}" imeongezwa kwa mafanikio.', 'success')
        
    except ValueError:
        flash('Bei lazima iwe namba.', 'error')
    except Exception as e:
        flash(f'Kuna hitilafu: {str(e)}', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    """Kufuta Bidhaa (Admin Only)."""
    if not is_admin():
        flash('Huna ruhusa.', 'error')
        return redirect(url_for('admin_login'))
        
    global products
    initial_len = len(products)
    products = [p for p in products if p['id'] != product_id]
    
    if len(products) < initial_len:
        flash(f'Bidhaa ID {product_id} imefutwa.', 'success')
    else:
        flash(f'Bidhaa ID {product_id} haikupatikana.', 'error')
        
    return redirect(url_for('admin_dashboard'))

# == KAZI ZA MATANGAZO (POSTS) ==

@app.route('/admin/add_post', methods=['POST'])
def add_post():
    """Kuongeza Tangazo Jipya (Admin Only)."""
    if not is_admin():
        flash('Huna ruhusa.', 'error')
        return redirect(url_for('admin_login'))
        
    new_id = len(posts) + 1
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        flash('Tafadhali jaza kichwa cha habari na maudhui ya tangazo.', 'error')
        return redirect(url_for('admin_dashboard'))

    posts.append({
        'id': new_id,
        'title': title,
        'content': content
    })
    flash(f'Tangazo "{title}" limeongezwa kwa mafanikio.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    """Kufuta Tangazo (Admin Only)."""
    if not is_admin():
        flash('Huna ruhusa.', 'error')
        return redirect(url_for('admin_login'))
        
    global posts
    initial_len = len(posts)
    posts = [p for p in posts if p['id'] != post_id]
    
    if len(posts) < initial_len:
        flash(f'Tangazo ID {post_id} limefutwa.', 'success')
    else:
        flash(f'Tangazo ID {post_id} halikupatikana.', 'error')
        
    return redirect(url_for('admin_dashboard'))

# == KAZI ZA MAAGIZO (ORDERS) ==

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    """Kubadilisha Hali ya Agizo (Admin Only)."""
    if not is_admin():
        flash('Huna ruhusa.', 'error')
        return redirect(url_for('admin_login'))
        
    new_status = request.form.get('status')
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            flash(f'Hali ya agizo ID {order_id} imebadilishwa kuwa "{new_status}".', 'success')
            return redirect(url_for('admin_dashboard'))
            
    flash(f'Agizo ID {order_id} halikupatikana.', 'error')
    return redirect(url_for('admin_dashboard'))