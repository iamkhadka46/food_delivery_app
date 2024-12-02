import sqlite3

class Restaurant:
    def __init__(self, restaurant_id, name, location):
        self.id = restaurant_id
        self.name = name
        self.location = location

    def __str__(self):
        return f"Restaurant{{id={self.id}, name='{self.name}', location='{self.location}'}}"

class MenuItem:
    def __init__(self, item_id, restaurant_id, name, price):
        self.id = item_id
        self.restaurant_id = restaurant_id
        self.name = name
        self.price = price

    def __str__(self):
        return f"MenuItem{{id={self.id}, restaurant_id={self.restaurant_id}, name='{self.name}', price={self.price}}}"

class Order:
    def __init__(self, order_id, restaurant_id, customer_name, items, total_cost, status):
        self.order_id = order_id
        self.restaurant_id = restaurant_id
        self.customer_name = customer_name
        self.items = items
        self.total_cost = total_cost
        self.status = status

    def __str__(self):
        return f"Order{{order_id={self.order_id}, restaurant_id={self.restaurant_id}, customer_name='{self.customer_name}', total_cost={self.total_cost}, status='{self.status}'}}"

class FoodDeliveryManager:
    DB_URL = "food_delivery.db"

    def __init__(self):
        self.restaurants = {}
        self.menu_items = {}
        self.orders = []
        try:
            self.initialize_database()
            self.initialize_data()
        except sqlite3.Error as e:
            print(f"Initialization error: {e}")

    def initialize_database(self):
        try:
            with sqlite3.connect(self.DB_URL) as conn:
                cursor = conn.cursor()
                # Create `restaurants` table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS restaurants (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        location TEXT NOT NULL
                    )
                """)
                # Create `menu_items` table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS menu_items (
                        id INTEGER PRIMARY KEY,
                        restaurant_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
                    )
                """)
                # Create `orders` table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        restaurant_id INTEGER NOT NULL,
                        customer_name TEXT NOT NULL,
                        total_cost REAL NOT NULL,
                        status TEXT NOT NULL CHECK (status IN ('Pending', 'Delivered')),
                        FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
                    )
                """)
                
                # Populate `restaurants` table
                cursor.execute("SELECT COUNT(*) FROM restaurants")
                if cursor.fetchone()[0] == 0:
                    print("Populating restaurants table with sample data...")
                    cursor.executemany("""
                        INSERT INTO restaurants (id, name, location) VALUES (?, ?, ?)
                    """, [
                        (1, 'Pizza Palace', 'New York'),
                        (2, 'Sushi World', 'Los Angeles'),
                        (3, 'Burger Barn', 'Chicago')
                    ])
                
                # Populate `menu_items` table
                cursor.execute("SELECT COUNT(*) FROM menu_items")
                if cursor.fetchone()[0] == 0:
                    print("Populating menu_items table with sample data...")
                    cursor.executemany("""
                        INSERT INTO menu_items (id, restaurant_id, name, price) VALUES (?, ?, ?, ?)
                    """, [
                        (1, 1, 'Pepperoni Pizza', 12.99),
                        (2, 1, 'Cheese Pizza', 9.99),
                        (3, 1, 'Veggie Pizza', 10.99),
                        (4, 2, 'California Roll', 8.99),
                        (5, 2, 'Spicy Tuna Roll', 10.49),
                        (6, 2, 'Dragon Roll', 11.99),
                        (7, 3, 'Classic Burger', 7.99),
                        (8, 3, 'Cheeseburger', 8.99),
                        (9, 3, 'Veggie Burger', 8.49)
                    ])
                
                # Populate `orders` table
                cursor.execute("SELECT COUNT(*) FROM orders")
                if cursor.fetchone()[0] == 0:
                    print("Populating orders table with sample data...")
                    cursor.executemany("""
                        INSERT INTO orders (restaurant_id, customer_name, total_cost, status) VALUES (?, ?, ?, ?)
                    """, [
                        (1, 'John Doe', 22.98, 'Pending'),  # Ordering items from Pizza Palace
                        (2, 'Jane Smith', 19.48, 'Delivered'),  # Ordering items from Sushi World
                        (3, 'Alice Brown', 16.98, 'Pending')  # Ordering items from Burger Barn
                    ])
        except sqlite3.Error as e:
            print(f"Database error during initialization: {e}")
            raise


    def initialize_data(self):
        try:
            with sqlite3.connect(self.DB_URL) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM restaurants")
                for row in cursor.fetchall():
                    restaurant_id, name, location = row
                    self.restaurants[restaurant_id] = Restaurant(restaurant_id, name, location)
                cursor.execute("SELECT * FROM menu_items")
                for row in cursor.fetchall():
                    item_id, restaurant_id, name, price = row
                    self.menu_items[item_id] = MenuItem(item_id, restaurant_id, name, price)
        except sqlite3.Error as e:
            print(f"Error loading data: {e}")
            raise

    def place_order(self, restaurant_id, customer_name, item_ids):
        total_cost = 0
        items = []
        for item_id in item_ids:
            item = self.menu_items.get(item_id)
            if item and item.restaurant_id == restaurant_id:
                items.append(item)
                total_cost += item.price
            else:
                print(f"Item with ID {item_id} not found or doesn't belong to the selected restaurant.")
                return

        try:
            with sqlite3.connect(self.DB_URL) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO orders (restaurant_id, customer_name, total_cost, status)
                    VALUES (?, ?, ?, ?)
                """, (restaurant_id, customer_name, total_cost, 'Pending'))
                cursor.execute("SELECT last_insert_rowid()")
                order_id = cursor.fetchone()[0]
                self.orders.append(Order(order_id, restaurant_id, customer_name, items, total_cost, 'Pending'))
                print(f"Order placed successfully! Total cost: ${total_cost:.2f}")
        except sqlite3.Error as e:
            print(f"Error placing order: {e}")

    def deliver_order(self, order_id):
        order = next((o for o in self.orders if o.order_id == order_id), None)
        if order and order.status == 'Pending':
            try:
                with sqlite3.connect(self.DB_URL) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE orders SET status = ? WHERE order_id = ?
                    """, ('Delivered', order_id))
                    order.status = 'Delivered'
                    print(f"Order {order_id} delivered successfully!")
            except sqlite3.Error as e:
                print(f"Error delivering order: {e}")
        else:
            print("Order not found or already delivered.")

    def view_available_menu(self, restaurant_id):
        restaurant = self.restaurants.get(restaurant_id)
        if restaurant:
            print(f"Menu for {restaurant.name} in {restaurant.location}:")
            for item in self.menu_items.values():
                if item.restaurant_id == restaurant_id:
                    print(item)
        else:
            print("Restaurant not found.")

    def view_orders(self):
        for order in self.orders:
            print(order)
 

if __name__ == "__main__":
    food_delivery = FoodDeliveryManager()
    # View available menu for a restaurant
    food_delivery.view_available_menu(1)
    # Place an order
    food_delivery.place_order(1, "John Doe", [1, 2])  # Ordering item with ID 1 and 2 from restaurant 1
    # View all orders
    food_delivery.view_orders()
    # Deliver the order
    food_delivery.deliver_order(4)

