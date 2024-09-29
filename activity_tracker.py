import threading
import pyautogui
import time
import random
from datetime import datetime
import os
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
from PIL import ImageFilter
from google.api_core.exceptions import RetryError, DeadlineExceeded

cred = credentials.Certificate('config/db-firebase-credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

class ActivityTracker:
    def __init__(self, uploader, screenshot_interval=5, suspicious_thresholds=None):
        self.last_mouse_position = pyautogui.position()
        self.last_mouse_time = time.time()
        self.last_keystroke_time = time.time()
        self.suspicious_flag = False
        self.screenshot_interval = screenshot_interval
        self.screenshot_type = 'unblurred'  # Default screenshot type
        self.capture_enabled = True  # Default capture enabled
        self.suspicious_thresholds = suspicious_thresholds or {
            'max_speed': 3000,
            'min_randomness': 0.1,
            'keystroke_min_interval': 0.05,
        }
        self.current_timezone = self.detect_timezone()
        self.load_config()
        self.uploader = uploader
        
        self.config_thread = threading.Thread(target=self.run_config_loader)
        self.config_thread.daemon = True  # Daemonize thread to exit when main program exits
        self.config_thread.start()
        
    def run_config_loader(self):
        """ Continuously load configuration every second. """
        while True:
            try:
                self.load_config()  # Load the configuration
                self.check_time_zone_change()
            except Exception as e:
                print(f"Error in run_config_loader: {e}")
            time.sleep(20)  # Wait for 20 second before checking again
    
    def detect_timezone(self):
        # Get the local timezone
        return time.tzname[time.daylight]
    
    def check_time_zone_change(self):
        new_timezone = self.detect_timezone()
        if new_timezone != self.current_timezone:
            print(f"Time zone changed from {self.current_timezone} to {new_timezone}")
            self.current_timezone = new_timezone
    
    def adjust_timestamp(self, timestamp):
        # Adjust the timestamp to the current timezone
        utc_time = pytz.utc.localize(timestamp)
        local_time = utc_time.astimezone(pytz.timezone(self.current_timezone))
        return local_time
    
    def load_config(self):
        config_ref = db.collection('config').document('settings')
        try:
            config = config_ref.get(timeout=10)  # Set a 10-second timeout
            if config.exists:
                config_data = config.to_dict()
                self.screenshot_interval = config_data.get('screenshot_interval', 5)
                self.screenshot_type = config_data.get('screenshot_type', 'unblurred')
                self.capture_enabled = config_data.get('capture_enabled', True)
                self.suspicious_thresholds['max_speed'] = config_data.get('max_speed', self.suspicious_thresholds['max_speed'])
                self.suspicious_thresholds['min_randomness'] = config_data.get('min_randomness', self.suspicious_thresholds['min_randomness'])
                self.suspicious_thresholds['keystroke_min_interval'] = config_data.get('keystroke_min_interval', self.suspicious_thresholds['keystroke_min_interval'])
                timezone = config_data.get('timezone', 'India Standard Time')
                if timezone != str(self.current_timezone):
                    print('Timezone was changed before starting the application.')
                    self.current_timezone = timezone
            else:
                print("Config document does not exist. Using default values.")
        except (RetryError, DeadlineExceeded) as e:
            print(f"Error loading config from Firestore: {e}")
            print("Using last known configuration.")
        except Exception as e:
            print(f"Unexpected error loading config: {e}")
            print("Using default configuration.")

    def update_config(self):
        print("Current Configuration:")
        print(f"Screenshot Interval: {self.screenshot_interval}")
        print(f"Screenshot Type: {self.screenshot_type}")
        print(f"Capture Enabled: {self.capture_enabled}")
        print(f"Max Speed: {self.suspicious_thresholds['max_speed']}")
        print(f"Min Randomness: {self.suspicious_thresholds['min_randomness']}")
        print(f"Keystroke Min Interval: {self.suspicious_thresholds['keystroke_min_interval']}\n")

        try:
            new_interval = input("Enter new screenshot interval (seconds, or press Enter to keep current): ")
            if new_interval:
                self.screenshot_interval = int(new_interval)

            new_type = input("Enter new screenshot type (blurred/unblurred, or press Enter to keep current): ")
            if new_type:
                self.screenshot_type = new_type

            new_capture_enabled = input("Capture enabled (true/false, or press Enter to keep current): ")
            if new_capture_enabled:
                self.capture_enabled = new_capture_enabled.lower() == 'true'

            new_max_speed = input("Enter new max speed (or press Enter to keep current): ")
            if new_max_speed:
                self.suspicious_thresholds['max_speed'] = int(new_max_speed)

            new_min_randomness = input("Enter new min randomness (or press Enter to keep current): ")
            if new_min_randomness:
                self.suspicious_thresholds['min_randomness'] = float(new_min_randomness)

            new_keystroke_interval = input("Enter new keystroke min interval (or press Enter to keep current): ")
            if new_keystroke_interval:
                self.suspicious_thresholds['keystroke_min_interval'] = float(new_keystroke_interval)

            db.collection('config').document('settings').set({
                'screenshot_interval': self.screenshot_interval,
                'screenshot_type': self.screenshot_type,
                'capture_enabled': self.capture_enabled,
                'max_speed': self.suspicious_thresholds['max_speed'],
                'min_randomness': self.suspicious_thresholds['min_randomness'],
                'keystroke_min_interval': self.suspicious_thresholds['keystroke_min_interval'],
            }, merge=True)

            print("Configuration updated successfully!")

        except Exception as e:
            print(f"An error occurred while updating the configuration: {e}")
    
    def capture_screenshot(self, suspicious=False):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if suspicious:
            filename = f"SuspiciousActivity_{timestamp}.jpg"  # Save as JPEG for compression
        else:
            filename = f"UserActivity_{timestamp}.jpg"
        
        os.makedirs('screenshots', exist_ok=True)
        filepath = os.path.join('screenshots', filename)

        screenshot = pyautogui.screenshot()

        if self.screenshot_type == 'blurred':
            screenshot = screenshot.filter(ImageFilter.GaussianBlur(5))  # Adjust the blur radius as needed

        screenshot = screenshot.convert('RGB')

        compression_quality = 85  # Adjust compression quality (0-100)
        screenshot.save(filepath, "JPEG", optimize=True, quality=compression_quality)

        return filepath

    def monitor_mouse_movement(self):
        current_mouse_position = pyautogui.position()
        current_time = time.time()

        distance = ((current_mouse_position[0] - self.last_mouse_position[0]) ** 2 +
                     (current_mouse_position[1] - self.last_mouse_position[1]) ** 2) ** 0.5
        time_diff = current_time - self.last_mouse_time
        speed = distance / time_diff if time_diff > 0 else 0

        randomness = random.random()

        if speed > self.suspicious_thresholds['max_speed'] or randomness < self.suspicious_thresholds['min_randomness']:
            self.suspicious_flag = True
            print("Suspicious mouse activity detected")
        else:
            self.suspicious_flag = False
            print("Normal User mouse activity detected")

        self.last_mouse_position = current_mouse_position
        self.last_mouse_time = current_time

    def monitor_keystrokes(self):
        current_time = time.time()
        keystroke_interval = current_time - self.last_keystroke_time

        if keystroke_interval < self.suspicious_thresholds['keystroke_min_interval']:
            self.suspicious_flag = True
            print("Suspicious keystroke activity detected")
        else:
            self.suspicious_flag = False
            print("Normal User keystroke activity detected")

        self.last_keystroke_time = current_time

    def track_user_activity(self):
        self.check_time_zone_change()
        if not self.capture_enabled:
            return None  # Return None if capturing is disabled

        self.monitor_mouse_movement()
        self.monitor_keystrokes()

        if self.suspicious_flag:
            return self.capture_screenshot(suspicious=True)
        else:
            return self.capture_screenshot(suspicious=False)

    def handle_shutdown(self):
        """Ensure safe shutdown handling."""
        print("Tracker shutting down...")
        self.uploader.shutdown_handler()