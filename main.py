import time
import requests
from mcstatus import JavaServer
from datetime import datetime
import os

import threading
from flask import Flask

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHECK_INTERVAL = 60  
LOG_FILE = "status_log.txt"

last_status = None

#logging
def log_message(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_line = f"{timestamp} {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

#DC
def send_discord_message(message):
    log_message(f"Sending to Discord: {message}")
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

def status_loop():
    global last_status, last_change_time
    while True:
        try:
            server = JavaServer.lookup(SERVER_ADDRESS)
            # check server status (ping server)
            try:
                status = server.status()
                status_ok = True
            except Exception:
                status_ok = False
            # check server query (joinable)
            try:
                query = server.query()
                query_ok = True
            except Exception:
                query_ok = False
            # logic status
            if not status_ok and not query_ok:
                current_status = "offline"
            elif status_ok and not query_ok:
                current_status = "booting"
            else:
                current_status = "online"
        except Exception:
            current_status = "offline"
    
        if last_status != current_status:
            if current_status == "online":
                send_discord_message("✅ **Minecraft server ONLINE**")
            elif current_status == "booting":
                send_discord_message("⚙️ **Server is BOOTING UP**")
            elif current_status == "offline":
                send_discord_message("⛔ **Minecraft server OFFLINE**")
                
            log_message(f"Status changed to: {current_status.upper()}")
    
        last_status = current_status
        time.sleep(CHECK_INTERVAL)

# --- FLASK WEB SERVER ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Aternos notifier is running."

# --- START EVERYTHING ---
if __name__ == "__main__":
    # Start the background thread
    threading.Thread(target=status_loop, daemon=True).start()

    # Run Flask so Render keeps the service alive
    port = int(os.getenv("PORT", 10000))  # Render provides this automatically
    app.run(host="0.0.0.0", port=port)