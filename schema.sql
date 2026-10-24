-- ========================================================
-- FOOD ORDERING & RESTAURANT MANAGEMENT SYSTEM
-- Database Schema for SQLite (DBMS Project)
-- ========================================================

-- Enable Foreign Key support in SQLite
PRAGMA foreign_keys = ON;

-- 1. USERS TABLE
-- Stores customers and admin/staff accounts
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    role TEXT CHECK(role IN ('customer', 'admin', 'staff')) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CATEGORIES TABLE
-- Food categories like Starters, Main Course, Beverages, Desserts
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    icon TEXT DEFAULT '🍽️'
);

-- 3. MENU ITEMS TABLE
-- Restaurant dishes with attributes (spice levels, diet type, price)
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price > 0),
    diet_type TEXT CHECK(diet_type IN ('veg', 'non-veg')) DEFAULT 'veg',
    is_spicy_customizable INTEGER DEFAULT 1, -- 1: Yes, 0: No
    default_spice_level TEXT CHECK(default_spice_level IN ('Mild', 'Medium', 'Spicy', 'Extra Spicy')) DEFAULT 'Medium',
    image_url TEXT,
    is_available INTEGER DEFAULT 1, -- 1: Available, 0: Out of stock
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- 4. OFFERS / COUPONS TABLE
-- Promotional discount vouchers for customers
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    discount_percent REAL NOT NULL CHECK(discount_percent > 0 AND discount_percent <= 100),
    min_order_amount REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    valid_until TEXT
);

-- 5. ORDERS TABLE
-- Tracks orders, order type (Dine-in / Takeaway), status, and billing totals
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_type TEXT CHECK(order_type IN ('DineIn', 'TakeAway')) NOT NULL,
    table_number INTEGER, -- NULL for TakeAway, integer for DineIn
    total_amount REAL NOT NULL,
    discount_amount REAL DEFAULT 0,
    final_amount REAL NOT NULL,
    status TEXT CHECK(status IN ('Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled')) DEFAULT 'Pending',
    offer_code TEXT,
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 6. ORDER ITEMS TABLE
-- Weak entity / Bridge entity storing itemized list of dishes ordered
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price_per_unit REAL NOT NULL,
    spice_level TEXT DEFAULT 'Medium',
    item_total REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
);

-- 7. RESTAURANT QUEUE / WAITING LIST TABLE
-- Manages physical or virtual customer waitlist for dining tables
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    party_size INTEGER NOT NULL CHECK(party_size > 0),
    token_number INTEGER NOT NULL,
    status TEXT CHECK(status IN ('Waiting', 'Seated', 'Cancelled')) DEFAULT 'Waiting',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 8. STAFF MANAGEMENT TABLE
-- Details of restaurant workforce (roles, shifts, salaries)
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role_title TEXT NOT NULL CHECK(role_title IN ('Manager', 'Head Chef', 'Sous Chef', 'Waiter', 'Cashier', 'Bartender')),
    shift TEXT CHECK(shift IN ('Morning', 'Evening', 'Night')) DEFAULT 'Morning',
    phone TEXT,
    salary REAL NOT NULL CHECK(salary >= 0),
    joined_date DATE DEFAULT (DATE('now'))
);

-- 9. CUSTOMER REVIEWS TABLE
-- Stores ratings (1-5 stars) and reviews for dishes and general service
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_id INTEGER,
    menu_item_id INTEGER,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE SET NULL
);

-- Create indexes for performance in querying orders & menus
CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status);
