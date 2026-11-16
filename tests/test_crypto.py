"""Unit tests for encryption/decryption cycles."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.crypto import CryptoEngine

class TestCryptoEngine(unittest.TestCase):

    def test_encrypt_decrypt_cycle(self):
        secret_message = b"Top secret audio binary payload sample 1234567890"
        passphrase = "UltraSecurePassword2026!"

        encrypted = CryptoEngine.encrypt(secret_message, passphrase)
        self.assertNotEqual(secret_message, encrypted)

        decrypted = CryptoEngine.decrypt(encrypted, passphrase)
        self.assertEqual(secret_message, decrypted)

    def test_wrong_password_fails(self):
        secret_message = b"Critical secret payload"
        encrypted = CryptoEngine.encrypt(secret_message, "PasswordA")

        with self.assertRaises(ValueError):
            CryptoEngine.decrypt(encrypted, "PasswordB")

    def test_tampered_ciphertext_fails(self):
        secret_message = b"Integrity check payload"
        encrypted = bytearray(CryptoEngine.encrypt(secret_message, "CorrectPassword"))
        # Flip a bit near the end
        encrypted[-1] ^= 0xFF

        with self.assertRaises(ValueError):
            CryptoEngine.decrypt(bytes(encrypted), "CorrectPassword")

if __name__ == "__main__":
    unittest.main()
