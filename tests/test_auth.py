import unittest
from utils.security import hash_password, verify_password


class TestSecurity(unittest.TestCase):
    def test_hash_password_returns_string(self):
        result = hash_password("admin123")
        self.assertIsInstance(result, str)

    def test_verify_password_correct(self):
        hashed = hash_password("secret")
        self.assertTrue(verify_password("secret", hashed))

    def test_verify_password_incorrect(self):
        hashed = hash_password("secret")
        self.assertFalse(verify_password("wrong", hashed))


if __name__ == "__main__":
    unittest.main()