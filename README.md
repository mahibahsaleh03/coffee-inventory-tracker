## Local Setup Instructions

### 1. Prerequisites

- Python 3.8+
- MySQL Server (local)
- MongoDB (local)

### 2. Clone the Project

```bash
git clone https://github.com/YOUR_USERNAME/coffee-inventory-tracker.git
cd coffee-inventory-tracker
```

### 3. 🛠 Run Setup Script

```bash
chmod +x setup.sh   # Only needed once
./setup.sh
```

This will:
- Create a virtual environment (`venv`)
- Install Python dependencies from `requirements.txt`
- Copy `.env.example` → `.env` (if `.env` doesn’t exist)
- Exit and ask you to **edit `.env`** before continuing

### 3. Set Up MySQL Database

After editing your `.env`, run:
```bash
mysql -u root -p < coffee_database.sql
```

This creates the full schema.

### 4. Start MongoDB locally

```bash
mongod
```

### 4. ▶️ Start the App

```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

Then go to: [http://127.0.0.1:5000](http://127.0.0.1:5000)