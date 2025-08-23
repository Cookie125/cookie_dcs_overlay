import http.server
import socketserver
from http import HTTPStatus
from base64 import b64decode
import os
import logging
from urllib.parse import urlparse, unquote
import sys  # Added for exit handling
import time  # Added for retry delay

# Configuration
PORT = 5314  # Updated to port 5314
CSV_FILE = "server-fueldata.csv"  # Name of the CSV file to serve
LOCK_FILE = CSV_FILE + ".lock"  # Lock file path
USERNAME = "admin"  # Change to your desired username
PASSWORD = "K7$mP9!xL2qJ4"  # Change to a strong password
LOG_FILE = "server.log"  # Log file for debugging
ALLOWED_IPS = {'192.168.50.1'}  # Add client PC public IP here
MAX_ATTEMPTS = 5
MAX_RETRIES = 5  # Maximum retry attempts for lock
RETRY_DELAY = 1  # Seconds to wait between retries

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
failed_attempts = {}

class CustomRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request from {self.client_address[0]} for: {self.path}")  # Add to CMD
        logging.info(f"Received request from {self.client_address[0]} for: {self.path}")
        
        # Check IP restriction
        if self.client_address[0] not in ALLOWED_IPS:
            self.send_error(403, "Forbidden")
            print(f"Access denied from unauthorized IP: {self.client_address[0]}")  # Add to CMD
            logging.warning(f"Access denied from unauthorized IP: {self.client_address[0]}")
            return

        # Check authentication
        auth_header = self.headers.get('Authorization')
        if not auth_header or not self.check_auth(auth_header):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Secure DCS Data"')
            self.end_headers()
            print(f"Authentication failed for IP: {self.client_address[0]}")  # Add to CMD
            logging.warning(f"Authentication failed for IP: {self.client_address[0]}")
            return

        # Sanitize and validate the path
        path = unquote(urlparse(self.path).path)
        sanitized_path = os.path.normpath(os.path.join(os.getcwd(), path.lstrip('/')))
        expected_path = os.path.normpath(os.path.join(os.getcwd(), CSV_FILE))

        print(f"Original path: {path}, Sanitized path: {sanitized_path}")  # Add to CMD
        logging.info(f"Original path: {path}, Sanitized path: {sanitized_path}")

        if sanitized_path != expected_path:
            self.send_error(404, "File not found or access denied")
            print(f"Invalid path attempt: {path}")  # Add to CMD
            logging.warning(f"Invalid path attempt: {path}, Sanitized: {sanitized_path}")
            return

        # Check for lock file and wait if present
        retry_count = 0
        while os.path.exists(LOCK_FILE) and retry_count < MAX_RETRIES:
            print(f"Lock file detected, waiting... Retry {retry_count + 1}/{MAX_RETRIES}")  # Add to CMD
            logging.info(f"Lock file detected, waiting... Retry {retry_count + 1}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY)
            retry_count += 1

        if os.path.exists(LOCK_FILE):
            self.send_error(503, "Service Unavailable - File locked by writer")
            print(f"Failed to access {CSV_FILE} after {MAX_RETRIES} retries")  # Add to CMD
            logging.error(f"Failed to access {CSV_FILE} after {MAX_RETRIES} retries")
            return

        # Serve the CSV file
        if os.path.exists(CSV_FILE):
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS for any origin
            self.end_headers()
            with open(CSV_FILE, 'rb') as f:
                self.wfile.write(f.read())
            print(f"Served {CSV_FILE} to {self.client_address[0]}")  # Add to CMD
            logging.info(f"Served {CSV_FILE} to {self.client_address[0]}")
        else:
            self.send_error(404, "CSV file not found")
            print(f"CSV file not found: {CSV_FILE}")  # Add to CMD
            logging.error(f"{CSV_FILE} not found")

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        print(f"Received OPTIONS request from {self.client_address[0]} for: {self.path}")  # Add to CMD
        logging.info(f"Received OPTIONS request from {self.client_address[0]} for: {self.path}")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')  # Cache preflight for 24 hours
        self.end_headers()
        logging.info(f"Responded to OPTIONS request from {self.client_address[0]}")

    def check_auth(self, auth_header):
        if auth_header.startswith('Basic '):
            ip = self.client_address[0]
            if ip in failed_attempts and failed_attempts[ip] >= MAX_ATTEMPTS:
                print(f"Max attempts exceeded for IP: {ip}")  # Add to CMD
                logging.error(f"Max attempts exceeded for IP: {ip}")
                return False
            try:
                credentials = b64decode(auth_header[6:]).decode('utf-8')
                username, password = credentials.split(':')
                if username == USERNAME and password == PASSWORD:
                    failed_attempts[ip] = 0
                    return True
                else:
                    failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
                    print(f"Invalid credentials for IP: {ip}, attempts: {failed_attempts[ip]}")  # Add to CMD
                    logging.warning(f"Invalid credentials for IP: {ip}, attempts: {failed_attempts[ip]}")
                    return False
            except Exception as e:
                print(f"Authentication error for IP {ip}: {e}")  # Add to CMD
                logging.error(f"Authentication error for IP {ip}: {e}")
                failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
                return False
        return False

def run_server(port=PORT):
    server_address = ('', port)
    httpd = socketserver.TCPServer(server_address, CustomRequestHandler)
    logging.info(f"Starting secure server on port {port}...")
    print(f"Starting secure server on port {port}...")  # Add to CMD
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        print("Server stopped by user")  # Add to CMD
        httpd.server_close()
    except Exception as e:
        logging.error(f"Server error: {e}")
        print(f"Error: {e}. Check {LOG_FILE} for details. Press Enter to exit.")  # Add to CMD
        input()  # Keeps console open on error

if __name__ == '__main__':
    run_server()