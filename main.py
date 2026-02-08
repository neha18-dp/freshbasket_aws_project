from flask import Flask, render_template, request, redirect, session, url_for, jsonify

app = Flask(__name__)
app.secret_key = "freshbasket_secret_key"

# -------------------------------------------------
# TEMP DATA (Replace with DB later)
# -------------------------------------------------

products = [
    {"product_id": 1, "name": "Apple", "weight": "1 Kg", "rate": 120,
     "description": "Fresh red apples", "image": "AP.jpg", "category": "fruits"},

    {"product_id": 2, "name": "Banana", "weight": "1 Dozen", "rate": 50,
     "description": "Organic bananas", "image": "banana.jpeg", "category": "fruits"},

    {"product_id": 3, "name": "Tomato", "weight": "1 Kg", "rate": 40,
     "description": "Farm fresh tomatoes", "image": "tomato.webp", "category": "vegetables"},

    {"product_id": 4, "name": "Amla", "weight": "1 Kg", "rate": 60,
     "description": "Vitamin C rich amla", "image": "amla.jpg", "category": "seasonal"}
]

sellers = [
    [1, "seller1", "987", "seller@gmail.com", "21, abc street"],
    [2, "veg seller", "143", "vegseller@gmail.com", "eb colony"]
]

# -------------------------------------------------
# PUBLIC
# -------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    if "role" not in session:
        return redirect(url_for("index"))
    return render_template("home.html")

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")

@app.route("/contactus")
def contactus():
    return render_template("contactus.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "role" not in session:
        return redirect(url_for("index"))

    success = False

    if request.method == "POST":
        session["username"] = request.form["username"]
        success = True

    return render_template("profile.html", success=success)



# -------------------------------------------------
# AUTH
# -------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        session.clear()
        session["username"] = request.form["username"]
        session["role"] = "user"
        session["cart"] = []
        session["orders"] = []
        return redirect(url_for("home"))

    return render_template("registration.html")

@app.route("/login", methods=["POST"])
def login():
    session.clear()
    username = request.form["username"]
    session["username"] = username

    if username == "admin":
        session["role"] = "admin"
        return redirect(url_for("admin_dashboard"))

    elif username.startswith("seller"):
        session["role"] = "seller"
        return redirect(url_for("seller_dashboard"))

    else:
        session["role"] = "user"
        session.setdefault("cart", [])
        session.setdefault("orders", [])
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# -------------------------------------------------
# USER PAGES
# -------------------------------------------------

@app.route("/fruits")
def fruits():
    return render_template("fruits.html",
        data=[p for p in products if p["category"] == "fruits"])

@app.route("/vegetables")
def vegetables():
    return render_template("vegetables.html",
        data=[p for p in products if p["category"] == "vegetables"])

@app.route("/seasonal")
def seasonal():
    return render_template("seasonal.html",
        data=[p for p in products if p["category"] == "seasonal"])

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

@app.route("/address")
def address():
    return render_template("address.html")

# -------------------------------------------------
# CART
# -------------------------------------------------

@app.route("/addtocart/<product_name>", methods=["POST"])
def add_to_cart(product_name):
    if session.get("role") != "user":
        return jsonify({"success": False})

    session.setdefault("cart", [])

    for item in session["cart"]:
        if item["name"] == product_name:
            item["qty"] += 1
            session.modified = True
            return jsonify({"success": True})

    for p in products:
        if p["name"] == product_name:
            session["cart"].append({
                "name": p["name"],
                "price": p["rate"],   # ✅ NUMBER ONLY
                "qty": 1,
                "status": "Pending"
            })
            session.modified = True
            return jsonify({"success": True})

    return jsonify({"success": False})


# @app.route("/cart")
# def cart():
#     return render_template("order.html", cart=session.get("cart", []))


@app.route("/cart")
def cart():
    cart_items = session.get("cart", [])

    for item in cart_items:
        item.setdefault("status", "Pending")
        item["total_price"] = item["price"] * item["qty"]

    return render_template("order.html", cart=cart_items)



@app.route("/placeorder", methods=["POST"])
def placeorder():
    if not session.get("cart"):
        return redirect(url_for("cart"))

    session.setdefault("orders", [])

    for item in session["cart"]:
        item["status"] = "Ordered"
        item["total_price"] = item["price"] * item["qty"]  # ✅ IMPORTANT

        session["orders"].append(item.copy())  # safer copy

    session["cart"] = []
    session.modified = True

    return redirect(url_for("myorders"))


@app.route("/myorders")
def myorders():
    if "role" not in session:
        return redirect(url_for("index"))

    return render_template("myorders.html",
        orders=session.get("orders", []))

# -------------------------------------------------
# SELLER
# -------------------------------------------------

@app.route("/seller")
def seller_dashboard():
    if session.get("role") != "seller":
        return redirect(url_for("index"))
    return render_template("seller.html")

@app.route("/seller/products")
def seller_products():
    return render_template("Productdetails.html", products=products)

@app.route("/seller/add-product", methods=["GET", "POST"])
def seller_add_product():
    if request.method == "POST":
        new_id = max(p["product_id"] for p in products) + 1
        products.append({
            "product_id": new_id,
            "name": request.form["fruit_name"],
            "weight": request.form["fruit_weight"],
            "rate": int(request.form["fruit_rate"]),
            "description": request.form["fruit_desc"],
            "image": request.form["fruit_image"],
            "category": request.form["fruit_category"]
        })
        return redirect(url_for("seller_products"))
    return render_template("addproducts.html")

@app.route("/seller/delete/<int:pid>")
def seller_delete(pid):
    global products
    products = [p for p in products if p["product_id"] != pid]
    return redirect(url_for("seller_products"))

@app.route("/seller/update/<int:pid>", methods=["GET", "POST"])
def seller_update(pid):
    product = next(p for p in products if p["product_id"] == pid)

    if request.method == "POST":
        product["name"] = request.form["name"]
        product["weight"] = request.form["weight"]
        product["rate"] = int(request.form["rate"])
        product["description"] = request.form["description"]
        product["category"] = request.form["category"]
        return redirect(url_for("seller_products"))

    return render_template("edit_product.html", product=product)


# -------------------------------------------------
# ADMIN
# -------------------------------------------------

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("index"))
    return render_template("admin.html")

@app.route("/admin/products")
def admin_products():
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    return render_template("ManageProducts.html", products=products)


@app.route("/admin/fruits")
def admin_fruits():
    return render_template("afruits.html",
        products=[p for p in products if p["category"] == "fruits"])

@app.route("/admin/vegetables")
def admin_vegetables():
    return render_template("avegetables.html",
        products=[p for p in products if p["category"] == "vegetables"])

@app.route("/admin/seasonal")
def admin_seasonal():
    return render_template("aseasonal.html",
        products=[p for p in products if p["category"] == "seasonal"])

@app.route("/admin/sellers")
def admin_sellers():
    return render_template("ManageSellers.html", data=sellers)

@app.route("/admin/delete/<int:pid>")
def admin_delete(pid):
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    global products
    products = [p for p in products if p["product_id"] != pid]

    return redirect(request.referrer or url_for("admin_dashboard"))

@app.route("/admin/seller/delete/<int:seller_id>", methods=["POST"])
def delete_seller(seller_id):
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    global sellers
    sellers = [s for s in sellers if s[0] != seller_id]

    return redirect(url_for("admin_sellers"))



# -------------------------------------------------
# RUN
# -------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
