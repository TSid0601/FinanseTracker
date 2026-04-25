import json
import os
import sys
from datetime import datetime

class RecordFactory:
    """Creates specific record objects based on the requested type."""
    @staticmethod
    def create(record_type, amount, desc, extra_info):
        if record_type == "personal":
            return PersonalRecord(amount, desc, category=extra_info)
        elif record_type == "group":
            return GroupRecord(amount, desc, contributor=extra_info)
        else:
            raise ValueError("Unknown record type")

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
        return {
            "type": "personal",
            "amount": self.amount,
            "desc": self.desc,
            "category": self.category,
            "timestamp": self.timestamp
        }

class GroupRecord(Record):
    """Represents a shared group fund transaction."""
    def __init__(self, amount, desc, contributor):
        super().__init__(amount, desc)
        self.contributor = contributor

    def prepare_for_saving(self):
        return {
            "type": "group",
            "amount": self.amount,
            "desc": self.desc,
            "contributor": self.contributor,
            "timestamp": self.timestamp
        }

class GroupFundManager:
    """Manages the shared fund containing GroupRecord objects."""
    def __init__(self):
        self.filename = "group_fund.json"
        self.records = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        loaded = []
        for item in data:
            record = GroupRecord(item["amount"], item["desc"], item["contributor"])
            record.timestamp = item["timestamp"]
            loaded.append(record)
        return loaded

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump([r.prepare_for_saving() for r in self.records], f, indent=4, ensure_ascii=False)

    def add_transaction(self, username, amount, desc):
        new_record = RecordFactory.create("group", amount, desc, username)
        self.records.append(new_record)
        self.save_data()
        
        t_type = "deposited" if amount > 0 else "withdrew"
        print(f"Group fund updated: {username} {t_type} {abs(amount)} EUR.")

    def get_total_fund(self):
        return sum(r.amount for r in self.records)
        
    def view_history(self):
        print("\n--- GROUP FUND HISTORY ---")
        if not self.records:
            print("No group transactions yet.")
            return
        for r in reversed(self.records):
            t_type = "DEPOSIT" if r.amount > 0 else "WITHDRAWAL"
            print(f"[{t_type}] {r.timestamp} | {abs(r.amount):.2f} EUR | User: {r.contributor} | Desc: {r.desc}")

class FinanceManager:
    """Manages a user's personal finance records."""
    def __init__(self, username, limits):
        self.username = username
        self.limits = limits
        self.filename = f"data_{username}.json"
        self.records = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        loaded = []
        for item in data:
            record = PersonalRecord(item["amount"], item["desc"], item["category"])
            record.timestamp = item["timestamp"]
            loaded.append(record)
        return loaded

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump([r.prepare_for_saving() for r in self.records], f, indent=4, ensure_ascii=False)

    def check_limits(self, amount):
        if amount <= 0:
            return True, ""

        now = datetime.now()
        daily = 0
        weekly = 0
        monthly = 0
        
        for r in self.records:
            if r.amount > 0:
                rec_date = datetime.strptime(r.timestamp, "%Y-%m-%d %H:%M:%S")
                if rec_date.date() == now.date(): 
                    daily += r.amount
                if rec_date.isocalendar()[1] == now.isocalendar()[1] and rec_date.year == now.year: 
                    weekly += r.amount
                if rec_date.month == now.month and rec_date.year == now.year: 
                    monthly += r.amount

        if self.limits.get("daily") and (daily + amount) > self.limits["daily"]:
            return False, f"Daily limit ({self.limits['daily']} EUR) exceeded."
        if self.limits.get("weekly") and (weekly + amount) > self.limits["weekly"]:
            return False, f"Weekly limit ({self.limits['weekly']} EUR) exceeded."
        if self.limits.get("monthly") and (monthly + amount) > self.limits["monthly"]:
            return False, f"Monthly limit ({self.limits['monthly']} EUR) exceeded."

        return True, ""

    def add_record(self, category, amount, desc):
        allowed, msg = self.check_limits(amount)
        if not allowed:
            print(f"Error: {msg}")
            return
            
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
                f.write(f"[{record.timestamp}] {t_type}: {record.amount:>8.2f} EUR | {record.category}: {record.desc}\n")
        print(f"Report saved to: {report_filename}")

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    default = {
        "admin": {
            "password": "admin", 
            "locked": False, 
            "limits": {"daily": None, "weekly": None, "monthly": None}
        }
    }
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
            if target in users and target != "admin":
                users[target]["locked"] = not users[target]["locked"]
                save_users(users)
                print("Status updated.")
            else:
                print("Error: User not found or cannot edit admin.")
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
            if target in users and target != "admin":
                del users[target]
                save_users(users)
                
                if os.path.exists(f"data_{target}.json"):
                    os.remove(f"data_{target}.json")
                if os.path.exists(f"{target}.txt"):
                    os.remove(f"{target}.txt")
                print("User deleted.")
            else:
                print("Error: User not found or cannot delete admin.")
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

def set_limits_menu(username, users_db):
    print("\n--- DEPOSIT LIMITS ---")
    print("- Type a number to set a limit.")
    print("- Type '0' to REMOVE a limit.")
    print("- Leave blank and press Enter to KEEP the current limit.")
    
    c_daily = users_db[username]["limits"]["daily"]
    c_weekly = users_db[username]["limits"]["weekly"]
    c_monthly = users_db[username]["limits"]["monthly"]

    daily = input(f"Set Daily Limit (Current: {c_daily}): ")
    weekly = input(f"Set Weekly Limit (Current: {c_weekly}): ")
    monthly = input(f"Set Monthly Limit (Current: {c_monthly}): ")

    try:
        if daily != "": 
            val = float(daily.replace(',', '.'))
            users_db[username]["limits"]["daily"] = val if val > 0 else None
        if weekly != "": 
            val = float(weekly.replace(',', '.'))
            users_db[username]["limits"]["weekly"] = val if val > 0 else None
        if monthly != "": 
            val = float(monthly.replace(',', '.'))
            users_db[username]["limits"]["monthly"] = val if val > 0 else None
        
        save_users(users_db)
        print("Limits updated successfully.")
    except ValueError:
        print("Error: Invalid number format.")

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
                users[u] = {
                    "password": p, 
                    "locked": False, 
                    "limits": {"daily": None, "weekly": None, "monthly": None}
                }
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
            
        manager = FinanceManager(active_user, users_db[active_user]["limits"])
        group_fund = GroupFundManager()
        
        while True:
            print(f"\n--- {active_user.upper()}'S FINANCES ---")
            print(f"Current Balance: {manager.get_balance():.2f} EUR")
            print("1. Add Income/Expense")
            print("2. View History")
            print("3. Remove an Expense/Income")
            print("4. Set Deposit Limits")
            print("5. Group Fund Actions")
            print("6. Logout and Generate Report")
            
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
                set_limits_menu(active_user, users_db)
                manager.limits = users_db[active_user]["limits"]
                
            elif action == '5':
                print(f"\n--- GROUP FUND (Total: {group_fund.get_total_fund():.2f} EUR) ---")
                print("1. Make a deposit to Group Fund")
                print("2. Withdraw from Group Fund")
                print("3. View Group Fund History")
                
                g_action = input("Select: ")
                if g_action == '1':
                    try:
                        amt = float(input("Amount to deposit: ").replace(',', '.'))
                        if amt > 0:
                            desc = input("Description: ")
                            group_fund.add_transaction(active_user, amt, desc)
                            manager.add_record("Group Fund", -amt, desc)
                        else:
                            print("Error: Amount must be positive.")
                    except ValueError:
                        print("Error: Please enter a valid number.")
                        
                elif g_action == '2':
                    try:
                        amt = float(input("Amount to withdraw: ").replace(',', '.'))
                        if amt > 0:
                            if amt <= group_fund.get_total_fund():
                                desc = input("Description: ")
                                group_fund.add_transaction(active_user, -amt, desc)
                                manager.add_record("Group Fund Withdrawal", amt, desc)
                            else:
                                print("Error: Not enough money in the Group Fund.")
                        else:
                            print("Error: Amount must be positive.")
                    except ValueError:
                        print("Error: Please enter a valid number.")
                        
                elif g_action == '3':
                    group_fund.view_history()
                else:
                    print("Invalid choice.")
                    
            elif action == '6':
                manager.generate_txt_report()
                print(f"Logging out {active_user}...")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    main_menu()