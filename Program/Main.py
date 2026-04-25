import json
import os
import sys
from datetime import datetime

#RECORD FACTORY
class RecordFactory:
    """Creates specific record objects based on the requested type."""
    @staticmethod
    def create(record_type, amount, desc, extra_info):
        if record_type == "personal":
            return PersonalRecord(amount, desc, category=extra_info)
        else:
            raise ValueError("Unknown record type")

#RECORD CLASSES
class Record:
    """Parent base class for all transactions."""
    def __init__(self, amount, desc):
        self.amount = amount
        self.desc = desc
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def prepare_for_saving(self):
        """Must be overridden by child classes to provide a saveable dictionary."""
        raise NotImplementedError("Subclasses must implement prepare_for_saving()")

class PersonalRecord(Record):
    """Represents a single personal finance transaction."""
    def __init__(self, amount, desc, category):
        super().__init__(amount, desc)
        self.category = category

    def prepare_for_saving(self):
        """Returns the personal record data formatted as a dictionary."""
        return {
            "type": "personal",
            "amount": self.amount,
            "desc": self.desc,
            "category": self.category,
            "timestamp": self.timestamp
        }

#DATA MANAGERS
class FinanceManager:
    """Manages a user's personal finance records."""
    def __init__(self, username):
        self.username = username
        self.filename = f"data_{username}.json"
        self.records = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        loaded_records = []
        for item in data:
            if item["type"] == "personal":
                record = PersonalRecord(item["amount"], item["desc"], item["category"])
                record.timestamp = item["timestamp"]
                loaded_records.append(record)
        return loaded_records

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            data_to_save = [r.prepare_for_saving() for r in self.records]
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)

    def add_record(self, category, amount, desc):
        new_record = RecordFactory.create("personal", amount, desc, category)
        self.records.append(new_record)
        self.save_data()
        print(f"Added: {amount} EUR")

    def remove_record(self, index):
        if 0 <= index < len(self.records):
            removed = self.records.pop(index)
            self.save_data()
            print(f"Removed record: {removed.amount} EUR")
        else:
            print("Error: Invalid record ID.")

    def get_balance(self):
        return sum(r.amount for r in self.records)
        
    def generate_txt_report(self):
        balance = self.get_balance()
        report_filename = f"{self.username}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"USER {self.username.upper()} FINANCE REPORT\n")
            f.write("-" * 40 + "\n")
            f.write(f"CURRENT BALANCE: {balance:.2f} EUR\n")
            f.write("-" * 40 + "\n\n")
            
            for record in reversed(self.records):
                t_type = "INCOME" if record.amount > 0 else "EXPENSE"
                f.write(f"[{record.timestamp}] {t_type}: {record.amount:>8.2f} EUR | "
                        f"{record.category}: {record.desc}\n")
                        
        print(f"Report saved to: {report_filename}")

#AUTHENTICATION & MENUS
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    default = {"admin": {"password": "admin", "locked": False}}
    with open("users.json", 'w', encoding='utf-8') as f:
        json.dump(default, f, indent=4)
    return default

def save_users(users):
    with open("users.json", 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def admin_menu(users):
    while True:
        print("\n=== ADMIN PANEL ===")
        print("1. View All Users")
        print("2. Lock/Unlock User")
        print("3. Change User Password")
        print("4. Delete User")
        print("5. Logout")
        
        choice = input("Select an option: ")
        
        if choice == '1':
            print("\n--- REGISTERED USERS ---")
            for u, d in users.items():
                status = "LOCKED" if d['locked'] else "ACTIVE"
                print(f"- {u} ({status})")
                
        elif choice == '2':
            target = input("Enter username to lock/unlock: ").strip().lower()
            if target == "admin":
                print("Error: Cannot lock admin.")
            elif target in users:
                users[target]["locked"] = not users[target]["locked"]
                save_users(users)
                print("Status updated.")
            else:
                print("Error: User not found.")
                
        elif choice == '3':
            target = input("Enter username to change password: ").strip().lower()
            if target in users:
                users[target]["password"] = input("New password: ")
                save_users(users)
                print("Password updated.")
            else:
                print("Error: User not found.")
                
        elif choice == '4':
            target = input("Enter username to delete: ").strip().lower()
            if target == "admin":
                print("Error: Cannot delete admin.")
            elif target in users:
                del users[target]
                save_users(users)
                if os.path.exists(f"data_{target}.json"):
                    os.remove(f"data_{target}.json")
                if os.path.exists(f"{target}.txt"):
                    os.remove(f"{target}.txt")
                print("User deleted.")
            else:
                print("Error: User not found.")
                
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

def authenticate_user():
    users = load_users()
    while True:
        print("\n=== LOGIN ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit Program")
        choice = input("Select an option: ")

        if choice == '3':
            return None, None
            
        elif choice == '2':
            u = input("Username: ").strip().lower()
            p = input("Password: ")
            if u not in users and u != "admin":
                users[u] = {"password": p, "locked": False}
                save_users(users)
                print("Registration successful! You can now log in.")
            else:
                print("Error: User already exists or name is reserved.")
                
        elif choice == '1':
            u = input("Username: ").strip().lower()
            p = input("Password: ")
            if u in users and users[u]["password"] == p:
                if users[u]["locked"]:
                    print("Error: Your account is locked by admin.")
                else:
                    print(f"Welcome back, {u}!")
                    return u, users
            else:
                print("Error: Invalid username or password.")
        else:
            print("Invalid choice. Try again.")

def main_menu():
    while True:
        active_user, users_db = authenticate_user()
        
        if active_user is None:
            print("Exiting program. Goodbye!")
            sys.exit()
            
        if active_user == "admin":
            admin_menu(users_db)
            continue
            
        manager = FinanceManager(active_user)
        
        while True:
            print(f"\n--- {active_user.upper()}'S FINANCES ---")
            print(f"Current Balance: {manager.get_balance():.2f} EUR")
            print("1. Add Income/Expense")
            print("2. View History")
            print("3. Remove an Expense/Income")
            print("4. Logout and Generate Report")
            
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
                    for r in reversed(manager.records):
                        t_type = "INCOME" if r.amount > 0 else "EXPENSE"
                        print(f"[{t_type}] {r.timestamp} | {r.amount} EUR | {r.category} - {r.desc}")
                        
            elif action == '3':
                print("\n--- REMOVE RECORD ---")
                if not manager.records:
                    print("No records to remove.")
                else:
                    for i, r in enumerate(manager.records):
                        t_type = "INCOME" if r.amount > 0 else "EXPENSE"
                        print(f"ID: {i+1} | [{t_type}] {r.timestamp} | {r.amount} EUR")
                    try:
                        record_id = int(input("Enter record ID to remove: "))
                        manager.remove_record(record_id - 1)
                    except ValueError:
                        print("Error: Please enter a valid ID number.")
                        
            elif action == '4':
                manager.generate_txt_report()
                print(f"Logging out {active_user}...")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    main_menu()