import unittest
import os
from Main import RecordFactory, PersonalRecord, GroupRecord, FinanceManager, GroupFundManager

class TestFinanceApp(unittest.TestCase):
    def setUp(self):
        """Arrange: Pasiruošimas prieš kiekvieną testą (Sukuriamas valdytojas ir išvalomi duomenys)."""
        self.limits = {"daily": 50.0, "weekly": 200.0, "monthly": 500.0}
        self.manager = FinanceManager("test_user", self.limits)
        self.manager.records = []  
        self.group_manager = GroupFundManager()
        self.group_manager.records = []

    def tearDown(self):
        """Išvalymas po testų."""
        for file in ["data_test_user.json", "test_user.txt", "group_fund.json"]:
            if os.path.exists(file):
                os.remove(file)

    # --- RecordFactory Testai (3) ---
    def test_factory_creates_personal_record(self):
        # Arrange
        amount, desc, cat = 10.0, "Pietūs", "Maistas"
        # Act
        record = RecordFactory.create("personal", amount, desc, cat)
        # Assert
        self.assertIsInstance(record, PersonalRecord)
        self.assertEqual(record.category, cat)

    def test_factory_creates_group_record(self):
        # Arrange
        amount, desc, user = 20.0, "Dovana", "Titas"
        # Act
        record = RecordFactory.create("group", amount, desc, user)
        # Assert
        self.assertIsInstance(record, GroupRecord)
        self.assertEqual(record.contributor, user)

    def test_factory_raises_error_on_unknown_type(self):
        # Arrange
        bad_type = "unknown_type"
        # Act & Assert
        with self.assertRaises(ValueError):
            RecordFactory.create(bad_type, 10, "Test", "Extra")

    # --- Polimorfizmo Testai (2) ---
    def test_personal_record_prepare_for_saving(self):
        # Arrange
        record = PersonalRecord(15.0, "Kinas", "Pramogos")
        # Act
        data = record.prepare_for_saving()
        # Assert
        self.assertEqual(data["type"], "personal")
        self.assertEqual(data["amount"], 15.0)

    def test_group_record_prepare_for_saving(self):
        # Arrange
        record = GroupRecord(50.0, "Nuoma", "Titas")
        # Act
        data = record.prepare_for_saving()
        # Assert
        self.assertEqual(data["type"], "group")
        self.assertEqual(data["contributor"], "Titas")

    # --- FinanceManager Logikos Testai (8) ---
    def test_manager_adds_record_successfully(self):
        # Arrange
        initial_count = len(self.manager.records)
        # Act
        self.manager.add_record("Maistas", -10.0, "Kava")
        # Assert
        self.assertEqual(len(self.manager.records), initial_count + 1)

    def test_manager_calculates_balance_correctly(self):
        # Arrange
        self.manager.add_record("Įnašas", 40.0, "Sausis")  # Naudojam 40, kad neviršytų 50 limito!
        self.manager.add_record("Maistas", -10.0, "Pietūs")
        # Act
        balance = self.manager.get_balance()
        # Assert
        self.assertEqual(balance, 30.0)

    def test_manager_removes_record_valid_index(self):
        # Arrange
        self.manager.add_record("Įnašas", 40.0, "Sausis") # Naudojam 40, kad neviršytų limito
        initial_count = len(self.manager.records)
        # Act
        self.manager.remove_record(0)
        # Assert
        self.assertEqual(len(self.manager.records), initial_count - 1)

    def test_manager_removes_record_invalid_index(self):
        # Arrange
        self.manager.add_record("Įnašas", 40.0, "Sausis") # Naudojam 40, kad neviršytų limito
        initial_count = len(self.manager.records)
        # Act
        self.manager.remove_record(99) # Blogas ID
        # Assert
        self.assertEqual(len(self.manager.records), initial_count)

    def test_daily_limit_allows_transaction(self):
        # Arrange
        amount = 40.0 # Limitas yra 50
        # Act
        allowed, msg = self.manager.check_limits(amount)
        # Assert
        self.assertTrue(allowed)

    def test_daily_limit_blocks_transaction(self):
        # Arrange
        self.manager.add_record("Įnašas", 40.0, "Test1")
        # Act
        allowed, msg = self.manager.check_limits(20.0) # 40 + 20 > 50
        # Assert
        self.assertFalse(allowed)
        self.assertIn("Daily limit", msg)

    def test_weekly_limit_blocks_transaction(self):
        # Arrange
        self.limits["daily"] = None # Išjungiame dienos limitą
        self.manager.add_record("Įnašas", 190.0, "Test")
        # Act
        allowed, msg = self.manager.check_limits(20.0) # 190 + 20 > 200
        # Assert
        self.assertFalse(allowed)
        self.assertIn("Weekly limit", msg)

    def test_limits_ignore_negative_amounts(self):
        # Arrange
        amount = -1000.0 # Išlaidos neturi trigerinti depozito limitų
        # Act
        allowed, msg = self.manager.check_limits(amount)
        # Assert
        self.assertTrue(allowed)

    # --- GroupFundManager Testai (3) ---
    def test_group_manager_adds_transaction(self):
        # Arrange
        initial_count = len(self.group_manager.records)
        # Act
        self.group_manager.add_transaction("Titas", 50.0, "Prisidėjimas")
        # Assert
        self.assertEqual(len(self.group_manager.records), initial_count + 1)

    def test_group_manager_calculates_total(self):
        # Arrange
        self.group_manager.add_transaction("Titas", 50.0, "Prisidėjimas")
        self.group_manager.add_transaction("Jonas", -20.0, "Išėmimas")
        # Act
        total = self.group_manager.get_total_fund()
        # Assert
        self.assertEqual(total, 30.0)

    def test_group_manager_view_history_empty_list(self):
        # Arrange
        self.group_manager.records = []
        # Act
        try:
            self.group_manager.view_history()
            crashed = False
        except Exception:
            crashed = True
        # Assert
        self.assertFalse(crashed) # Neturi nulūžti, kai istorija tuščia

if __name__ == '__main__':
    unittest.main()