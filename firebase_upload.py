import firebase_admin
from firebase_admin import credentials, storage
import os
import requests
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

class FirebaseUploader:
    def __init__(self, cred_path, bucket_name, password):
        # Check if the default app has already been initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': bucket_name
            })
        self.bucket = storage.bucket(bucket_name)
        self.password = password  # Use a secure password for encryption
        self.upload_queue = []  # Store failed uploads here

    def generate_key(self, salt):
        """Derive a key from the password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.password.encode())

    def encrypt_file(self, file_path):
        """Encrypt the file using AES encryption."""
        # Generate a salt and initialization vector (IV)
        salt = os.urandom(16)
        iv = os.urandom(16)
        key = self.generate_key(salt)

        # Create cipher and padder
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        encrypted_file_path = f"{file_path}.enc"
        
        # Read and encrypt the file
        with open(file_path, 'rb') as f, open(encrypted_file_path, 'wb') as enc_file:
            enc_file.write(salt)  # Save the salt at the beginning
            enc_file.write(iv)    # Save the IV after the salt
            while chunk := f.read(1024):
                padded_data = padder.update(chunk)
                enc_file.write(encryptor.update(padded_data))
            enc_file.write(encryptor.update(padder.finalize()))
            enc_file.write(encryptor.finalize())

        return encrypted_file_path

    def check_internet_connection(self):
        """Check if the internet connection is active."""
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def upload_file(self, file_path):
        """Upload file to Firebase Storage."""
        try:
            encrypted_file_path = self.encrypt_file(file_path)
            blob = self.bucket.blob(os.path.basename(encrypted_file_path))
            # Check if the internet is connected
            if self.check_internet_connection():
                blob.upload_from_filename(encrypted_file_path)
                print(f"Successfully uploaded {encrypted_file_path} to Firebase Storage.")
                if os.path.exists(encrypted_file_path):
                    os.remove(encrypted_file_path)
                    print(f"File {encrypted_file_path} deleted from local system.")
                else:
                    print(f"File {encrypted_file_path} not found locally. Perhaps it was already deleted.")
            else:
                print(f"No internet connection. Queuing {encrypted_file_path} for retry.")
                self.upload_queue.append(encrypted_file_path)
        except Exception as e:
            print(f"Error uploading {encrypted_file_path}: {e}")
            if "firewall" in str(e).lower():
                print("Possible firewall issue detected. Please check your network settings.")
            self.upload_queue.append(encrypted_file_path)

    def retry_queued_uploads(self):
        """Retry uploading files from the queue."""
        for file_path in list(self.upload_queue):  # Create a copy of the list
            print(f"Retrying upload for {file_path}...")
            self.upload_file(file_path)
            if file_path not in self.upload_queue:
                self.upload_queue.remove(file_path)

    def save_queue(self, file_path='upload_queue.txt'):
        """Save the queue to a file before application shutdown."""
        with open(file_path, 'w') as f:
            for item in self.upload_queue:
                f.write(f"{item}\n")
        print(f"Upload queue saved to {file_path}.")

    def load_queue(self, file_path='upload_queue.txt'):
        """Load the upload queue from a file at startup."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.upload_queue = f.read().splitlines()
            print(f"Loaded {len(self.upload_queue)} items from upload queue.")

    def shutdown_handler(self):
        """Handle safe shutdown for pending uploads."""
        if self.upload_queue:
            print("Application is shutting down. Saving pending uploads...")
            self.save_queue()

