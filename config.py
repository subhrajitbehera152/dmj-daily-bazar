import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_NAME = os.environ.get("DB_NAME", "grocery.db")

ADMIN_USER = os.environ.get("ADMIN_USER", "subhrajitbehera152")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "9938950097_St")

SUPPORT_PHONE = os.environ.get("SUPPORT_PHONE", "917873688073")
SUPPORT_DISPLAY_PHONE = os.environ.get("SUPPORT_DISPLAY_PHONE", "+917848988073")

VALID_ORDER_STATUSES = (
    "Pending",
    "In Progress",
    "On the way",
    "Completed",
)

# Customer-facing delivery fee rule (cart, items, track, admin orders list)
FREE_DELIVERY_THRESHOLD = 199.0
DELIVERY_FEE = 30.0

# Admin order details temporary OOS delivery fee rule (preserved from order_details.html)
ADMIN_DETAIL_DELIVERY_THRESHOLD = 150.0
ADMIN_DETAIL_DELIVERY_FEE = 30.0

# Category & Sub-category hierarchy preserved from original application
CATEGORY_GROUPS = {
    "Fresh Vegetables": [
        ("Leafy Vegetables", "🥬"),
        ("Root Vegetables", "🥕"),
        ("Gourds", "🥒"),
        ("Beans & Peas", "🫘"),
        ("Chilli & Capsicum", "🌶️"),
        ("Mushrooms", "🍄"),
    ],
    "Meats, Fish & Eggs": [
        ("Mutton", "🍖"),
        ("Chicken", "🍗"),
        ("Fish & Seafood", "🐟"),
        ("Eggs", "🥚"),
    ],
    "Fresh Fruits": [
        ("Bananas", "🍌"),
        ("Citrus Fruits", "🍊"),
        ("Apples & Pears", "🍎"),
        ("Mangoes", "🥭"),
        ("Melons", "🍉"),
        ("Exotic Fruits", "🥝"),
    ],
    "Atta, Rice, Oil & Dals": [
        ("Rice", "🍚"),
        ("Atta & Flour", "🌾"),
        ("Cooking Oils", "🫗"),
        ("Dals & Pulses", "🫘"),
        ("Sugar & Salt", "🧂"),
        ("Spices", "🌶️"),
    ],
    "Dairy, Bread & Paneer": [
        ("Milk & Curd", "🥛"),
        ("Paneer & Cheese", "🧀"),
        ("Butter & Spreads", "🧈"),
        ("Bread & Bakery", "🍞"),
        ("Dairy Drinks", "🥤"),
        ("Eggs", "🥚"),
    ],
    "Home Food": [
        ("Breakfast", "🍳"),
        ("Lunch", "🍛"),
        ("Dinner", "🍽️"),
        ("Snacks", "🥪"),
        ("Sweets & Desserts", "🍰"),
        ("Ready to Eat", "🥡"),
    ],
}

MAIN_CATEGORY_ICONS = {
    "Fresh Vegetables": "🥬",
    "Meats, Fish & Eggs": "🥩",
    "Fresh Fruits": "🍎",
    "Atta, Rice, Oil & Dals": "🌾",
    "Dairy, Bread & Paneer": "🥛",
    "Home Food": "🍱",
}

INTRO_YOUTUBE_ID = "w7cNhKQuwAg"
TRACK_AD_YOUTUBE_ID = "tXVGFgnPxgk"
