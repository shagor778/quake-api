import os
import json
import requests
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# ================= সিকিউর কানেকশন (Render ENV থেকে) =================
# আমরা Render এর 'Environment Variable' থেকে চাবি নিব
firebase_config_str = os.environ.get('FIREBASE_CREDENTIALS')

if firebase_config_str:
    # স্ট্রিং থেকে JSON এ কনভার্ট করা
    cred_dict = json.loads(firebase_config_str)
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
# =================================================================

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
last_processed_id = None

@app.route('/')
def home():
    return "FCM Server is Running!"

# ১. টেস্ট রুট (ম্যানুয়াল চেক করার জন্য)
@app.route('/test-alert')
def test_alert():
    return send_fcm_alert("TEST: Dhaka, Bangladesh", 6.5)

# ২. অটোমেশন রুট (Cron Job এর জন্য)
@app.route('/check-alert')
def check_and_notify():
    global last_processed_id
    
    try:
        response = requests.get(USGS_URL)
        data = response.json()
        
        if "features" in data and len(data["features"]) > 0:
            latest = data["features"][0]
            props = latest["properties"]
            
            current_id = latest["id"]
            place = props["place"]
            mag = props["mag"]

            # প্রথমবার সার্ভার চালু হলে নোটিফিকেশন যাবে না
            if last_processed_id is None:
                last_processed_id = current_id
                return jsonify({"status": "Initialized", "id": current_id})

            # নতুন ভূমিকম্প এবং মাত্রা ৪.৫ এর বেশি হলে
            if current_id != last_processed_id:
                last_processed_id = current_id
                
                if mag >= 4.5:
                    return send_fcm_alert(place, mag)
                
            return jsonify({"status": "No new earthquake"})
            
    except Exception as e:
        return jsonify({"error": str(e)})
    
    return jsonify({"status": "No data"})

# ৩. নোটিফিকেশন ফাংশন
def send_fcm_alert(place, mag):
    try:
        # 'earthquakes' টপিকের সবাইকে মেসেজ পাঠাবে
        message = messaging.Message(
            topic='earthquakes',
            notification=messaging.Notification(
                title='⚠️ Earthquake Alert!',
                body=f'Magnitude {mag} detected at {place}',
            ),
            data={
                'place': place,
                'mag': str(mag),
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            }
        )
        response = messaging.send(message)
        return jsonify({"status": "Alert Sent via FCM!", "response": response})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
