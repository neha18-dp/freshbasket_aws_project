from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import boto3
import uuid
from boto3.dynamodb.conditions import Key

app = Flask(__name__)
app.secret_key = "freshbasket_aws_secret"

# ---------------- AWS CONFIG ----------------
REGION = "us-east-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client('sns', region_name=REGION)


users_table = dynamodb.Table("Users")
products_table = dynamodb.Table("Products")
cart_table = dynamodb.Table("Cart")
orders_table = dynamodb.Table("Orders")
sellers_table = dynamodb.Table("Sellers")

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:975050316116:FreshBasket'
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
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]

    res = users_table.get_item(Key={"username": username})
    if "Item" not in res:
        return "User not found"

    session["username"] = username
    session["role"] = res["Item"]["role"]

    if session["role"] == "admin":
        return redirect(url_for("admin"))
    elif session["role"] == "seller":
        return redirect(url_for("seller"))
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
            UpdateExpression="""
                SET email=:e, phone=:p, address=:a
            """,
            ExpressionAttributeValues={
                ":e": request.form["email"],
                ":p": request.form["phone"],
                ":a": request.form["address"]
            }
        )
        success = True

    user = users_table.get_item(Key={"username": session["username"]}).get("Item")
    return render_template("profile.html", user=user, success=success)

# ---------------- USER ----------------
@app.route("/home")
def home():
    products = products_table.scan().get("Items", [])
    return render_template("home.html", products=products)

@app.route("/addtocart/<pid>", methods=["POST"])
def add_to_cart(pid):
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
    res = cart_table.query(
        KeyConditionExpression=Key("username").eq(session["username"])
    )
    return render_template("order.html", cart=res.get("Items", []))

@app.route("/placeorder", methods=["POST"])
def placeorder():
    order_id = str(uuid.uuid4())

    cart_items = cart_table.query(
        KeyConditionExpression=Key("username").eq(session["username"])
    ).get("Items", [])

    orders_table.put_item(
        Item={
            "order_id": order_id,
            "username": session["username"],
            "items": cart_items,
            "status": "Ordered"
        }
    )

    for item in cart_items:
        cart_table.delete_item(
            Key={
                "username": session["username"],
                "product_id": item["product_id"]
            }
        )

    return redirect(url_for("myorders"))

@app.route("/myorders")
def myorders():
    orders = orders_table.scan().get("Items", [])
    user_orders = [o for o in orders if o["username"] == session["username"]]
    return render_template("myorders.html", orders=user_orders)

# ---------------- SELLER ----------------
@app.route("/seller")
def seller():
    return render_template("seller.html")

@app.route("/seller/add-product", methods=["POST"])
def seller_add_product():
    products_table.put_item(
        Item={
            "product_id": str(uuid.uuid4()),
            "name": request.form["fruit_name"],
            "weight": request.form["fruit_weight"],
            "rate": int(request.form["fruit_rate"]),
            "description": request.form["fruit_desc"],
            "image": request.form["fruit_image"],
            "category": request.form["fruit_category"]
        }
    )
    return redirect(url_for("seller"))

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    return render_template(
        "admin.html",
        users=users_table.scan().get("Items", []),
        products=products_table.scan().get("Items", []),
        orders=orders_table.scan().get("Items", [])
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
