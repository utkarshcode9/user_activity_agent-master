
# Activity Tracker Application

## Description
The **Activity Tracker Application** is a robust tool designed to monitor and log user activities on a system. This Python-based application is equipped with real-time activity tracking, automated data uploads to Firebase for centralized storage, and modular design for flexibility. The application is ideal for use in personal productivity tracking, employee monitoring, or system usage analytics.

## Features
This section breaks down each feature and explains the corresponding implementation in detail.

### 1. **Activity Tracking (`activity_tracker.py`)**
   - **Keyboard and Mouse Tracking**: The application records user interactions such as key presses and mouse movements. This helps to capture user activity in real-time.
     - The `pyautogui` library is used to track mouse movements and clicks.
     - Keyboard events are captured using custom functions to log when a user is actively using their system.
   - **Timestamps and Logging**: All tracked activities are time-stamped using Python’s `datetime` module to provide accurate logs of when each event occurred.
     - The events are stored locally in structured formats, typically as log files, for later upload.
   - **Multi-threading**: The tracking process runs in the background using Python’s `threading` module, ensuring minimal interruption to the user's tasks.

### 2. **Data Encryption (`cryptography` and `filelock` modules)**
   - **Secure Data Handling**: User data is encrypted using the `cryptography` library to ensure secure storage of sensitive information before it is uploaded to Firebase.
   - **File Locking**: To prevent data corruption, the `filelock` module ensures that only one process can write to a file at a time, providing safe concurrent access to logs.

### 3. **Firebase Integration (`firebase_upload.py`)**
   - **Firebase Admin SDK**: The application integrates with Firebase using the `firebase-admin` library, allowing you to upload activity logs and user data to the cloud in real-time.
   - **Authentication**: The Firebase integration uses service account credentials to authenticate with Firebase securely, ensuring only authorized uploads.
   - **Data Storage**: The uploaded data can be stored in Firebase's Firestore or Realtime Database for later retrieval, analysis, or visualization.
   - **Retry Logic**: The Firebase upload functionality includes retry mechanisms to handle network failures or API timeouts, ensuring that no data is lost during uploads.

### 4. **Real-time Background Processing**
   - **Non-Intrusive Tracking**: The system is designed to run quietly in the background without interrupting the user’s workflow. The activity tracker and the Firebase uploader both operate in separate threads, making the application lightweight.
   - **Signal Handling**: The application uses the `signal` module to gracefully handle system signals and ensures a smooth shutdown without corrupting logs.

### 5. **Modular Design (`main.py`)**
   - **Centralized Control**: The `main.py` script acts as the main entry point for the application, managing both the tracking and the upload processes. This script initializes the activity tracker and periodically calls the upload script to ensure logs are synchronized with Firebase.
   - **Configuration Flexibility**: You can configure which features to enable or disable by modifying the `main.py` script. For instance, you can choose to track only keyboard events or disable Firebase uploads for local-only tracking.

## Installation

### Prerequisites
- **Python 3.x**: Ensure Python is installed on your system.
- **Firebase Project**: You must have a Firebase project with the proper service account credentials.
- **Required Libraries**: Install the necessary libraries using `pip`.

### Steps
1. Clone the repository:
    git clone https://github.com/Utkarsh-Saxena88/user_activity_agent.git

2. Install dependencies:
    pip install -r requirements.txt

3. Configure Firebase:
   - Download your Firebase Admin SDK credentials (`serviceAccountKey.json`).
   - Place the credentials file in the config folder.
   - Modify the Firebase configuration in `firebase_upload.py` to point to your Firebase database.

4. Run the application:
    python main.py

## Usage

### 1. **Tracking User Activity**
   - By running `activity_tracker.py`, the application begins logging user activity such as keyboard input, mouse movement, and system interaction.
   - Example:
     python activity_tracker.py

### 2. **Uploading Logs to Firebase**
   - The `firebase_upload.py` script is responsible for uploading local logs to Firebase. It can be run manually or periodically through a cron job or as a background process in `main.py`.
   - Example:
     python firebase_upload.py

### 3. **Running the Complete Application**
   - The `main.py` script is the entry point that manages both tracking and uploading processes. Run this script to start tracking activities and automatically upload them to Firebase.
   - Example:
     python main.py

## Configuration

### Firebase Setup
1. Download the Firebase Admin SDK credentials from your Firebase console.
2. Place the `serviceAccountKey.json` file in your config folder.
3. Update `firebase_upload.py` to include the correct Firebase database URL and credentials path.

### Adjusting Activity Tracking
- You can modify the `activity_tracker.py` to track additional events or change the logging format. The script is designed to be flexible, allowing you to log more detailed system data if needed.

## Requirements

The following Python packages are required for the project to run:
- **Pillow**: Handles image processing (if screenshots are being logged).
- **cryptography**: Ensures secure encryption of data.
- **filelock**: Prevents concurrent file access issues.
- **firebase-admin**: Integrates with Firebase for secure uploads.
- **google-api-python-client**: Allows for interaction with Google APIs.
- **pyautogui**: Tracks user input like mouse and keyboard events.
- **pytz**: Manages timezone-aware timestamps.
- **requests**: Facilitates HTTP requests, used for API interactions.

Install all dependencies via:
pip install -r requirements.txt

## Contributors
- **Utkarsh-Saxena** - Initial development

Feel free to contribute to this project by opening issues or submitting pull requests.