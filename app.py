"""
Food Ordering and Restaurant Management System
Backend: Python Flask + SQLite
DBMS Project Implementation
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = 'restaurant_super_secret_key_dbms_2026'

# Ensure database is initialized and seeded on startup
init_db()
seed_db()



# -------------------------------------------------------------------------
# AUTHENTICATION HELPERS & DECORATORS
# -------------------------------------------------------------------------
def login_required(f):
    """Decorator to protect routes requiring logged-in customer or staff."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to protect routes requiring admin or staff privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') not in ['admin', 'staff']:
            flash('Staff or Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def customer_only(f):
    """Decorator to prevent admin/staff from seeing customer-facing pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') in ['admin', 'staff']:
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def get_customer_queue_status(customer_id):
    """Fetch customer's active queue spot (Waiting or Seated)."""
    conn = get_db()
    entry = conn.execute("""
        SELECT * FROM queue 
        WHERE customer_id = ? AND status IN ('Waiting', 'Seated')
        ORDER BY id DESC LIMIT 1
    """, (customer_id,)).fetchone()
    conn.close()
    return entry


@app.context_processor
def inject_global_data():
    """Injects user session data and active cart item count into all Jinja templates."""
    cart_count = 0
    if 'cart' in session:
        cart_count = sum(item.get('quantity', 1) for item in session['cart'].values())
    return {
        'current_user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'role': session.get('user_role'),
            'email': session.get('user_email')
        },
        'cart_count': cart_count
    }


# -------------------------------------------------------------------------
# AUTHENTICATION ROUTES (Login, Signup, Logout)
# -------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login supporting both customers and admin/staff."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['user_email'] = user['email']

            flash(f"Welcome back, {user['name']}!", 'success')
            if user['role'] in ['admin', 'staff']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('menu'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@app.route('/quick-login/<role>')
def quick_login(role):
    """Convenient 1-click login helper for college viva / project demonstration."""
    conn = get_db()
    if role == 'admin':
        user = conn.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    else:
        user = conn.execute("SELECT * FROM users WHERE role = 'customer' LIMIT 1").fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        session['user_email'] = user['email']
        flash(f"Logged in as demo {role.capitalize()} ({user['name']})", 'info')
        if user['role'] in ['admin', 'staff']:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('menu'))
    flash('Demo user not found.', 'danger')
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """New customer registration."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
            return render_template('auth/signup.html')

        hashed_pw = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO users (name, email, password, phone, role)
                VALUES (?, ?, ?, ?, 'customer')
            """, (name, email, hashed_pw, phone))
            conn.commit()

            # Auto-login after registration
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['user_email'] = user['email']

            flash('Account created successfully! Welcome to the restaurant.', 'success')
            return redirect(url_for('menu'))
        except sqlite3.IntegrityError:
            flash('An account with this email address already exists.', 'danger')
        finally:
            conn.close()

    return render_template('auth/signup.html')


@app.route('/logout')
def logout():
    """Clear session data and log out."""
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('login'))


# -------------------------------------------------------------------------
# CUSTOMER PORTAL ROUTES
# -------------------------------------------------------------------------
@app.route('/')
@customer_only
def index():
    """Landing homepage with restaurant highlights and active offers."""
    conn = get_db()
    # Featured items
    featured = conn.execute("""
        SELECT m.*, c.name as category_name 
        FROM menu_items m 
        JOIN categories c ON m.category_id = c.id
        WHERE m.is_available = 1
        LIMIT 6
    """).fetchall()

    # Active promotional offers
    offers = conn.execute("SELECT * FROM offers WHERE is_active = 1 LIMIT 3").fetchall()

    # Recent customer reviews
    reviews = conn.execute("""
        SELECT r.*, u.name as customer_name, m.name as dish_name
        FROM reviews r
        JOIN users u ON r.customer_id = u.id
        LEFT JOIN menu_items m ON r.menu_item_id = m.id
        ORDER BY r.created_at DESC LIMIT 3
    """).fetchall()

    # Active queue count
    queue_count = conn.execute("SELECT COUNT(*) FROM queue WHERE status = 'Waiting'").fetchone()[0]

    conn.close()
    return render_template('customer/index.html', featured=featured, offers=offers, reviews=reviews, queue_count=queue_count)


@app.route('/menu')
@customer_only
def menu():
    """Interactive food menu with category filter, dietary filter, and spice selection."""
    category_id = request.args.get('category', type=int)
    diet = request.args.get('diet', type=str)
    search = request.args.get('search', type=str, default='').strip()

    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY id ASC").fetchall()

    # Dynamic SQL construction based on filters
    query = """
        SELECT m.*, c.name as category_name, c.icon as category_icon
        FROM menu_items m
        JOIN categories c ON m.category_id = c.id
        WHERE 1=1
    """
    params = []

    if category_id:
        query += " AND m.category_id = ?"
        params.append(category_id)
    if diet in ['veg', 'non-veg']:
        query += " AND m.diet_type = ?"
        params.append(diet)
    if search:
        query += " AND (m.name LIKE ? OR m.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY m.is_available DESC, m.category_id ASC, m.name ASC"

    menu_items = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('customer/menu.html', 
                           categories=categories, 
                           menu_items=menu_items,
                           selected_category=category_id,
                           selected_diet=diet,
                           search_query=search)


# -------------------------------------------------------------------------
# CART & CHECKOUT MANAGEMENT (Session-backed with spice customization)
# -------------------------------------------------------------------------
@app.route('/cart/add', methods=['POST'])
@customer_only
def add_to_cart():
    """Add a dish to cart with selected spice level and quantity."""
    item_id = request.form.get('item_id', type=int)
    spice_level = request.form.get('spice_level', 'Medium')
    quantity = request.form.get('quantity', 1, type=int)

    if quantity <= 0:
        quantity = 1

    conn = get_db()
    item = conn.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
    conn.close()

    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('menu'))

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    # Composite key includes spice level so same item with different spice are separate entries!
    cart_key = f"{item_id}_{spice_level}"

    if cart_key in cart:
        cart[cart_key]['quantity'] += quantity
    else:
        cart[cart_key] = {
            'item_id': item['id'],
            'name': item['name'],
            'price': float(item['price']),
            'spice_level': spice_level,
            'quantity': quantity,
            'diet_type': item['diet_type']
        }

    session['cart'] = cart
    session.modified = True
    flash(f"Added {item['name']} ({spice_level}) to your cart!", 'success')
    return redirect(request.referrer or url_for('menu'))


@app.route('/cart/update', methods=['POST'])
@customer_only
def update_cart():
    """Update item quantity or remove item from cart."""
    cart_key = request.form.get('cart_key')
    action = request.form.get('action')  # 'increase', 'decrease', 'remove'

    if 'cart' in session and cart_key in session['cart']:
        cart = session['cart']
        if action == 'increase':
            cart[cart_key]['quantity'] += 1
        elif action == 'decrease':
            cart[cart_key]['quantity'] -= 1
            if cart[cart_key]['quantity'] <= 0:
                del cart[cart_key]
        elif action == 'remove':
            del cart[cart_key]

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('view_cart'))


@app.route('/cart/clear', methods=['POST'])
@customer_only
def clear_cart():
    """Empty cart contents."""
    session.pop('cart', None)
    session.pop('applied_offer', None)
    flash('Cart has been cleared.', 'info')
    return redirect(url_for('view_cart'))


@app.route('/cart')
@customer_only
def view_cart():
    """View cart contents, select DineIn/TakeAway, apply promo codes."""
    cart = session.get('cart', {})
    cart_items = list(cart.values())

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Calculate discount if coupon applied
    discount_amount = 0.0
    applied_offer = session.get('applied_offer')

    # Single-use check for WELCOME20
    user_id = session.get('user_id')
    used_welcome20 = False
    if user_id:
        conn = get_db()
        used_count = conn.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE customer_id = ? AND UPPER(offer_code) = 'WELCOME20' AND status != 'Cancelled'
        """, (user_id,)).fetchone()[0]
        conn.close()
        used_welcome20 = (used_count > 0)

        if applied_offer and applied_offer.get('code') == 'WELCOME20' and used_welcome20:
            session.pop('applied_offer', None)
            applied_offer = None
            flash("Coupon 'WELCOME20' is only applicable once for your first order. You have already redeemed it.", 'warning')

    if applied_offer and subtotal > 0:
        if subtotal >= applied_offer['min_order_amount']:
            discount_amount = round((subtotal * applied_offer['discount_percent']) / 100.0, 2)
        else:
            # Min order requirement no longer met
            session.pop('applied_offer', None)
            applied_offer = None
            flash(f"Minimum order for coupon was not met. Offer removed.", 'warning')

    final_total = max(0.0, round(subtotal - discount_amount, 2))

    # Check seating requirement
    is_seated = False
    my_queue = None
    if user_id:
        my_queue = get_customer_queue_status(user_id)
        if my_queue and my_queue['status'] == 'Seated':
            is_seated = True

    conn = get_db()
    offers = conn.execute("SELECT * FROM offers WHERE is_active = 1").fetchall()
    conn.close()

    return render_template('customer/cart.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           discount_amount=discount_amount,
                           final_total=final_total,
                           applied_offer=applied_offer,
                           available_offers=offers,
                           is_seated=is_seated,
                           my_queue=my_queue,
                           used_welcome20=used_welcome20)


@app.route('/cart/apply-offer', methods=['POST'])
@customer_only
def apply_offer():
    """Validate and apply promo code discount."""
    code = request.form.get('offer_code', '').strip().upper()
    user_id = session.get('user_id')

    # Enforce WELCOME20 single-use rule
    if code == 'WELCOME20' and user_id:
        conn = get_db()
        used_count = conn.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE customer_id = ? AND UPPER(offer_code) = 'WELCOME20' AND status != 'Cancelled'
        """, (user_id,)).fetchone()[0]
        conn.close()
        if used_count > 0:
            flash("Promo code 'WELCOME20' is only applicable once for your first order. You have already redeemed this offer.", 'danger')
            return redirect(url_for('view_cart'))
    
    conn = get_db()
    offer = conn.execute("SELECT * FROM offers WHERE code = ? AND is_active = 1", (code,)).fetchone()
    conn.close()

    if not offer:
        flash(f"Invalid or expired promo code: '{code}'", 'danger')
        return redirect(url_for('view_cart'))

    # Calculate subtotal
    cart = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())

    if subtotal < offer['min_order_amount']:
        flash(f"Offer '{code}' requires a minimum order amount of ₹{offer['min_order_amount']:.2f}.", 'warning')
        return redirect(url_for('view_cart'))

    session['applied_offer'] = {
        'code': offer['code'],
        'title': offer['title'],
        'discount_percent': float(offer['discount_percent']),
        'min_order_amount': float(offer['min_order_amount'])
    }
    flash(f"Promo code '{offer['code']}' applied! You save {offer['discount_percent']}%.", 'success')
    return redirect(url_for('view_cart'))


@app.route('/cart/remove-offer', methods=['POST'])
@customer_only
def remove_offer():
    """Remove currently applied promo code."""
    session.pop('applied_offer', None)
    flash('Promo code removed.', 'info')
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['POST'])
@login_required
@customer_only
def checkout():
    """
    Process order placement:
    Only allowed when the customer is Seated.
    Validates single-use WELCOME20 coupon.
    Inserts order into `orders` table and item details into `order_items` table.
    """
    user_id = session['user_id']

    # 1. Enforce Seating requirement
    my_queue = get_customer_queue_status(user_id)
    if not my_queue or my_queue['status'] != 'Seated':
        if my_queue and my_queue['status'] == 'Waiting':
            flash(f"You cannot place an order yet. You are currently in the table queue (Token #{my_queue['token_number']}). Please wait until restaurant staff seats you at a table.", 'warning')
        else:
            flash("You cannot place an order yet. You must be seated at a table before ordering. Please join the table queue first.", 'warning')
        return redirect(url_for('customer_queue'))

    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty. Add some delicious dishes first!', 'warning')
        return redirect(url_for('menu'))

    order_type = request.form.get('order_type', 'DineIn')
    table_number = request.form.get('table_number', type=int) if order_type == 'DineIn' else None
    special_instructions = request.form.get('special_instructions', '').strip()

    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    applied_offer = session.get('applied_offer')
    discount_amount = 0.0
    offer_code = None

    # Enforce WELCOME20 single-use check at checkout
    if applied_offer and applied_offer.get('code') == 'WELCOME20':
        conn_check = get_db()
        used_count = conn_check.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE customer_id = ? AND UPPER(offer_code) = 'WELCOME20' AND status != 'Cancelled'
        """, (user_id,)).fetchone()[0]
        conn_check.close()
        if used_count > 0:
            session.pop('applied_offer', None)
            applied_offer = None
            flash("Coupon 'WELCOME20' is only applicable once for your first order. Order placed at regular price.", 'warning')

    if applied_offer and subtotal >= applied_offer['min_order_amount']:
        discount_amount = round((subtotal * applied_offer['discount_percent']) / 100.0, 2)
        offer_code = applied_offer['code']

    final_amount = max(0.0, round(subtotal - discount_amount, 2))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 1. Insert into orders table
        cursor.execute("""
            INSERT INTO orders (customer_id, order_type, table_number, total_amount, discount_amount, final_amount, status, offer_code, special_instructions)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        """, (user_id, order_type, table_number, subtotal, discount_amount, final_amount, offer_code, special_instructions))
        
        order_id = cursor.lastrowid

        # 2. Insert into order_items table (Relation)
        for key, item in cart.items():
            item_total = round(item['price'] * item['quantity'], 2)
            cursor.execute("""
                INSERT INTO order_items (order_id, menu_item_id, quantity, price_per_unit, spice_level, item_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, item['item_id'], item['quantity'], item['price'], item['spice_level'], item_total))

        conn.commit()

        # Clear cart and promo code
        session.pop('cart', None)
        session.pop('applied_offer', None)

        flash(f'Order #{order_id} placed successfully!', 'success')
        return redirect(url_for('check_bill', order_id=order_id))
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred while placing order: {str(e)}', 'danger')
        return redirect(url_for('view_cart'))
    finally:
        conn.close()


# -------------------------------------------------------------------------
# BILL & ORDER STATUS TRACKER
# -------------------------------------------------------------------------
@app.route('/bill/<int:order_id>')
@login_required
def check_bill(order_id):
    """
    Check Bill / Invoice Page.
    Fetches order header, item details with spice preferences, and customer info.
    """
    conn = get_db()
    order = conn.execute("""
        SELECT o.*, u.name as customer_name, u.email as customer_email, u.phone as customer_phone
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        WHERE o.id = ?
    """, (order_id,)).fetchone()

    if not order:
        conn.close()
        flash('Order not found.', 'danger')
        return redirect(url_for('admin_orders') if session.get('user_role') in ['admin', 'staff'] else url_for('my_orders'))

    # Security check: Only customer who placed it or staff can view bill
    if session.get('user_role') not in ['admin', 'staff'] and order['customer_id'] != session['user_id']:
        conn.close()
        flash('Unauthorized access to this order bill.', 'danger')
        return redirect(url_for('my_orders'))

    items = conn.execute("""
        SELECT oi.*, m.name as dish_name, m.diet_type
        FROM order_items oi
        JOIN menu_items m ON oi.menu_item_id = m.id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()

    conn.close()
    return render_template('customer/bill.html', order=order, items=items)


@app.route('/orders')
@login_required
@customer_only
def my_orders():
    """Customer's active and past order history."""
    conn = get_db()
    orders = conn.execute("""
        SELECT o.*, COUNT(oi.id) as total_items
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.customer_id = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """, (session['user_id'],)).fetchall()
    conn.close()

    return render_template('customer/orders.html', orders=orders)


# -------------------------------------------------------------------------
# QUEUE / WAITING LIST (DINE-IN)
# -------------------------------------------------------------------------
@app.route('/queue', methods=['GET', 'POST'])
@login_required
@customer_only
def customer_queue():
    """
    Customer table waiting queue.
    Allows customers to join the waitlist, view live token number, and see when they are Seated.
    """
    conn = get_db()

    if request.method == 'POST':
        party_size = request.form.get('party_size', 2, type=int)
        
        # Check if already waiting or seated
        existing = conn.execute("""
            SELECT * FROM queue 
            WHERE customer_id = ? AND status IN ('Waiting', 'Seated')
        """, (session['user_id'],)).fetchone()

        if existing:
            if existing['status'] == 'Seated':
                flash(f"You are currently seated at a table (Token #{existing['token_number']})!", 'info')
            else:
                flash(f"You already have an active queue spot (Token #{existing['token_number']}).", 'warning')
        else:
            # Calculate next token number for the day
            last_token = conn.execute("SELECT MAX(token_number) FROM queue").fetchone()[0]
            next_token = (last_token or 100) + 1

            conn.execute("""
                INSERT INTO queue (customer_id, customer_name, party_size, token_number, status)
                VALUES (?, ?, ?, ?, 'Waiting')
            """, (session['user_id'], session['user_name'], party_size, next_token))
            conn.commit()
            flash(f"You have joined the queue! Your Token number is #{next_token}.", 'success')

    # Fetch customer's current queue status (Waiting or Seated)
    my_queue = conn.execute("""
        SELECT * FROM queue 
        WHERE customer_id = ? AND status IN ('Waiting', 'Seated')
        ORDER BY id DESC LIMIT 1
    """, (session['user_id'],)).fetchone()

    parties_ahead = 0
    if my_queue and my_queue['status'] == 'Waiting':
        parties_ahead = conn.execute("""
            SELECT COUNT(*) FROM queue 
            WHERE status = 'Waiting' AND id < ?
        """, (my_queue['id'],)).fetchone()[0]

    # Overall active waitlist count
    total_waiting = conn.execute("SELECT COUNT(*) FROM queue WHERE status = 'Waiting'").fetchone()[0]

    conn.close()
    return render_template('customer/queue.html', 
                           my_queue=my_queue, 
                           parties_ahead=parties_ahead, 
                           total_waiting=total_waiting)


@app.route('/queue/cancel', methods=['POST'])
@login_required
@customer_only
def cancel_queue():
    """Customer cancels their queue waiting spot."""
    conn = get_db()
    conn.execute("""
        UPDATE queue 
        SET status = 'Cancelled' 
        WHERE customer_id = ? AND status = 'Waiting'
    """, (session['user_id'],))
    conn.commit()
    conn.close()

    flash('Your spot in the waiting list has been cancelled.', 'info')
    return redirect(url_for('customer_queue'))


@app.route('/queue/leave', methods=['POST'])
@login_required
@customer_only
def leave_table():
    """Customer leaves their table when finished dining."""
    conn = get_db()
    conn.execute("""
        UPDATE queue 
        SET status = 'Cancelled' 
        WHERE customer_id = ? AND status IN ('Waiting', 'Seated')
    """, (session['user_id'],))
    conn.commit()
    conn.close()

    flash('You have vacated your table. Thank you for dining with us!', 'info')
    return redirect(url_for('customer_queue'))


# -------------------------------------------------------------------------
# OFFERS SECTION (Customer View)
# -------------------------------------------------------------------------
@app.route('/offers')
@customer_only
def customer_offers():
    """Browse all promotional offers, discounts, and vouchers."""
    conn = get_db()
    offers = conn.execute("SELECT * FROM offers WHERE is_active = 1 ORDER BY discount_percent DESC").fetchall()

    used_welcome20 = False
    if 'user_id' in session:
        count = conn.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE customer_id = ? AND UPPER(offer_code) = 'WELCOME20' AND status != 'Cancelled'
        """, (session['user_id'],)).fetchone()[0]
        used_welcome20 = (count > 0)

    conn.close()
    return render_template('customer/offers.html', offers=offers, used_welcome20=used_welcome20)


# -------------------------------------------------------------------------
# REVIEWS SECTION (Ratings & Feedback)
# -------------------------------------------------------------------------
@app.route('/reviews', methods=['GET', 'POST'])
@customer_only
def customer_reviews():
    """View and post reviews for dishes or restaurant dining experience."""
    conn = get_db()

    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to leave a review.', 'warning')
            return redirect(url_for('login'))

        rating = request.form.get('rating', 5, type=int)
        comment = request.form.get('comment', '').strip()
        menu_item_id = request.form.get('menu_item_id', type=int) or None
        order_id = request.form.get('order_id', type=int) or None

        if not comment:
            flash('Please enter your review comments.', 'danger')
        else:
            conn.execute("""
                INSERT INTO reviews (customer_id, order_id, menu_item_id, rating, comment)
                VALUES (?, ?, ?, ?, ?)
            """, (session['user_id'], order_id, menu_item_id, rating, comment))
            conn.commit()
            flash('Thank you for your valuable feedback!', 'success')
            return redirect(url_for('customer_reviews'))

    # Fetch all reviews with user names and dish names
    reviews = conn.execute("""
        SELECT r.*, u.name as customer_name, m.name as dish_name
        FROM reviews r
        JOIN users u ON r.customer_id = u.id
        LEFT JOIN menu_items m ON r.menu_item_id = m.id
        ORDER BY r.created_at DESC
    """).fetchall()

    # Dishes for review dropdown
    dishes = conn.execute("SELECT id, name FROM menu_items WHERE is_available = 1 ORDER BY name ASC").fetchall()
    
    # Calculate average rating
    avg_rating_row = conn.execute("SELECT AVG(rating), COUNT(*) FROM reviews").fetchone()
    avg_rating = round(avg_rating_row[0] or 5.0, 1)
    total_reviews = avg_rating_row[1]

    conn.close()
    return render_template('customer/reviews.html', 
                           reviews=reviews, 
                           dishes=dishes, 
                           avg_rating=avg_rating, 
                           total_reviews=total_reviews)


# -------------------------------------------------------------------------
# RESTAURANT SIDE (ADMIN / STAFF / SERVER)
# -------------------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    """
    Staff / Admin Dashboard:
    Live statistics (Total revenue, order counts by status, live queue, staff count).
    """
    conn = get_db()
    
    # Metrics
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue = conn.execute("SELECT SUM(final_amount) FROM orders WHERE status != 'Cancelled'").fetchone()[0] or 0.0
    pending_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Pending', 'Preparing')").fetchone()[0]
    active_queue = conn.execute("SELECT COUNT(*) FROM queue WHERE status = 'Waiting'").fetchone()[0]
    staff_count = conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]

    # Recent 5 Orders
    recent_orders = conn.execute("""
        SELECT o.*, u.name as customer_name
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        ORDER BY o.created_at DESC LIMIT 5
    """).fetchall()

    # Popular Dishes (Aggregation using GROUP BY & SUM)
    popular_dishes = conn.execute("""
        SELECT m.name, SUM(oi.quantity) as total_sold, SUM(oi.item_total) as revenue
        FROM order_items oi
        JOIN menu_items m ON oi.menu_item_id = m.id
        GROUP BY oi.menu_item_id
        ORDER BY total_sold DESC LIMIT 4
    """).fetchall()

    conn.close()
    return render_template('admin/dashboard.html',
                           total_orders=total_orders,
                           total_revenue=round(total_revenue, 2),
                           pending_orders=pending_orders,
                           active_queue=active_queue,
                           staff_count=staff_count,
                           recent_orders=recent_orders,
                           popular_dishes=popular_dishes)


@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Live Order Management: Filter by status, see item spice levels and table info."""
    status_filter = request.args.get('status', 'All')

    conn = get_db()
    query = """
        SELECT o.*, u.name as customer_name, u.phone as customer_phone
        FROM orders o
        JOIN users u ON o.customer_id = u.id
    """
    params = []
    if status_filter != 'All':
        query += " WHERE o.status = ?"
        params.append(status_filter)

    query += " ORDER BY CASE o.status WHEN 'Pending' THEN 1 WHEN 'Preparing' THEN 2 WHEN 'Ready' THEN 3 ELSE 4 END, o.created_at DESC"

    orders = conn.execute(query, params).fetchall()

    # Pre-fetch items for each order to display cleanly in kitchen order view
    orders_data = []
    for ord_row in orders:
        items = conn.execute("""
            SELECT oi.*, m.name as dish_name
            FROM order_items oi
            JOIN menu_items m ON oi.menu_item_id = m.id
            WHERE oi.order_id = ?
        """, (ord_row['id'],)).fetchall()
        orders_data.append({
            'order': ord_row,
            'order_items': items
        })

    conn.close()
    return render_template('admin/orders.html', orders_data=orders_data, current_status=status_filter)


@app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """One-click transition of order status (Pending -> Preparing -> Ready -> Completed / Cancelled)."""
    new_status = request.form.get('status')
    valid_statuses = ['Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled']

    if new_status in valid_statuses:
        conn = get_db()
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        flash(f"Order #{order_id} status updated to '{new_status}'.", 'success')
        if new_status == 'Completed':
            return redirect(url_for('admin_orders', status='Completed'))
    else:
        flash("Invalid status update.", 'danger')

    return redirect(request.referrer or url_for('admin_orders'))


# -------------------------------------------------------------------------
# MENU ITEMS MANAGEMENT (Add, Edit, Delete, Toggle Availability)
# -------------------------------------------------------------------------
@app.route('/admin/menu')
@admin_required
def admin_menu():
    """Menu list with filters and management modal."""
    conn = get_db()
    items = conn.execute("""
        SELECT m.*, c.name as category_name
        FROM menu_items m
        JOIN categories c ON m.category_id = c.id
        ORDER BY m.category_id ASC, m.name ASC
    """).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY id ASC").fetchall()
    conn.close()

    return render_template('admin/menu_items.html', items=items, categories=categories)


@app.route('/admin/menu/add', methods=['POST'])
@admin_required
def add_menu_item():
    """Add a new dish to the restaurant menu."""
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id', type=int)
    description = request.form.get('description', '').strip()
    price = request.form.get('price', type=float)
    diet_type = request.form.get('diet_type', 'veg')
    is_spicy_customizable = 1 if request.form.get('is_spicy_customizable') else 0
    default_spice_level = request.form.get('default_spice_level', 'Medium')

    conn = get_db()
    conn.execute("""
        INSERT INTO menu_items (category_id, name, description, price, diet_type, is_spicy_customizable, default_spice_level, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, '')
    """, (category_id, name, description, price, diet_type, is_spicy_customizable, default_spice_level))
    conn.commit()
    conn.close()

    flash(f"Menu item '{name}' added successfully!", 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/toggle-stock', methods=['POST'])
@admin_required
def toggle_item_stock(item_id):
    """Toggle in-stock / out-of-stock status."""
    conn = get_db()
    conn.execute("UPDATE menu_items SET is_available = CASE WHEN is_available = 1 THEN 0 ELSE 1 END WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item stock availability updated.", 'info')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/delete', methods=['POST'])
@admin_required
def delete_menu_item(item_id):
    """Delete a dish from menu."""
    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Menu item deleted.", 'info')
    return redirect(url_for('admin_menu'))


# -------------------------------------------------------------------------
# STAFF MANAGEMENT (Staff Directory, Add, Shifts, Salaries)
# -------------------------------------------------------------------------
@app.route('/admin/staff')
@admin_required
def admin_staff():
    """Manage staff members, roles, shifts, and salaries."""
    conn = get_db()
    staff_list = conn.execute("SELECT * FROM staff ORDER BY id DESC").fetchall()
    total_payroll = conn.execute("SELECT SUM(salary) FROM staff").fetchone()[0] or 0
    conn.close()

    return render_template('admin/staff.html', staff_list=staff_list, total_payroll=total_payroll)


@app.route('/admin/staff/add', methods=['POST'])
@admin_required
def add_staff():
    """Add a new employee / staff member."""
    name = request.form.get('name', '').strip()
    role_title = request.form.get('role_title', 'Waiter')
    shift = request.form.get('shift', 'Morning')
    phone = request.form.get('phone', '').strip()
    salary = request.form.get('salary', 0, type=float)

    conn = get_db()
    conn.execute("""
        INSERT INTO staff (name, role_title, shift, phone, salary)
        VALUES (?, ?, ?, ?, ?)
    """, (name, role_title, shift, phone, salary))
    conn.commit()
    conn.close()

    flash(f"Staff member '{name}' ({role_title}) added successfully!", 'success')
    return redirect(url_for('admin_staff'))


@app.route('/admin/staff/<int:staff_id>/delete', methods=['POST'])
@admin_required
def delete_staff(staff_id):
    """Remove a staff member."""
    conn = get_db()
    conn.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    conn.commit()
    conn.close()
    flash("Staff record removed.", 'info')
    return redirect(url_for('admin_staff'))


# -------------------------------------------------------------------------
# QUEUE / WAITLIST MANAGEMENT (Restaurant Side)
# -------------------------------------------------------------------------
@app.route('/admin/queue')
@admin_required
def admin_queue():
    """Live restaurant table waitlist queue monitoring."""
    conn = get_db()
    queue_list = conn.execute("""
        SELECT * FROM queue 
        ORDER BY CASE status WHEN 'Waiting' THEN 1 ELSE 2 END, id ASC
    """).fetchall()
    conn.close()

    return render_template('admin/queue.html', queue_list=queue_list)


@app.route('/admin/queue/<int:queue_id>/seat', methods=['POST'])
@admin_required
def seat_customer(queue_id):
    """Seat a waiting party at a table."""
    conn = get_db()
    conn.execute("UPDATE queue SET status = 'Seated' WHERE id = ?", (queue_id,))
    conn.commit()
    conn.close()
    flash(f"Party has been marked as Seated!", 'success')
    return redirect(url_for('admin_queue'))


@app.route('/admin/queue/<int:queue_id>/cancel', methods=['POST'])
@admin_required
def cancel_queue_entry(queue_id):
    """Cancel customer queue spot."""
    conn = get_db()
    conn.execute("UPDATE queue SET status = 'Cancelled' WHERE id = ?", (queue_id,))
    conn.commit()
    conn.close()
    flash(f"Queue entry cancelled.", 'info')
    return redirect(url_for('admin_queue'))


@app.route('/admin/queue/<int:queue_id>/release', methods=['POST'])
@admin_required
def release_queue_entry(queue_id):
    """Release/vacate a seated customer table."""
    conn = get_db()
    conn.execute("UPDATE queue SET status = 'Cancelled' WHERE id = ?", (queue_id,))
    conn.commit()
    conn.close()
    flash("Table has been cleared and vacated.", 'info')
    return redirect(url_for('admin_queue'))


# -------------------------------------------------------------------------
# OFFERS MANAGEMENT (Restaurant Side)
# -------------------------------------------------------------------------
@app.route('/admin/offers')
@admin_required
def admin_offers():
    """Manage promotional discount codes."""
    conn = get_db()
    offers = conn.execute("SELECT * FROM offers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin/offers.html', offers=offers)


@app.route('/admin/offers/add', methods=['POST'])
@admin_required
def add_offer():
    """Create a new promotional discount voucher."""
    code = request.form.get('code', '').strip().upper()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    discount_percent = request.form.get('discount_percent', type=float)
    min_order_amount = request.form.get('min_order_amount', 0.0, type=float)
    valid_until = request.form.get('valid_until', '2026-12-31')

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO offers (code, title, description, discount_percent, min_order_amount, is_active, valid_until)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (code, title, description, discount_percent, min_order_amount, valid_until))
        conn.commit()
        flash(f"Offer code '{code}' created successfully!", 'success')
    except sqlite3.IntegrityError:
        flash(f"An offer code with '{code}' already exists.", 'danger')
    finally:
        conn.close()

    return redirect(url_for('admin_offers'))


@app.route('/admin/offers/<int:offer_id>/toggle', methods=['POST'])
@admin_required
def toggle_offer(offer_id):
    """Toggle offer active / inactive."""
    conn = get_db()
    conn.execute("UPDATE offers SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (offer_id,))
    conn.commit()
    conn.close()
    flash("Offer status updated.", 'info')
    return redirect(url_for('admin_offers'))


@app.route('/admin/offers/<int:offer_id>/delete', methods=['POST'])
@admin_required
def delete_offer(offer_id):
    """Delete offer."""
    conn = get_db()
    conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    conn.commit()
    conn.close()
    flash("Offer deleted.", 'info')
    return redirect(url_for('admin_offers'))


# -------------------------------------------------------------------------
# RUN APPLICATION
# -------------------------------------------------------------------------
if __name__ == '__main__':
    # Run locally on port 5000
    app.run(debug=True, port=5000)
