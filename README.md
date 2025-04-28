## Local Setup Instructions

### 1. Prerequisites

- Python 3.8+
- MySQL Server (local) [https://dev.mysql.com/downloads/mysql/](https://dev.mysql.com/downloads/mysql/)
- MongoDB (local) [https://www.mongodb.com/docs/manual/installation/](https://www.mongodb.com/docs/manual/installation/)

### 2. Clone the Project

```bash
git clone https://github.com/YOUR_USERNAME/coffee-inventory-tracker.git
cd coffee-inventory-tracker
```

### 3. Run Setup Script

```bash
chmod +x setup.sh   # Only needed once
./setup.sh
```

This will:
- Create a virtual environment (`venv`)
- Install Python dependencies from `requirements.txt`
- Copy `.env.example` → `.env` (if `.env` doesn’t exist)
- Exit and ask you to **edit `.env`** before continuing

### 4. Set Up MySQL Database

After editing your `.env`, run:
```bash
mysql -u root -p < coffee_database.sql
```

This creates the full schema. Replace `mysql` with the path to your own if needed. (E.g. `usr/local/mysql`)

### 5. Start MongoDB locally

```bash
mongod
```
or to run MongoDB as a macOS service, run: (Recommended)
```bash
brew services start mongodb-community
```

### 6. Start the App

```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

Then go to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

You're all set!

## Data Preparation
### Overview
The data used in this project is synthetic but inspired by real-world coffee shop datasets such as those found on Kaggle. Our goal was to simulate a working version of a coffee inventory and review tracking system. The intention is to reflect the type of data that would realistically be added by store users themselves through the app's UI (e.g., store accounts, customer reviews, purchase history).

* Store login credentials (`logins.json`) - MySQL
* Purchase history data (`purchase_history.json`) - MySQL
* Customer reviews data (`review_history.json`) - MongoDB

The rest of structured data are directly loaded into MySQL database through `coffee_database.sql` script.
