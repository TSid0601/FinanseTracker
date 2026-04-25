import json
import os
import sys
from datetime import datetime


class FinanceManager:
    """Manage personal finance records and calculate balance."""

    def __init__(self, username):
        """Initialize finance manager for a user."""
        self.username = username
        self.filename = f"data_{username}.json"
        self.records = self.load_data()

    def load_data(self):
        """Load records from the JSON file."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_data(self):
        """Save records to the JSON file."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, indent=4, ensure_ascii=False)

    def add_record(self, category, amount, description):
        """Add a new income or expense record."""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        record = {}
        record["timestamp"] = timestamp
        record["category"] = category
        record["amount"] = amount
        record["description"] = description
        
        self.records.append(record)
        self.save_data()
        print(f"Added: {amount} EUR ({timestamp})")

    def get_balance(self):
        """Calculate total balance."""
        total = 0.0
        for record in self.records:
            total = total + record["amount"]
        return total

    def generate_txt_report(self):
        """Generate a text file report."""
        balance = self.get_balance()
        report_filename = f"{self.username}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"USER {self.username.upper()} FINANCE REPORT\n")
            f.write("-" * 40 + "\n")
            f.write(f"CURRENT BALANCE: {balance:.2f} EUR\n")
            f.write("-" * 40 + "\n\n")
            f.write("TRANSACTION HISTORY (Newest to Oldest):\n")
            
            for record in reversed(self.records):
                if record["amount"] > 0:
                    t_type = "INCOME"
                else:
                    t_type = "EXPENSE"
                f.write(f"[{record['timestamp']}] {t_type}: "
                        f"{record['amount']:>8.2f} EUR | "
                        f"{record['category']}: {record['description']}\n")
                        
        print(f"Report saved to: {report_filename}")


def authenticate_user():
    """Handle basic user registration and login."""
    users_file = "users.json"
    
    if os.path.exists(users_file):
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
    else:
        users = {}

    while True:
        print("\n=== LOGIN ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit Program")
        choice = input("Select an option: ")

        if choice == '3':
            return None

        if choice == '2':
            username = input("Username: ").strip().lower()
            password = input("Password: ")
            
            if username in users:
                print("Error: User already exists!")
            else:
                users[username] = password
                with open(users_file, 'w', encoding='utf-8') as f:
                    json.dump(users, f, indent=4)
                print("Registration successful! You can now log in.")
                
        elif choice == '1':
            username = input("Username: ").strip().lower()
            password = input("Password: ")
            
            if username in users and users[username] == password:
                print(f"Welcome back, {username}!")
                return username
            else:
                print("Error: Invalid username or password.")
        else:
            print("Invalid choice.")


def main_menu():
    """Run the continuous main program loop."""
    while True:
        active_user = authenticate_user()
        
        if active_user is None:
            print("Exiting program. Goodbye!")
            sys.exit()

        manager = FinanceManager(active_user)
        
        while True:
            print(f"\n--- {active_user.upper()}'S FINANCES ---")
            print(f"Current Balance: {manager.get_balance():.2f} EUR")
            print("1. Add Income/Expense")
            print("2. View History")
            print("3. Logout and Generate Report")
            print("4. Exit Program")
            
            action = input("Select an action: ")

            if action == '1':
                try:
                    category = input("Category: ")
                    amount_input = input("Amount (use minus for expenses): ")
                    amount = float(amount_input.replace(',', '.'))
                    description = input("Description: ")
                    manager.add_record(category, amount, description)
                except ValueError:
                    print("Error: Please enter a valid number.")
            
            elif action == '2':
                print("\n--- HISTORY ---")
                if not manager.records:
                    print("No records found.")
                else:
                    for record in reversed(manager.records):
                        if record["amount"] > 0:
                            t_type = "INCOME"
                        else:
                            t_type = "EXPENSE"
                        print(f"[{t_type}] {record['timestamp']} | "
                              f"{record['amount']} EUR | "
                              f"{record['category']} - "
                              f"{record['description']}")
            
            elif action == '3':
                manager.generate_txt_report()
                print(f"Logging out {active_user}...")
                break  # Breaks inner loop, returns to login
                
            elif action == '4':
                manager.generate_txt_report()
                print("Exiting program. Goodbye!")
                sys.exit()
                
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    main_menu()