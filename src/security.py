import base64
import getpass  # Used to securely hide password input in the terminal
import hashlib
import os
from pathlib import Path

import msoffcrypto


def encrypt_password_with_hashlib(plain_password: str, secret_key: str) -> str:
    """Encrypts the password using hashlib (SHA-256) combined with an XOR cipher."""
    # Generate a SHA-256 hash of the secret key to create a secure 32-byte key stream
    key_stream = hashlib.sha256(secret_key.encode("utf-8")).digest()

    # XOR each character of the plain password with the corresponding byte in the key stream
    encrypted_bytes = bytearray()
    for i, char in enumerate(plain_password.encode("utf-8")):
        encrypted_bytes.append(char ^ key_stream[i % len(key_stream)])

    # Encode the encrypted bytes in base64 to store or transmit as a readable string
    return base64.b64encode(encrypted_bytes).decode("utf-8")


def decrypt_password_with_hashlib(encrypted_password: str, secret_key: str) -> str:
    """Decrypts the password back to plain text using the identical secret key and Hashlib stream."""
    # Decode the base64 string back into encrypted bytes
    encrypted_bytes = base64.b64decode(encrypted_password)

    # Recreate the identical 32-byte key stream using the secret key
    key_stream = hashlib.sha256(secret_key.encode("utf-8")).digest()

    # XOR the encrypted bytes with the key stream to retrieve the original password
    decrypted_bytes = bytearray()
    for i, byte in enumerate(encrypted_bytes):
        decrypted_bytes.append(byte ^ key_stream[i % len(key_stream)])

    return decrypted_bytes.decode("utf-8")


def encrypt_excel_with_password(source_path: Path, password: str) -> Path:
    """Encrypt an Excel workbook with a native Office open password.

    The resulting workbook uses the Office encryption container supported by
    Microsoft Excel and compatible mobile viewers, rather than a ZIP archive.

    Args:
        source_path (Path): The unencrypted ``.xlsx`` file to protect.
        password (str): The password required to open the workbook.

    Returns:
        Path: The path to the newly created encrypted ``.xlsx`` file.
    """
    encrypted_path = source_path.with_name(f"{source_path.stem}_protected.xlsx")

    with source_path.open("rb") as source, encrypted_path.open("wb") as destination:
        office_file = msoffcrypto.OfficeFile(source)
        office_file.encrypt(password, destination)

    return encrypted_path


# --- Script Execution / Testing ---
if __name__ == "__main__":
    # Fetch the secret key from the environment; if missing, prompt the user securely
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        print("Warning: SECRET_KEY not found in environment.")
        SECRET_KEY = getpass.getpass("Enter your Secret Key: ")

    # Securely prompt for the password instead of hardcoding it in the script
    ORIGINAL_PASSWORD = getpass.getpass("Enter the password you want to encrypt: ")

    # Encrypt the provided password
    encrypted = encrypt_password_with_hashlib(ORIGINAL_PASSWORD, SECRET_KEY)
    print(f"\nEncrypted Password for config.json: {encrypted}")

    # Decrypt the password to verify the logic
    decrypted = decrypt_password_with_hashlib(encrypted, SECRET_KEY)
    print(f"Decrypted Password (Verification): {decrypted}")
