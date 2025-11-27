import os
import json
import requests
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, messaging, db # db ইম্পোর্ট করা হলো

app = Flask(__name__)

# ================= সিকিউর কানেকশন =================
firebase_config_str = os.environ.get('FIREBASE_CREDENTIALS')

# আপনার ডাটাবেস লিংক (অবশ্যই আপনারটা বসাবেন)
# উদাহরণ: https://earthquakealert-xxxxx.firebaseio.com/
DATABASE_URL = "https://earthquakealert-30dd7-default-rtdb.firebaseio.com/" 

if firebase_config_str:
    cred_dict = json.loads(firebase_config_str)
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        # ডাটাবেস URL সহ ইনিশিলাইজ করা
        firebase_admin.initialize_app(cred, {
            'databaseURL': DATABASE_URL
        })
# ================================================

# ৭ দিনের ডাটা (4.5+ মাত্রা)
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"
last_processed_id = None

@app.route('/')
def home():
    return "Server is Running & Syncing Data!"

@app.route('/test-alert')
def test_alert():
    return send_fcm_alert("TEST: Dhaka", 6.5)

# অটোমেশন রুট (Cron Job এটা চালাবে)
@app.route('/check-alert')
def check_and_notify():
    global last_processed_id
    
    try:
        response = requests.get(USGS_URL)
        data = response.json()
        
        formatted_list = []
        
        if "features" in data and len(data["features"]) > 0:
            # ১. লুপ চালিয়ে ডাটা সাজানো (ম্যাপের জন্য)
            for q in data["features"]:
                props = q["properties"]
                geo = q["geometry"]["coordinates"]
                
                model = {
                    "place": props["place"],
                    "magnitude": props["mag"],
                    "time": props["time"],
                    "depth": geo[2],
                    "lat": geo[1],
                    "lon": geo[0]
                }
                formatted_list.append(model)

            # ২. ফায়ারবেসে পুরো ডাটা সেভ করা (এই লাইনটি আগে মিসিং ছিল)
            ref = db.reference('latest_quakes')
            ref.set(formatted_list)

            # ৩. নোটিফিকেশন লজিক (লেটেস্ট ভূমিকম্পের জন্য)
            latest = data["features"][0]
            current_id = latest["id"]
            
            if last_processed_id is None:
                last_processed_id = current_id
                return jsonify({"status": "Initialized & Data Synced", "count": len(formatted_list)})

            if current_id != last_processed_id:
                last_processed_id = current_id
                if latest["properties"]["mag"] >= 4.5:
                    send_fcm_alert(latest["properties"]["place"], latest["properties"]["mag"])
                
            return jsonify({"status": "Data Synced", "count": len(formatted_list)})
            
    except Exception as e:
        return jsonify({"error": str(e)})
    
    return jsonify({"status": "No data"})

def send_fcm_alert(place, mag, lat, lon):
    try:
        # আমরা 'notification' অংশটি বাদ দিয়েছি, শুধু 'data' পাঠাচ্ছি
        # এতে অ্যাপ ব্যাকগ্রাউন্ডে থাকলেও আমাদের লজিক কাজ করবে
        message = messaging.Message(
            topic='earthquakes',
            data={
                'title': '⚠️ Earthquake Alert!',
                'place': place,
                'mag': str(mag),
                'lat': str(lat),
                'lon': str(lon),
                'type': 'alert'
            },
            android=messaging.AndroidConfig(
                priority='high' # হাই প্রয়োরিটি যাতে স্লিপ মোডেও কাজ করে
            )
        )
        response = messaging.send(message)
        return jsonify({"status": "Alert Sent via FCM (Data Only)!", "response": response})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


