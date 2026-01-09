import streamlit as st
import json
import os
import pandas as pd
import requests
from datetime import datetime

# Configuration
CURRENCY_API = "https://api.exchangerate-api.com/v4/latest"
DATA_FILE = "expenses.json"

class ExpenseTracker:
    def __init__(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)
        self.load_data()

    def load_data(self):
        with open(DATA_FILE, 'r') as f:
            self.data = json.load(f)

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def register_user(self, identifier, password=None, method="email"):
        if identifier in self.data:
            return False, "User already exists!"
        
        self.data[identifier] = {
            "user_id": f"{identifier}_{datetime.now().strftime('%Y%m%d')}",
            "password": password,
            "auth_method": method,
            "currency": "USD",
            "transactions": []
        }
        self.save_data()
        return True, "Registration successful!"

# --- UI Setup ---
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰")
tracker = ExpenseTracker()

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# --- Sidebar Navigation ---
st.sidebar.title("💰 Expense Manager")
if st.session_state.logged_in:
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Expense", "Currency Converter", "Settings", "Logout"])
else:
    menu = st.sidebar.radio("Access", ["Login", "Register"])

# --- Authentication Logic ---
if menu == "Register":
    st.header("Create Account")
    reg_type = st.selectbox("Register with", ["Email", "Apple ID"])
    with st.form("register_form"):
        u_id = st.text_input("Email/Apple ID")
        u_pw = st.text_input("Password", type="password") if reg_type == "Email" else None
        if st.form_submit_button("Sign Up"):
            success, msg = tracker.register_user(u_id, u_pw, reg_type.lower())
            if success: st.success(msg)
            else: st.error(msg)

elif menu == "Login":
    st.header("Login")
    l_id = st.text_input("Identifier (Email/Apple ID)")
    l_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if l_id in tracker.data and (tracker.data[l_id]["auth_method"] == "apple" or tracker.data[l_id]["password"] == l_pw):
            st.session_state.logged_in = True
            st.session_state.user = l_id
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- Main App Logic ---
if st.session_state.logged_in:
    user_data = tracker.data[st.session_state.user]
    
    if menu == "Dashboard":
        st.title(f"Welcome, {st.session_state.user} 👋")
        
        if user_data["transactions"]:
            df = pd.DataFrame(user_data["transactions"])
            
            # Key Metrics
            total_spent = df['amount'].sum()
            st.metric("Total Expenses", f"{total_spent} {user_data['currency']}")
            
            # Expense Table
            st.subheader("Recent Transactions")
            st.dataframe(df, use_container_width=True)
            
            # Visuals
            st.subheader("Spending by Category")
            chart_data = df.groupby("category")["amount"].sum()
            st.bar_chart(chart_data)
        else:
            st.info("No transactions found. Start by adding one!")

    elif menu == "Add Expense":
        st.header("Record New Expense")
        with st.form("expense_form"):
            amt = st.number_input("Amount", min_value=0.01)
            cat = st.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Health", "Other"])
            desc = st.text_input("Description")
            if st.form_submit_button("Add"):
                new_exp = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "amount": amt,
                    "category": cat,
                    "description": desc
                }
                tracker.data[st.session_state.user]["transactions"].append(new_exp)
                tracker.save_data()
                st.success("Expense Added!")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
