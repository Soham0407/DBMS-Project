# 🍽️ Saffron Feast — Food Ordering & Restaurant Management System
> **Academic DBMS Project** built with **Python Flask**, **SQLite3**, **HTML5**, **Vanilla CSS3**, and **JavaScript**.

---

## 📌 Project Overview
**Saffron Feast** is a full-stack restaurant management solution designed specifically for college/university DBMS courses. It provides a dual-portal interface:
1. **Customer Side**: Account registration, live table waitlist queue, interactive menu with spice level customization, dynamic cart & checkout (Dine-In with Table Number vs TakeAway), coupon code discounts, printable bills with real-time kitchen tracking, and customer reviews.
2. **Restaurant / Server Side (Admin & Staff)**: Real-time operations dashboard, kitchen order stream with one-click status transitions, menu catalog management (add dish, toggle stock), workforce/staff management (roles, shifts, salaries), live queue host control, and promotional offer creation.

---

## 🎯 Key Features Breakdown

### 👤 1. Customer Side
- **Authentication**: Secure Login & Sign-up using hashed passwords (`werkzeug.security`).
- **Table Queue (Waitlist)**:
  - Join waitlist by selecting party size (1, 2, 4, 6+ guests).
  - Live digital token generation (e.g., `#103`).
  - View real-time parties ahead in line and estimated wait time.
  - Option to cancel token.
- **Interactive Menu**:
  - Filter by food category (*Starters, Main Course, Pizzas, Burgers, Desserts, Beverages*).
  - Dietary filter: **Pure Veg (🟢)** vs **Non-Veg (🔺)**.
  - Real-time search by dish name or description.
- **Item Customization (Attributes)**:
  - Spice level selector for dishes: **Mild (🟢)**, **Medium (🟡)**, **Spicy (🟠)**, or **Extra Spicy (🔴)**.
  - Custom quantity selector.
- **Cart & Checkout**:
  - Multiple spice variations of the same dish are tracked independently.
  - Choose between **Dine-In** (select Table 1-7) or **Express TakeAway**.
  - Promotional coupon apply box (validates minimum order rules).
  - Special chef cooking instructions.
- **Check Bill & Invoice**:
  - Complete digital invoice with Order ID, customer details, itemized breakdown, tax/discounts, and total.
  - **Live Kitchen Status Tracker**: `1. Placed` ➔ `2. In Kitchen` ➔ `3. Food Ready` ➔ `4. Served`.
  - Clean printable format with CSS `@media print` support (`Ctrl+P`).
- **Customer Reviews**:
  - Read diner reviews with 1–5 star ratings.
  - Submit ratings & feedback linked to specific menu items or dining experience.
- **Past Orders History**:
  - Instant access to historical bills and current active orders.
- **Offers Section**:
  - Browse active discount vouchers with 1-click code copying.

---

### ⚙️ 2. Restaurant / Server Side (Admin & Staff)
- **Operations Dashboard**:
  - KPI Metrics: Total Revenue (₹), Active Kitchen Orders, Waiting Queue, Staff Workforce.
  - Popular Dishes Aggregation (`GROUP BY menu_item_id ORDER BY total_sold DESC`).
- **Live Order Management Board**:
  - Filter orders by status: **All**, **Pending**, **Preparing**, **Ready**, **Completed**, **Cancelled**.
  - Displays customer contact, Table #, itemized dishes with customer's chosen spice level, and chef notes.
  - 1-Click Status Transitions: *Start Preparing*, *Mark Ready*, *Mark Completed*, *Cancel*.
- **Menu Management (Add Item)**:
  - Add new dishes with category, name, price, veg/non-veg tag, spice customizable toggle, and image.
  - Instant In-Stock / Out-of-Stock toggle button.
  - Delete dish functionality.
- **Staff Management**:
  - Employee directory with designations: *Manager, Head Chef, Sous Chef, Waiter, Cashier, Bartender*.
  - Assign work shifts: *Morning (☀️), Evening (🌆), Night (🌙)*.
  - Track monthly payroll and individual employee salaries.
  - Add and delete staff records.
- **Queue / Waitlist Control**:
  - Monitor all waiting parties with token numbers.
  - One-click *Seat Table* to mark customers seated as tables clear up.
- **Promotional Offers Management**:
  - Create promotional discount codes with custom percentage, minimum order amount, and validity dates.
  - Activate, pause, or remove offers.

---

## 🗄️ Database Design (DBMS Viva Ready)

The database is built on **SQLite3** with strict relational integrity (`PRAGMA foreign_keys = ON;`).

### Relational Schema Diagram:
```
+------------------+         +-------------------+
|      users       |1       *|      orders       |
+------------------+---------+-------------------+
| id (PK)          |         | id (PK)           |
| name             |         | customer_id (FK)  |
| email (UNIQUE)   |         | order_type        |
| password         |         | table_number      |
| phone            |         | total_amount      |
| role             |         | discount_amount   |
| created_at       |         | final_amount      |
+------------------+         | status            |
         |1                  | offer_code        |
         |                   | created_at        |
         |*                  +-------------------+
+------------------+                   |1
|      queue       |                   |
+------------------+                   |*
| id (PK)          |         +-------------------+         +-------------------+
| customer_id (FK) |         |    order_items    |*       1|    menu_items     |
| customer_name    |         +-------------------+---------+-------------------+
| party_size       |         | id (PK)           |         | id (PK)           |
| token_number     |         | order_id (FK)     |         | category_id (FK)  |
| status           |         | menu_item_id (FK) |         | name              |
| created_at       |         | quantity          |         | price             |
+------------------+         | price_per_unit    |         | diet_type         |
                             | spice_level       |         | is_spicy_custom   |
+------------------+         | item_total        |         | is_available      |
|     reviews      |         +-------------------+         +-------------------+
+------------------+                                                 |*
| id (PK)          |                                                 |1
| customer_id (FK) |                                       +-------------------+
| menu_item_id (FK)|                                       |    categories     |
| rating (1-5)     |                                       +-------------------+
| comment          |                                       | id (PK)           |
+------------------+                                       | name, icon        |
                                                           +-------------------+
```

### Key DBMS Concepts Demonstrated:
1. **Entity-Relationship Normalization**: 3NF normalized tables avoiding data redundancy.
2. **Foreign Key Cascades**: `ON DELETE CASCADE` on `order_items` ensures orphaned rows are avoided when parent orders are removed.
3. **Check Constraints**:
   - `price > 0`
   - `quantity > 0`
   - `rating BETWEEN 1 AND 5`
   - `order_type IN ('DineIn', 'TakeAway')`
   - `status IN ('Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled')`
4. **ACID Transactions**: In `/checkout`, inserting into `orders` and multiple `order_items` is wrapped inside a single atomic `conn.commit()` / `conn.rollback()`.
5. **Relational Aggregations**:
   - `SUM(final_amount)` for revenue calculation.
   - `COUNT(*)` for waiting queue and order volume.
   - `GROUP BY menu_item_id ORDER BY total_sold DESC` for identifying top-selling dishes.

---

## 🚀 How to Run the Project Locally

### Step 1: Install Dependencies
Ensure Python 3.10+ is installed, then run:
```bash
pip install -r requirements.txt
```

### Step 2: Initialize & Seed Database
*(The database automatically seeds itself on first run, or you can run manually:)*
```bash
python database.py
```

### Step 3: Start the Flask Application
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Credentials (1-Click Login Included)

On the `/login` page, you will find **1-Click Demo Login** buttons for easy presentation:

| Role | Email | Password | Access |
| :--- | :--- | :--- | :--- |
| **Admin / Manager** | `admin@restaurant.com` | `admin123` | Full access to Restaurant & Staff Portal |
| **Customer (Demo)** | `customer@gmail.com` | `customer123` | Ordering, Cart, Queue, Reviews |
| **New Customer** | *Any email* | *Your password* | Register via `/signup` |

---

## 💡 Quick Viva / Presentation Q&A

**Q: Why use SQLite for this project?**  
> *A:* SQLite is a serverless, self-contained relational database engine that stores data in a single `.db` file. It supports standard SQL syntax, foreign keys, transactions, and check constraints without requiring external server setup, making it lightweight, zero-configuration, and perfect for academic evaluation.

**Q: How does the system handle item customizations like spice level?**  
> *A:* In `order_items`, `spice_level` is stored as an attribute of the relation along with `quantity` and `price_per_unit`. In the session cart, items are keyed using a composite identifier `f"{item_id}_{spice_level}"`, allowing a customer to order 1 Mild and 1 Extra Spicy portion of the same dish as distinct line items.

**Q: How is the transaction maintained during checkout?**  
> *A:* When a customer checks out, the order record is created in `orders` and all line items are inserted into `order_items`. If any database constraint fails, `conn.rollback()` is triggered so partial orders are never left in the database.
