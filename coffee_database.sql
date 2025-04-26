-- Create database
DROP DATABASE IF EXISTS coffee_db;
CREATE DATABASE IF NOT EXISTS coffee_db;
USE coffee_db;

-- Users table (stores)
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL,
  password VARCHAR(255) NOT NULL,
  StoreName VARCHAR(255) NOT NULL
);

-- Suppliers
CREATE TABLE suppliers (
  SupplierID INT AUTO_INCREMENT PRIMARY KEY,
  SupplierName VARCHAR(255),
  Contact VARCHAR(255),
  Location VARCHAR(255)
);

-- Coffee Beans
CREATE TABLE coffee_beans (
  BeanID INT AUTO_INCREMENT PRIMARY KEY,
  Type VARCHAR(100),
  Brand VARCHAR(100),
  Flavor VARCHAR(100),
  Origin VARCHAR(100),
  Price DECIMAL(5,2),
  ProductionDate DATE,
  SupplierID INT,
  FOREIGN KEY (SupplierID) REFERENCES suppliers(SupplierID)
);

-- Inventory (per store)
CREATE TABLE inventory (
  InventoryID INT AUTO_INCREMENT PRIMARY KEY,
  BeanID INT,
  Amount INT,
  StoreID INT,
  ExpirationDate DATE,
  FOREIGN KEY (BeanID) REFERENCES coffee_beans(BeanID),
  FOREIGN KEY (StoreID) REFERENCES users(id)
);

-- Products (e.g., latte, cold brew)
CREATE TABLE products (
  ProductID INT AUTO_INCREMENT PRIMARY KEY,
  Price DECIMAL(5,2),
  Name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE purchase_history (
	PurchaseID INT AUTO_INCREMENT PRIMARY KEY,
    StoreID INT,
    Product VARCHAR(100) NOT NULL,
    Quantity INT,
    Price DECIMAL(5,2),
    Type VARCHAR(100),
    Brand VARCHAR(100)
);

-- Sample Suppliers
INSERT INTO suppliers (SupplierName, Contact, Location) VALUES
('bluemountain', 'contact@bluemountain.com', 'Jamaica'),
('ethiopiansunbeans', 'info@ethiopiansunbeans.com', 'Ethiopia'),
('colombianexporters', 'support@colombianexporters.co', 'Colombia'),
('kenyabeans', 'hello@kenyabeans.org', 'Kenya'),
('brazilsantos', 'sales@brazilsantos.com', 'Brazil'),
('sumatrabeanimports', 'orders@sumatrabeanimports.id', 'Indonesia');

-- Sample Coffee Beans
INSERT INTO coffee_beans (Type, Brand, Flavor, Origin, Price, ProductionDate, SupplierID) VALUES
('Arabica', 'Blue Mountain', 'Nutty & Mild', 'Jamaica', 18.99, '2025-02-01', 1),
('Robusta', 'Vietnam Gold', 'Bold & Earthy', 'Vietnam', 12.50, '2025-03-15', 6),
('Liberica', 'Borneo Blend', 'Smoky & Woody', 'Malaysia', 14.75, '2025-04-10', 6),
('Arabica', 'Ethiopian Yirgacheffe', 'Floral & Bright', 'Ethiopia', 16.99, '2025-02-28', 2),
('Arabica', 'Colombian Supremo', 'Chocolate & Nutty', 'Colombia', 15.25, '2025-05-12', 3),
('Arabica', 'Guatemalan Huehuetenango', 'Fruity & Winey', 'Guatemala', 16.00, '2025-06-01', 3),
('Arabica', 'Kenyan AA', 'Berry & Citrus', 'Kenya', 17.50, '2025-04-22', 4),
('Robusta', 'Indian Cherry', 'Harsh & Heavy Body', 'India', 11.50, '2025-03-05', 6),
('Arabica', 'Brazil Santos', 'Sweet & Nutty', 'Brazil', 13.95, '2025-07-01', 5),
('Arabica', 'Costa Rican Tarrazú', 'Bright & Clean', 'Costa Rica', 14.60, '2025-08-15', 3),
('Arabica', 'Panama Geisha', 'Tea-like & Floral', 'Panama', 22.00, '2025-09-20', 3),
('Arabica', 'Sumatra Mandheling', 'Earthy & Herbal', 'Indonesia', 15.75, '2025-05-30', 6),
('Arabica', 'Honduras Marcala', 'Cocoa & Sweet', 'Honduras', 14.40, '2025-04-14', 3),
('Arabica', 'Mexican Chiapas', 'Light & Nutty', 'Mexico', 13.20, '2025-06-18', 3),
('Arabica', 'Peruvian Chanchamayo', 'Mild & Sweet', 'Peru', 13.80, '2025-07-25', 3),
('Arabica', 'Rwandan Bourbon', 'Fruity & Vibrant', 'Rwanda', 15.30, '2025-08-10', 2),
('Arabica', 'Tanzanian Peaberry', 'Citrusy & Bright', 'Tanzania', 15.90, '2025-09-05', 4),
('Robusta', 'Ugandan Robusta', 'Bold & Strong', 'Uganda', 12.00, '2025-03-30', 4),
('Arabica', 'El Salvador Pacamara', 'Sweet & Spicy', 'El Salvador', 16.10, '2025-10-15', 3),
('Arabica', 'Nicaragua Segovia', 'Balanced & Cocoa', 'Nicaragua', 14.70, '2025-11-01', 3);

-- Sample Products, select type of coffee bean to prep at purchase
INSERT INTO products (Name, Price) VALUES
('Latte', 5.25), ('Espresso', 3.75), ('Cold Brew', 4.65), ('Americano', 4.25), 
('Cappuccino', 5.25), ('Flat White', 5.25), 
('Nitro Cold Brew', 5.75), ('Iced Coffee', 3.95), ('Iced Coffee Vertica', 3.95), 
('Iced Shaken Espresso', 4.45), ('Macchiato', 5.95), ('Mocha', 5.95);

INSERT INTO purchase_history (StoreID, Product, Quantity, Price, Type, Brand) VALUES
(1, 'Macchiato', 1, 5.95, 'Arabica', 'Blue Mountain');
