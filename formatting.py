import json
import random

with open('purchase_history.json', 'r') as file:
    data = json.load(file)

reformatted_data = []

for item in data:
    new_entry = {
        "PurchaseID": item.get("PurchaseID"),
        "StoreID": 4,
        "Time": item.get("Time"),
        "Product": item.get("Product"),
        "Quantity": item.get("Quantity"),
        "Price": item.get("Price"),
        "Type": item.get("Type"),
        "Brand": item.get("Brand")
    }
    reformatted_data.append(new_entry)

with open('reformatted_purchase_history.json', 'w') as outfile:
    json.dump(reformatted_data, outfile, indent=4)

print("Reformatted JSON saved as 'reformatted_purchase_history.json'")
