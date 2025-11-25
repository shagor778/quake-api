from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# ================= চাবি বসান =================
ONESIGNAL_APP_ID = "1026e9bb-84db-462c-b129-39ed16c65790"
ONESIGNAL_API_KEY = "os_v2_app_catoto4e3ndczmjjhhwrnrsxsdjdyitivmde5s4p3ceaaqdxe6ace7oztu2ipcernmi5kdaj4l43zoewlk7i7a3vgzhgohha5ox3ckqcornjob//175"
# ==========================================

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
last_processed_id = None

@app.route('/')
def home():
    return "Server is Running!"

@app.route('/latest')
def get_latest():
    return jsonify(fetch_usgs_data())

# অটোমেশন লিংক
@app.route('/check-alert')
def check_and_notify():
    global last_processed_id
    
    raw_data = fetch_usgs_data()
    if not raw_data:
        return jsonify({"status": "No data"})

    latest = raw_data[0]
    current_id = latest['id']
    magnitude = latest['magnitude']
    place = latest['place']
    lat = latest['lat']
    lon = latest['lon']

    if last_processed_id is None:
        last_processed_id = current_id
        return jsonify({"status": "Initialized", "id": current_id})

    if current_id != last_processed_id:
        last_processed_id = current_id
        
        if magnitude >= 4.5:
            # এখানে আমরা ৪টি তথ্য পাঠাচ্ছি
            send_notification(place, magnitude, lat, lon)
            return jsonify({"status": "Alert Sent!", "place": place})
        
    return jsonify({"status": "No new earthquake"})

# টেস্ট রুট
@app.route('/test-alert')
def test_alert():
    # এখানেও ৪টি তথ্য পাঠাচ্ছি
    send_notification("TEST: Dhaka, Bangladesh", 6.5, 23.81, 90.41)
    return jsonify({"status": "Test Alert Sent!", "message": "Check phone notification!"})

# ডাটা আনার ফাংশন
def fetch_usgs_data():
    try:
        response = requests.get(USGS_URL)
        data = response.json()
        formatted = []
        if "features" in data:
            for q in data["features"]:
                props = q["properties"]
                geo = q["geometry"]["coordinates"]
                formatted.append({
                    "id": q["id"],
                    "place": props["place"],
                    "magnitude": props["mag"],
                    "time": props["time"],
                    "depth": geo[2],
                    "lat": geo[1],
                    "lon": geo[0]
                })
        return formatted
    except:
        return []

# নোটিফিকেশন ফাংশন (আপডেট করা হয়েছে)
# আগে ছিল: def send_notification(place, mag):
# এখন হলো:
def send_notification(place, mag, lat, lon):
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"],
        "headings": {"en": "⚠️ Earthquake Alert!"},
        "contents": {"en": f"Magnitude {mag} at {place}"},
        # এই Data অংশটি অ্যাপের ম্যাপের জন্য জরুরি
        "data": {"type": "quake", "mag": mag, "place": place, "lat": lat, "lon": lon}
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_API_KEY}"
    }
    requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

