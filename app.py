from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import pymysql
import os
import json
from dotenv import load_dotenv

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

# MongoDB setup
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['coffee_tracker_mongo']

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
            SELECT cb.BeanID, cb.Type, cb.Brand, cb.Flavor, cb.ExpirationDate, i.Amount
            FROM coffee_beans cb
            JOIN inventory i ON cb.BeanID = i.BeanID
            WHERE i.StoreID = %s
        """, (store_id,))
        inventory = cursor.fetchall()

    LOW_STOCK_THRESHOLD = 10
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
        low_stock=low_stock
    )


def update_inventory(bean_id, new_amount, store_id):
    with mysql.cursor() as cursor:
        cursor.execute("""
            UPDATE inventory
            SET Amount = %s + Amount
            WHERE BeanID = %s AND StoreID = %s
        """, (new_amount, bean_id, store_id))
        mysql.commit()

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
            error = "⚠️ That store name does not exist. Please check your spelling!"
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

@app.route('/add-inventory', methods=['GET', 'POST'])
@login_required
def add_inventory():
    store_id = session.get('_user_id')

    if request.method == 'POST':
        bean_id = request.form['bean_id']
        amount = request.form['amount']
        
        with mysql.cursor() as cursor:
            cursor.execute("SELECT * FROM inventory where storeID = %s AND beanID= %s", (store_id, bean_id,))
            store = cursor.fetchone()
            if store:
                update_inventory(bean_id, amount, store_id)
            else:
         # Insert new inventory row for this store
                cursor.execute("""
                    INSERT INTO inventory (BeanID, Amount, StoreID)
                    VALUES (%s, %s, %s)
                     """, (bean_id, amount, store_id))
                mysql.commit()
        return redirect(url_for('dashboard'))

    # GET: show form with beans not yet in store's inventory
    with mysql.cursor() as cursor:
        cursor.execute("SELECT BeanID, Brand, Type FROM coffee_beans") 
        available_beans = cursor.fetchall()
        cursor.execute("SELECT Contact FROM suppliers")
        suppliers = cursor.fetchall()

    return render_template('add_inventory.html', beans=available_beans, suppliers=suppliers)

@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    store_id = session.get('_user_id')

    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])

        # Fetch all bean requirements for this product
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT pb.BeanID, pb.AmountRequired
                FROM product_bean_usage pb
                WHERE pb.ProductID = %s
            """, (product_id,))
            bean_requirements = cursor.fetchall()

        # Check if store has enough of each bean
        with mysql.cursor() as cursor:
            for req in bean_requirements:
                bean_id = req['BeanID']
                total_needed = req['AmountRequired'] * quantity

                # Get current inventory
                cursor.execute("""
                    SELECT Amount FROM inventory
                    WHERE StoreID = %s AND BeanID = %s
                """, (store_id, bean_id))
                row = cursor.fetchone()

                if not row or row['Amount'] < total_needed:
                    return f"⚠️ Not enough stock of Bean ID {bean_id} to complete this order."

            # Deduct each bean from inventory
            for req in bean_requirements:
                bean_id = req['BeanID']
                total_needed = req['AmountRequired'] * quantity

                cursor.execute("""
                    UPDATE inventory
                    SET Amount = Amount - %s
                    WHERE StoreID = %s AND BeanID = %s
                """, (total_needed, store_id, bean_id))

            mysql.commit()

        return redirect(url_for('dashboard'))

    # GET: show available products
    with mysql.cursor() as cursor:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

    return render_template('purchase.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)
