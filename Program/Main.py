import json
import os
import sys
from datetime import datetime

class RecordFactory:
    @staticmethod
    def create(record_type, amount, desc, extra_info):
        if record_type == "personal":
            return PersonalRecord(amount, desc, category=extra_info)
        elif record_type == "group":
            return GroupRecord(amount, desc, contributor=extra_info)
        else:
            raise ValueError("Unknown record type")

class Record:
    def __init__(self, amount, desc):
        self.amount = amount
        self.desc = desc
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def prepare_for_saving(self):
        raise NotImplementedError("Subclasses must implement prepare_for_saving()")

class PersonalRecord(Record):
    def __init__(self, amount, desc, category):
        super().__init__(amount, desc)
        self.category = category

    def prepare_for_saving(self):
        return {"type": "personal", "amount": self.amount, "desc": self.desc, 
                "category": self.category, "timestamp": self.timestamp}

class GroupRecord(Record):
    def __init__(self, amount, desc, contributor):
        super().__init__(amount, desc)
        self.contributor = contributor

    def prepare_for_saving(self):
        return {"type": "group", "amount": self.amount, "desc": self.desc, 
                "contributor": self.contributor, "timestamp": self.timestamp}

class GroupFundManager:
    def __init__(self):
        self.filename = "group_fund.json"
        self.records = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename): return []
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
            json.dump([r.prepare_for_saving() for r in self.records], f, indent=4)

    def add_transaction(self, username, amount, desc):
        new_record = RecordFactory.create("group", amount, desc, username)
        self.records.append(new_record)
        self.save_data()
        print(f"Group fund updated by {username}.")

    def get_total(self):
        return sum(r.amount for r in self.records)

class FinanceManager:
    def __init__(self, username):
        self.username = username
        self.filename = f"data_{username}.json"
        self.records = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename): return []
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
            json.dump([r.prepare_for_saving() for r in self.records], f, indent=4)

    def add_record(self, amount, desc, category):
        new_record = RecordFactory.create("personal", amount, desc, category)
        self.records.append(new_record)
        self.save_data()

    def remove_record(self, index):
        if 0 <= index < len(self.records):
            self.records.pop(index)
            self.save_data()

    def get_balance(self):
        return sum(r.amount for r in self.records)

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", 'r') as f: return json.load(f)
    default = {"admin": {"password": "admin", "locked": False}}
    with open("users.json", 'w') as f: json.dump(default, f, indent=4)
    return default

def save_users(users):
    with open("users.json", 'w') as f: json.dump(users, f, indent=4)

def admin_menu(users):
    while True:
        print("\n=== ADMIN PANEL ===")
        print("1. View Users | 2. Lock User | 3. Delete User | 4. Logout")
        choice = input("Select: ")
        if choice == '1':
            for u, d in users.items(): print(f"- {u} (Locked: {d['locked']})")
        elif choice == '2':
            target = input("Username to lock/unlock: ").lower()
            if target in users and target != "admin":
                users[target]["locked"] = not users[target]["locked"]
                save_users(users)
        elif choice == '3':
            target = input("Username to delete: ").lower()
            if target in users and target != "admin":
                del users[target]
                save_users(users)
        elif choice == '4': break

def main_menu():
    users = load_users()
    while True:
        print("\n1. Login | 2. Register | 3. Exit")
        choice = input("Select: ")
        if choice == '3': sys.exit()
        elif choice == '2':
            u = input("Username: ").lower()
            p = input("Password: ")
            if u not in users:
                users[u] = {"password": p, "locked": False}
                save_users(users)
                print("Registered!")
            else: print("User exists.")
        elif choice == '1':
            u = input("Username: ").lower()
            p = input("Password: ")
            if u in users and users[u]["password"] == p:
                if users[u]["locked"]: print("Account locked.")
                elif u == "admin": admin_menu(users)
                else: user_loop(u)
            else: print("Invalid login.")

def user_loop(username):
    manager = FinanceManager(username)
    group = GroupFundManager()
    while True:
        print(f"\n--- {username.upper()} ---")
        print(f"Balance: {manager.get_balance():.2f} EUR")
        print("1. Add Record | 2. History | 3. Delete Record | 4. Group Fund | 5. Logout")
        
        action = input("Select: ")
        if action == '1':
            try:
                cat = input("Category: ")
                amt = float(input("Amount: ").replace(',', '.'))
                desc = input("Description: ")
                manager.add_record(amt, desc, cat)
            except ValueError: print("Invalid.")
        elif action == '2':
            for r in reversed(manager.records): print(f"{r.timestamp} | {r.amount} | {r.category}")
        elif action == '3':
            for i, r in enumerate(manager.records): print(f"{i+1}. {r.amount} EUR")
            try: manager.remove_record(int(input("ID: ")) - 1)
            except ValueError: print("Invalid.")
        elif action == '4':
            print(f"Group Total: {group.get_total():.2f} EUR")
            try:
                amt = float(input("Deposit to Group (minus to withdraw): ").replace(',', '.'))
                desc = input("Description: ")
                group.add_transaction(username, amt, desc)
                manager.add_record(-amt, desc, "Group Fund")
            except ValueError: print("Invalid.")
        elif action == '5': break

if __name__ == "__main__":
    main_menu()