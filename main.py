import signal
import time
import os
import sys
from activity_tracker import ActivityTracker
from firebase_upload import FirebaseUploader
from filelock import FileLock, Timeout

LOCK_FILE = "app_instance.lock"  # Name of the lock file

def check_single_instance():
    pid_file = 'instance.pid'
    if os.path.exists(pid_file):
        print("Another instance is already running.")
        sys.exit(1)
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

def main():
    try:
        # Try to acquire a file lock to ensure only one instance is running
        lock = FileLock(LOCK_FILE)
        
        lock.acquire(timeout=1)  # Raise exception if unable to acquire within 1 second
        print("Application lock acquired. Running...")
        
        # Initialize Firebase uploader
        firebase_uploader = FirebaseUploader(
            cred_path='config/db-firebase-credentials.json', 
            bucket_name='user-activity-db.appspot.com',
            password='7458'
        )
        firebase_uploader.load_queue()

        # Directory where screenshots will be saved before uploading
        screenshot_directory = 'screenshots'
        if not os.path.exists(screenshot_directory):
            os.makedirs(screenshot_directory)
            
        # Initialize the ActivityTracker
        tracker = ActivityTracker(uploader=firebase_uploader)
        
        def signal_handler(sig, frame):
            """Handle application shutdown."""
            print("\nReceived shutdown signal.")
            tracker.handle_shutdown()
            lock.release()
            exit(0)

        # Catch system interrupt (e.g., CTRL+C)
        signal.signal(signal.SIGINT, signal_handler)

        # Poll for configuration updates
        try:
            # Prompt for configuration update only once at the start
            # if input("Do you want to update configuration? (yes/no): ").strip().lower() == "yes":
            #     tracker.update_config()
            
            while True:
                screenshot_path = tracker.track_user_activity()
                
                if screenshot_path:  # Check if a valid screenshot path was returned
                    try:
                        # Upload the screenshot to Firebase
                        firebase_uploader.upload_file(screenshot_path)
                        print(f"Uploaded {screenshot_path} to Firebase.")

                        # Optionally delete local screenshot after upload
                        if os.path.exists(screenshot_path):
                            os.remove(screenshot_path)
                            print(f"Deleted local file: {screenshot_path}")

                    except Exception as e:
                        print(f"Failed to upload {screenshot_path} to Firebase: {e}")

                # Wait for the user-defined screenshot interval before tracking again
                time.sleep(tracker.screenshot_interval)
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            tracker.handle_shutdown()
            lock.release()
            
    except Timeout:
        print("Another instance of the application is already running. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
