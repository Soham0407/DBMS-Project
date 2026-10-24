"""
Database Helper & Seeder for Food Ordering and Restaurant Management System.
Uses SQLite for simple local database management, ideal for college DBMS projects.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'restaurant.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_db():
    """
    Establish and return a SQLite database connection.
    Row factory is set to sqlite3.Row for column-name dictionary-like access.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Execute schema.sql to create tables and indexes."""
    with get_db() as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()


def seed_db():
    """Populate default demo data if database is empty."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print("Seeding initial restaurant data...")

    # 1. Insert Default Users (Admin, Staff, Customer)
    # Password hashing using werkzeug
    admin_pw = generate_password_hash("admin123")
    customer_pw = generate_password_hash("customer123")

    cursor.execute("""
        INSERT INTO users (name, email, password, phone, role)
        VALUES 
        ('Restaurant Manager', 'admin@restaurant.com', ?, '9876543210', 'admin'),
        ('John Doe', 'customer@gmail.com', ?, '9123456789', 'customer'),
        ('Sarah Jenkins', 'sarah@gmail.com', ?, '9811223344', 'customer')
    """, (admin_pw, customer_pw, customer_pw))

    # 2. Insert Categories
    categories = [
        ('Starters & Appetizers', '🥟'),
        ('Main Course', '🍛'),
        ('Pizzas & Italian', '🍕'),
        ('Burgers & Wraps', '🍔'),
        ('Desserts', '🍨'),
        ('Beverages & Drinks', '🍹')
    ]
    cursor.executemany("INSERT INTO categories (name, icon) VALUES (?, ?)", categories)

    # 3. Insert Menu Items with attributes (spicy customization, veg/non-veg, price)
    menu_items = [
        # Starters (category_id = 1)
        (1, 'Crispy Paneer Tikka', 'Tender cottage cheese cubes marinated in spiced yogurt and grilled to perfection.', 260.00, 'veg', 1, 'Medium', 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=500&auto=format&fit=crop&q=60'),
        (1, 'Spicy Chicken Wings', 'Crispy wings tossed in fiery chili garlic sauce with cool ranch dip.', 290.00, 'non-veg', 1, 'Spicy', 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=500&auto=format&fit=crop&q=60'),
        (1, 'Vegetable Spring Rolls', 'Golden crispy rolls packed with sautéed seasonal veggies and sweet plum sauce.', 180.00, 'veg', 1, 'Mild', 'https://images.unsplash.com/photo-1544025162-d76694265947?w=500&auto=format&fit=crop&q=60'),
        (1, 'Garlic Butter Prawns', 'Sautéed prawns cooked in garlic herb butter with toasted baguette slices.', 420.00, 'non-veg', 1, 'Mild', 'https://images.unsplash.com/photo-1559742811-822873691df8?w=500&auto=format&fit=crop&q=60'),

        # Main Course (category_id = 2)
        (2, 'Butter Chicken & Naan', 'Succulent chicken in a rich, buttery tomato gravy served with warm garlic butter naan.', 380.00, 'non-veg', 1, 'Medium', 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=500&auto=format&fit=crop&q=60'),
        (2, 'Shahi Paneer Deluxe', 'Royal cottage cheese curry simmered with cashews and fragrant aromatic spices.', 320.00, 'veg', 1, 'Medium', 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500&auto=format&fit=crop&q=60'),
        (2, 'Hyderabadi Dum Biryani', 'Fragrant basmati rice layered with spiced meat, saffron, and caramelized onions.', 350.00, 'non-veg', 1, 'Spicy', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500&auto=format&fit=crop&q=60'),
        (2, 'Dal Makhani Special', 'Slow-cooked black lentils overnight in fresh cream and country butter.', 250.00, 'veg', 1, 'Mild', 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500&auto=format&fit=crop&q=60'),

        # Pizzas & Italian (category_id = 3)
        (3, 'Margherita Classica', 'Fresh mozzarella, san marzano tomato sauce, fresh basil leaves and extra virgin olive oil.', 290.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=500&auto=format&fit=crop&q=60'),
        (3, 'Fiery Pepperoni Feast', 'Loaded with cured beef pepperoni, jalapeños, chili flakes, and melted mozzarella.', 380.00, 'non-veg', 1, 'Spicy', 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=500&auto=format&fit=crop&q=60'),
        (3, 'Creamy Fettuccine Alfredo', 'Handmade fettuccine ribbons in rich parmesan cream sauce with wild mushrooms.', 320.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1645112411341-6c4fd023714a?w=500&auto=format&fit=crop&q=60'),

        # Burgers & Wraps (category_id = 4)
        (4, 'Smoky BBQ Smash Burger', 'Double grilled smash beef patty, aged cheddar, caramelized onions and house BBQ glaze.', 260.00, 'non-veg', 1, 'Medium', 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&auto=format&fit=crop&q=60'),
        (4, 'Crispy Veggie Supreme Burger', 'Crispy vegetable potato patty topped with spicy mayo, lettuce, pickles and melted cheese.', 190.00, 'veg', 1, 'Medium', 'https://images.unsplash.com/photo-1585238342024-78d387f4a707?w=500&auto=format&fit=crop&q=60'),

        # Desserts (category_id = 5)
        (5, 'Molten Chocolate Lava Cake', 'Warm chocolate cake with molten center served with Madagascar vanilla gelato.', 190.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500&auto=format&fit=crop&q=60'),
        (5, 'Classic New York Cheesecake', 'Rich creamy cheesecake on crunchy graham crust with strawberry coulis.', 220.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500&auto=format&fit=crop&q=60'),

        # Beverages (category_id = 6)
        (6, 'Fresh Mint Mojito', 'Fresh muddled mint, sparkling soda, lime wedges and raw sugar cane syrup.', 140.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&auto=format&fit=crop&q=60'),
        (6, 'Mango Lassi Royal', 'Smooth yogurt smoothie blended with sweet Alphonso mango pulp and cardamom.', 120.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1546173159-315724a31696?w=500&auto=format&fit=crop&q=60'),
        (6, 'Iced Hazelnut Cold Brew', 'Steeped cold brew coffee infused with roasted hazelnut syrup and cold foam.', 160.00, 'veg', 0, 'Mild', 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=500&auto=format&fit=crop&q=60')
    ]

    cursor.executemany("""
        INSERT INTO menu_items (category_id, name, description, price, diet_type, is_spicy_customizable, default_spice_level, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, menu_items)

    # 4. Insert Promotional Offers / Coupons
    offers = [
        ('WELCOME20', '20% Off First Order', 'Enjoy 20% flat discount on your delicious food order.', 20.0, 500.0, 1, '2026-12-31'),
        ('FEAST10', 'Flat 10% Family Feast', 'Save 10% on large family meals and party orders.', 10.0, 800.0, 1, '2026-12-31'),
        ('SPICY15', 'Chef Special 15% Off', 'Special midweek diner discount across all categories.', 15.0, 600.0, 1, '2026-12-31')
    ]
    cursor.executemany("""
        INSERT INTO offers (code, title, description, discount_percent, min_order_amount, is_active, valid_until)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, offers)

    # 5. Insert Staff Members
    staff_members = [
        ('Robert Vance', 'Manager', 'Morning', '9822334455', 45000),
        ('Chef Antonio Rossi', 'Head Chef', 'Morning', '9811445566', 55000),
        ('Priya Sharma', 'Sous Chef', 'Evening', '9833556677', 38000),
        ('Carlos Mendez', 'Waiter', 'Evening', '9844667788', 22000),
        ('Emily Watson', 'Cashier', 'Morning', '9855778899', 24000)
    ]
    cursor.executemany("""
        INSERT INTO staff (name, role_title, shift, phone, salary)
        VALUES (?, ?, ?, ?, ?)
    """, staff_members)

    # 6. Insert Sample Orders
    cursor.execute("""
        INSERT INTO orders (customer_id, order_type, table_number, total_amount, discount_amount, final_amount, status, offer_code, special_instructions)
        VALUES (2, 'DineIn', 4, 670.00, 134.00, 536.00, 'Preparing', 'WELCOME20', 'Please serve appetizers first and make it less salty.')
    """)
    order_id_1 = cursor.lastrowid

    cursor.execute("""
        INSERT INTO order_items (order_id, menu_item_id, quantity, price_per_unit, spice_level, item_total)
        VALUES 
        (?, 2, 1, 290.00, 'Extra Spicy', 290.00),
        (?, 13, 2, 190.00, 'Mild', 380.00)
    """, (order_id_1, order_id_1))

    cursor.execute("""
        INSERT INTO orders (customer_id, order_type, table_number, total_amount, discount_amount, final_amount, status, offer_code, special_instructions)
        VALUES (3, 'TakeAway', NULL, 890.00, 0.0, 890.00, 'Completed', NULL, 'Pack cutlery and extra napkins please.')
    """)
    order_id_2 = cursor.lastrowid

    cursor.execute("""
        INSERT INTO order_items (order_id, menu_item_id, quantity, price_per_unit, spice_level, item_total)
        VALUES 
        (?, 5, 1, 380.00, 'Medium', 380.00),
        (?, 11, 1, 320.00, 'Mild', 320.00),
        (?, 14, 1, 190.00, 'Mild', 190.00)
    """, (order_id_2, order_id_2, order_id_2))

    # 7. Insert Sample Queue Entries
    cursor.execute("""
        INSERT INTO queue (customer_id, customer_name, party_size, token_number, status)
        VALUES 
        (2, 'John Doe', 3, 101, 'Waiting'),
        (3, 'Sarah Jenkins', 2, 102, 'Waiting')
    """)

    # 8. Insert Sample Reviews
    cursor.execute("""
        INSERT INTO reviews (customer_id, order_id, menu_item_id, rating, comment)
        VALUES 
        (2, 1, 1, 5, 'The Paneer Tikka was extraordinarily soft and flavorful! Perfect spice level.'),
        (3, 2, 5, 5, 'Butter chicken with garlic naan was heavenly. Authentic rich flavors.'),
        (2, 1, NULL, 4, 'Great ambiance and attentive service. Will definitely dine in again!')
    """)

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")


if __name__ == '__main__':
    init_db()
    seed_db()
