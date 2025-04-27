from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import pymysql
import os
import json
from dotenv import load_dotenv
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL setup
mysql = pymysql.connect(
    host='localhost',
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DB'),
    cursorclass=pymysql.cursors.DictCursor
)

# Import existing coffee store credientials
with open('logins.json', 'r') as file:
    data = json.load(file)

for login in data['logins']:
    with mysql.cursor() as cursor:
            username = login['username']
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                cursor.execute(
                    "INSERT INTO users (username, password, StoreName) VALUES (%s, %s, %s)",
                    (username, generate_password_hash(login['password']), login['store_name'])
                )
                mysql.commit()

# Import purchase history for store 4
with open('purchase_history.json', 'r') as file:
    data = json.load(file)

for purchase in data:
    with mysql.cursor() as cursor:
            purchase_id = purchase['PurchaseID']
            store_id = purchase['StoreID']
            time = purchase['Time']
            product = purchase['Product']
            quantity = purchase['Quantity']
            price = purchase['Price']
            type_ = purchase['Type']
            brand = purchase['Brand']

            cursor.execute("SELECT * FROM purchase_history WHERE purchaseID = %s", (purchase_id,))
            this_purchase = cursor.fetchone()
            if not this_purchase:
                cursor.execute(
                    """
                    INSERT INTO purchase_history (PurchaseID, StoreID, Time, Product, Quantity, Price, Type, Brand)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (purchase['PurchaseID'], purchase['StoreID'], purchase['Time'], purchase['Product'], purchase['Quantity'], purchase['Price'], purchase['Type'], purchase['Brand'])
                )
                mysql.commit()

# MongoDB setup
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['coffee_tracker_mongo']
# Reset reviews database when restarting app
mongo_db.customer_reviews.delete_many({})

# Load reviews dataset for coffee_shop_4 into MongoDB
with open('review_dataset.json', 'r') as file:
    reviews = json.load(file)
mongo_db.customer_reviews.insert_many(reviews)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id_, username, password):
        self.id = id_
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    with mysql.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user['id'], user['username'], user['password'])
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with mysql.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
                login_user(User(user['id'], user['username'], user['password']))
                return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        store_name = request.form['store_name']
        with mysql.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, StoreName) VALUES (%s, %s, %s)",
                (username, password, store_name)
            )
            mysql.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    store_id = session.get('_user_id')

    with mysql.cursor() as cursor:
        cursor.execute("""
            SELECT cb.BeanID, cb.Type, cb.Brand, cb.Flavor, i.ExpirationDate, i.Amount
            FROM coffee_beans cb
            JOIN inventory i ON cb.BeanID = i.BeanID
            WHERE i.StoreID = %s
        """, (store_id,))
        inventory = cursor.fetchall()

    LOW_STOCK_THRESHOLD = 20
    # Find low-stock items for this store
    with mysql.cursor() as cursor:
        cursor.execute("""
            SELECT cb.Brand, cb.Type, i.Amount
            FROM coffee_beans cb
            JOIN inventory i ON cb.BeanID = i.BeanID
            WHERE i.StoreID = %s AND i.Amount < %s
        """, (store_id, LOW_STOCK_THRESHOLD))
        low_stock = cursor.fetchall()

    with mysql.cursor() as cursor:
        cursor.execute("SELECT StoreName FROM users WHERE id = %s", (store_id,))
        user_row = cursor.fetchone()
        store_name = user_row['StoreName'].strip() if user_row else ''

    reviews = list(mongo_db.customer_reviews.find({
        'shop_name': {'$regex': f'^{store_name}$', '$options': 'i'}
    }))

    return render_template(
        'dashboard.html',
        inventory=inventory,
        reviews=reviews,
        low_stock=low_stock,
    )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/review', methods=['GET', 'POST'])
def review():
    error = None

    if request.method == 'POST':
        shop_name = request.form['shop_name'].strip()
        rating = int(request.form['rating'])
        review_text = request.form['review']

        # Check if store exists
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users
                WHERE LOWER(StoreName) = LOWER(%s)
            """, (shop_name,))
            store = cursor.fetchone()

        if not store:
            error = "⚠️ The store does not exist. Please check your spelling!"
            return render_template('review.html', error=error)

        # Store exists — insert review
        review_data = {
            'shop_name': store['StoreName'],  # use official name
            'rating': rating,
            'review': review_text
        }

        mongo_db.customer_reviews.insert_one(review_data)
        return render_template('thank_you.html')

    return render_template('review.html', error=error)

@app.route('/')
def index():
    return render_template('home.html')

def update_inventory(bean_id, new_amount, store_id):
    with mysql.cursor() as cursor:
        cursor.execute("""
            UPDATE inventory
            SET Amount = %s + Amount, ExpirationDate = DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
            WHERE BeanID = %s AND StoreID = %s
        """, (new_amount, bean_id, store_id))
        mysql.commit()

@app.route('/add-inventory', methods=['GET', 'POST'])
@login_required
def add_inventory():
    store_id = session.get('_user_id')

    if request.method == 'POST':
        bean_id = request.form['bean_id']
        amount = request.form['amount']
        SupplierName = request.form['SupplierName']

        with mysql.cursor() as cursor:
            cursor.execute("SELECT * from coffee_beans where SupplierID=(SELECT SupplierID from suppliers where SupplierName=%s) AND BeanID=%s", (SupplierName, bean_id,))
            s = cursor.fetchone()
            if not s:
                return f"out of stock"
            else:
                cursor.execute("SELECT ProductionDate from coffee_beans WHERE BeanID=%s", (bean_id,))
                productionDate = cursor.fetchone()['ProductionDate']
                cursor.execute("SELECT * FROM inventory WHERE storeID = %s AND beanID= %s", (store_id, bean_id,))
                store = cursor.fetchone()
                if store:
                    update_inventory(bean_id, amount, store_id)
                else:
                # Insert new inventory row for this store
                    cursor.execute("""
                        INSERT INTO inventory (BeanID, Amount, StoreID, ExpirationDate)
                        VALUES (%s, %s, %s, %s)
                        """, (bean_id, amount, store_id, productionDate))
                    mysql.commit()
        return redirect(url_for('dashboard'))

    # GET: showing all beans from suppliers
    with mysql.cursor() as cursor:
        cursor.execute("SELECT BeanID, Brand, Type FROM coffee_beans") 
        available_beans = cursor.fetchall()
        cursor.execute("SELECT SupplierName FROM suppliers")
        suppliers = cursor.fetchall()

    return render_template('add_inventory.html', beans=available_beans, suppliers=suppliers)

@app.route('/purchase_history', methods=['GET'])
@login_required
def purchase_history():
    store_id = session.get('_user_id')

    with mysql.cursor() as cursor:
        cursor.execute("SELECT * from purchase_history WHERE StoreID=%s ORDER BY Time DESC", (store_id))
        purchase_history = cursor.fetchall()
    if purchase_history:

        df_purchased = pd.DataFrame(purchase_history)

        brand_totals = df_purchased.groupby('Brand')['Quantity'].sum().reset_index()
        top3 = brand_totals.sort_values(by='Quantity', ascending=False).head(3)
        net_quantity = brand_totals['Quantity'].sum()
        top3_quantity = top3['Quantity'].sum()
        top3_percentage = float((top3_quantity / net_quantity) * 100)

        plt.figure(figsize=(8,5))
        plt.barh(top3['Brand'], top3['Quantity'], color='#5e4033')
        plt.xlabel('Quantity Sold')
        plt.title('Top 3 Coffee Bean Brands by Quantity Sold')
        plt.gca().invert_yaxis()  # Highest at top

        plt.text(
            0.95, 0.05,  # (x,y) position in figure (in axis coordinates)
            f"Top 3 Quantity: {top3_percentage:.2f}% of Total",
            transform=plt.gca().transAxes,  # Relative to plot, not data
            fontsize=12,
            color='brown',
            ha='right',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray')
        )

        plt.tight_layout()
        plt.savefig('static/img.png')

    return render_template('purchase_history.html', purchase_history=purchase_history)

@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    store_id = session.get('_user_id')

    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        bean_id = int(request.form['bean_id'])
        quantity = int(request.form['quantity'])

        # Check if store has enough beans required in inventory
        with mysql.cursor() as cursor:
                # Get current inventory
                cursor.execute("""
                    SELECT Amount FROM inventory
                    WHERE StoreID = %s AND BeanID = %s
                """, (store_id, bean_id))
                row = cursor.fetchone()

                if not row or row['Amount'] < 5:
                    return f"⚠️ Not enough beans in stock to complete this order!"

                cursor.execute("""
                    UPDATE inventory
                    SET Amount = Amount - 5
                    WHERE StoreID = %s AND BeanID = %s
                """, (store_id, bean_id))

                # Insert purchase into purchase history
                cursor.execute("""
                    SELECT Name, Price FROM products
                    WHERE ProductID = %s
                """, (product_id))
                product = cursor.fetchone()

                cursor.execute("""
                    SELECT Brand, Type FROM coffee_beans
                    WHERE BeanID = %s
                """, (bean_id))
                bean_used = cursor.fetchone()

                cursor.execute("""
                    INSERT INTO purchase_history (StoreID, Time, Product, Quantity, Price, Type, Brand)
                    VALUES (%s, NOW(), %s, %s, %s, %s, %s)
                """, (store_id, product['Name'], quantity, product['Price'], bean_used['Type'], bean_used['Brand']))

                mysql.commit()

        return redirect(url_for('dashboard'))

    # GET: show available products & beans in stock
    with mysql.cursor() as cursor:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        cursor.execute("""SELECT coffee_beans.BeanID, coffee_beans.Brand, coffee_beans.Type 
                       FROM coffee_beans
                       JOIN inventory ON coffee_beans.BeanID = inventory.BeanID
                       WHERE inventory.StoreID = %s""", (store_id,)) 
        available_beans = cursor.fetchall()

    return render_template('purchase.html', products=products, beans=available_beans)

if __name__ == '__main__':
    app.run(debug=True)


