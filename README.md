# FreshBasket – AWS SmartBridge SkillWallet Project ☁️🛒

FreshBasket is a cloud-based e-commerce web application developed as part of the **AWS SmartBridge SkillWallet Program**.  
The project focuses on building and deploying a **scalable web application using AWS cloud services**.

FreshBasket allows users to order fruits and vegetables with dedicated modules for **Users, Sellers, and Admins**, hosted and managed using AWS infrastructure.

---

## Program Details

- **Program Name:** AWS SmartBridge – SkillWallet  
- **Project Type:** Cloud-Based Full Stack Application  
- **Cloud Provider:** Amazon Web Services (AWS)

---

## Introduction

FreshBasket is designed to demonstrate real-world usage of AWS services in a full-stack application.  
The frontend interacts with a Flask-based backend deployed on AWS EC2, while data storage and messaging are handled using AWS managed services.

---

## AWS Services Used

- **Amazon EC2** – Hosting the Flask backend application
- **AWS IAM** – User roles, permissions, and secure access management
- **Amazon DynamoDB** – NoSQL database for users, sellers, products, and orders
- **Amazon SNS** – Notifications for order updates and system alerts

---

## Screenshots

### Login Page
![Login Page](/screenshots/login.png)

### Home Page
![Home Page](/screenshots/home.png)
![Home Page](/screenshots/home2.png)

### Category Page
![Category Page](/screenshots/categories.png)

### Profile Page
![Profile Page](/screenshots/profile.png)

---

### Seller Module

#### Product Management
![Seller Dashboard](/screenshots/seller.png)

#### Add Product
![Add Product Page](/screenshots/seller_add.png)

---

### Admin Panel
![Admin Page](/screenshots/admin.png)

---

## Features

### User Features
- User authentication and profile management
- Browse products by category
- Place orders
- Receive notifications via AWS SNS

---

### Seller Features
- Separate seller login
- Add, update, and delete products
- Manage inventory using DynamoDB

---

### Admin Features
- Admin login
- Manage sellers and products
- Monitor platform activity

---

## Database Design (DynamoDB)

### Users Table
- `user_id` (Partition Key)
- `username`
- `email`
- `address`
- `phone`

### Products Table
- `product_id` (Partition Key)
- `seller_id`
- `name`
- `price`
- `category`
- `quantity`
- `image_url`

### Sellers Table
- `seller_id` (Partition Key)
- `username`
- `address`
- `delivery_type`

### Orders Table
- `order_id` (Partition Key)
- `user_id`
- `product_id`
- `order_status`
- `timestamp`

---

## Technologies Used

- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** Amazon DynamoDB
- **Cloud Platform:** AWS (EC2, IAM, SNS)
- **Version Control:** Git & GitHub

---

## Deployment

- Backend deployed on **Amazon EC2**
- IAM roles attached to EC2 for secure DynamoDB & SNS access
- Application accessed via EC2 public IP or domain

---

## How to Run Locally

```bash
pip install -r requirements.txt
python main.py
