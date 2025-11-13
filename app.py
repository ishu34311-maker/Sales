import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from datetime import datetime

# ====== MongoDB Connection ======
MONGO_URI = st.secrets["mongo"]["uri"]
client = MongoClient(MONGO_URI)
db = client["fastfood_store"]

users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]

# ====== Admin Credentials ======
ADMIN_USERNAME = st.secrets["admin"]["username"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# ====== Helper Functions ======
def user_exists(username):
    return users_col.find_one({"username": username})

def add_user(username, password):
    users_col.insert_one({"username": username, "password": password})

def add_product(name, price):
    products_col.insert_one({"name": name, "price": price})

def get_products():
    return list(products_col.find({}, {"_id": 0}))

def add_order(username, cart):
    order_data = {
        "username": username,
        "cart": cart,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    orders_col.insert_one(order_data)

def get_user_orders(username):
    return list(orders_col.find({"username": username}, {"_id": 0}))

def get_all_orders():
    return list(orders_col.find({}, {"_id": 0}))

# ====== UI ======
st.set_page_config(page_title="Fast Food Store", layout="centered")

st.title("🍔 Fast Food Store Management System")

menu = st.sidebar.selectbox("Select Role", ["Login", "About"])

if menu == "About":
    st.info("This is a Fast Food Store Management System using Streamlit & MongoDB.")

if menu == "Login":
    role = st.radio("Login as:", ["Admin", "User"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if role == "Admin":
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.success("Welcome Admin!")
                admin_action = st.selectbox("Choose Action", ["Create User", "Add Product", "View Sales Report"])

                if admin_action == "Create User":
                    new_user = st.text_input("New Username")
                    new_pass = st.text_input("New Password", type="password")
                    if st.button("Add User"):
                        if user_exists(new_user):
                            st.warning("User already exists!")
                        else:
                            add_user(new_user, new_pass)
                            st.success(f"User '{new_user}' created successfully!")

                elif admin_action == "Add Product":
                    prod_name = st.text_input("Product Name")
                    prod_price = st.number_input("Price", min_value=0.0, step=0.5)
                    if st.button("Add Product"):
                        add_product(prod_name, prod_price)
                        st.success(f"Product '{prod_name}' added successfully!")

                    st.subheader("📋 Current Menu")
                    products = get_products()
                    if products:
                        st.table(pd.DataFrame(products))
                    else:
                        st.info("No products found.")

                elif admin_action == "View Sales Report":
                    orders = get_all_orders()
                    if not orders:
                        st.info("No sales data yet.")
                    else:
                        sales_data = []
                        for order in orders:
                            for item in order["cart"]:
                                sales_data.append({
                                    "Product": item["name"],
                                    "Price": item["price"],
                                    "Date": order["timestamp"].split(" ")[0]
                                })

                        df = pd.DataFrame(sales_data)
                        st.subheader("📊 Sales Table")
                        st.dataframe(df)

                        st.subheader("📈 Daily Sales Chart")
                        fig = px.bar(df, x="Date", y="Price", color="Product", title="Daily Sales Overview")
                        st.plotly_chart(fig)

            else:
                st.error("Invalid Admin credentials!")

        elif role == "User":
            user = users_col.find_one({"username": username, "password": password})
            if user:
                st.success(f"Welcome {username}!")
                st.subheader("🍟 Menu")
                products = get_products()

                if products:
                    df = pd.DataFrame(products)
                    st.table(df)

                    cart = []
                    for product in products:
                        if st.button(f"Add {product['name']} to cart"):
                            cart.append(product)
                            st.success(f"Added {product['name']} to cart")

                    if st.button("Buy Now"):
                        if cart:
                            add_order(username, cart)
                            st.success("✅ Order placed successfully!")
                        else:
                            st.warning("Cart is empty.")

                    st.subheader("📦 Your Orders")
                    user_orders = get_user_orders(username)
                    if user_orders:
                        for order in user_orders:
                            st.write(f"🕓 {order['timestamp']}")
                            st.table(pd.DataFrame(order["cart"]))
                    else:
                        st.info("No orders found.")
                else:
                    st.warning("Menu is empty. Please check back later.")
            else:
                st.error("Invalid username or password.")
