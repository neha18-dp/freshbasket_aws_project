from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import boto3
import uuid
from boto3.dynamodb.conditions import Key

app = Flask(__name__)
app.secret_key = "freshbasket_aws_secret"

# ---------------- AWS CONFIG ----------------
REGION = "us-east-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

users_table = dynamodb.Table("Users")
products_table = dynamodb.Table("Products")
cart_table = dynamodb.Table("Cart")
orders_table = dynamodb.Table("Orders")
sellers_table = dynamodb.Table("Sellers")

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:796973488755:FreshBasket"

# ---------------- PUBLIC ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")

@app.route("/contactus")
def contactus():
    return render_template("contactus.html")

# ---------------- AUTH ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")

        if not username or not password:
            return "Username and password are required", 400

        users_table.put_item(
            Item={
                "username": username,
                "password": password,
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "role": "user"
            }
        )

        session["username"] = username
        session["role"] = "user"

        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=f"New user registered: {username}",
                Subject="FreshBasket Signup"
            )
        except Exception as e:
            print("SNS error:", e)

        return redirect(url_for("home"))

    return render_template("registration.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    res = users_table.get_item(Key={"username": username})

    if "Item" not in res:
        # fallback for admin/seller accounts
        if username == "admin":
            session["username"] = "admin"
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        elif username.startswith("seller"):
            session["username"] = username
            session["role"] = "seller"
            return redirect(url_for("seller_dashboard"))
        return "User not found"

    session["username"] = username
    session["role"] = res["Item"]["role"]

    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    elif session["role"] == "seller":
        return redirect(url_for("seller_dashboard"))
    return redirect(url_for("home"))



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect(url_for("index"))

    success = False
    if request.method == "POST":
        users_table.update_item(
            Key={"username": session["username"]},
            UpdateExpression="SET email=:e, phone=:p, address=:a",
            ExpressionAttributeValues={
                ":e": request.form["email"],
                ":p": request.form["phone"],
                ":a": request.form["address"]
            }
        )
        success = True

    user = users_table.get_item(Key={"username": session["username"]}).get("Item")
    return render_template("profile.html", user=user, success=success)

# ---------------- HOME / CATEGORIES ----------------
def get_products_by_category(category=None):
    items = products_table.scan().get("Items", [])
    if category:
        items = [p for p in items if p.get("category") == category]
    return items

@app.route("/home")
def home():
    products = get_products_by_category()
    return render_template("home.html", products=products)

@app.route("/fruits")
def fruits():
    products = products_table.scan().get("Items", [])
    fruits_only = [p for p in products if p.get("category") == "fruits"]
    return render_template("fruits.html", data=fruits_only)

@app.route("/vegetables")
def vegetables():
    products = products_table.scan().get("Items", [])
    veg_only = [p for p in products if p.get("category") == "vegetables"]
    return render_template("vegetables.html", data=veg_only)

@app.route("/seasonal")
def seasonal():
    products = products_table.scan().get("Items", [])
    seasonal_only = [p for p in products if p.get("category") == "seasonal"]
    return render_template("seasonal.html", data=seasonal_only)


@app.route("/categories/<category>")
def category_page(category):
    products = get_products_by_category(category)
    return render_template("home.html", products=products)

@app.route("/category/<category_name>")
def category(category_name):
    products = products_table.scan().get("Items", [])
    filtered = [p for p in products if p.get("category", "").lower() == category_name.lower()]
    if not filtered:
        return f"No products found in category '{category_name}'", 404
    return render_template("category.html", data=filtered, category=category_name)


# ---------------- CART ----------------
@app.route("/addtocart/<pid>", methods=["POST"])
def add_to_cart(pid):
    if "username" not in session:
        return jsonify({"success": False})

    cart_table.put_item(
        Item={
            "username": session["username"],
            "product_id": pid,
            "qty": 1,
            "status": "Pending"
        }
    )
    return jsonify({"success": True})

@app.route("/cart")
def cart():
    if "username" not in session:
        return redirect(url_for("index"))

    res = cart_table.query(KeyConditionExpression=Key("username").eq(session["username"]))
    cart_items = res.get("Items", [])
    return render_template("order.html", cart=cart_items)

@app.route("/placeorder", methods=["POST"])
def placeorder():
    if "username" not in session:
        return redirect(url_for("index"))

    cart_items = cart_table.query(KeyConditionExpression=Key("username").eq(session["username"])).get("Items", [])
    if not cart_items:
        return redirect(url_for("cart"))

    order_id = str(uuid.uuid4())
    orders_table.put_item(
        Item={
            "order_id": order_id,
            "username": session["username"],
            "items": cart_items,
            "status": "Ordered"
        }
    )

    # Remove cart items
    for item in cart_items:
        cart_table.delete_item(Key={"username": session["username"], "product_id": item["product_id"]})

    # SNS notification
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"New order placed by {session['username']}, Order ID: {order_id}",
            Subject="FreshBasket Order Notification"
        )
    except Exception as e:
        print("SNS error:", e)

    return redirect(url_for("myorders"))

@app.route("/myorders")
def myorders():
    if "username" not in session:
        return redirect(url_for("index"))

    all_orders = orders_table.scan().get("Items", [])
    user_orders = [o for o in all_orders if o["username"] == session["username"]]
    return render_template("myorders.html", orders=user_orders)

# ---------------- SELLER ----------------
@app.route("/seller")
def seller_dashboard():
    if session.get("role") != "seller":
        return redirect(url_for("index"))
    return render_template("seller.html")

@app.route("/seller/add-product", methods=["POST"])
def seller_add_product():
    product_id = str(uuid.uuid4())
    products_table.put_item(
        Item={
            "product_id": product_id,
            "name": request.form["fruit_name"],
            "weight": request.form["fruit_weight"],
            "rate": int(request.form["fruit_rate"]),
            "description": request.form["fruit_desc"],
            "image": request.form["fruit_image"],
            "category": request.form["fruit_category"]
        }
    )

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"New product added by seller {session['username']}: {request.form['fruit_name']}",
            Subject="FreshBasket New Product"
        )
    except Exception as e:
        print("SNS error:", e)

    return redirect(url_for("seller_dashboard"))

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    users = users_table.scan().get("Items", [])
    products = products_table.scan().get("Items", [])
    orders = orders_table.scan().get("Items", [])

    return render_template("admin.html", users=users, products=products, orders=orders)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
