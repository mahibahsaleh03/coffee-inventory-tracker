#!/bin/bash

# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Please edit .env with your MySQL/Mongo credentials before running the app."
  exit 1
fi

# 4. Prompt to run MySQL schema
read -p "Have you created the MySQL database and run coffee_tracker_schema.sql? (y/n): " dbready
if [[ "$dbready" != "y" ]]; then
  echo "Please set up your database first:"
  echo "    mysql -u root -p < coffee_tracker_schema.sql"
  exit 1
fi

# 5. Option to run app
echo "Starting Flask server..."
python app.py
echo "Setup complete. You can exit with CTRL+C and run with python app.py"
