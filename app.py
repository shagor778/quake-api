from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# ================= চাবি বসান (উদ্ধৃতি চিহ্ন "" সহ) =================
# আপনার ড্যাশবোর্ড থেকে মিলিয়ে সঠিক চাবি বসান
ONESIGNAL_APP_ID = "1026e9bb-84db-462c-b129-39ed16c65790"
ONESIGNAL_API_KEY = "os_v2_app_catoto4e3ndczmjjhhwrnrsxsannaetl6wfuf4fvgpdwzrdt2e4ecetoksmgvbqdiwyhf6z4k46mnhyi2d5e2b6xbedb4per2sjwvuq"
# =============================================================

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
last_processed_id = None

@app.route('/')
def home():
    return "Quake Server is Running! Access /test-alert to check notifications."

@app.route('/latest')
def get_latest():
    return jsonify(fetch_usgs_data())

# অটোমেশন রুট
@app.route('/check-alert')
def check_and_notify():
    global last_processed_id
    
    raw_data = fetch_usgs_data()
    if not raw_data:
        return jsonify({"status": "No data fetched"})

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
            # নোটিফিকেশন ফাংশন কল করা হচ্ছে
            response = send_notification(place, magnitude, lat, lon)
            return jsonify({
                "status": "Alert Sent!", 
                "place": place, 
                "onesignal_response": response # OneSignal কী বলল তা দেখাবে
            })
        
    return jsonify({"status": "No new earthquake"})

# ============ ম্যানুয়াল টেস্ট রুট (ডিবাগিং সহ) ============
@app.route('/test-alert')
def test_alert():
    # সরাসরি OneSignal রেসপন্স রিটার্ন করবে
    try:
        response = send_notification("TEST: Dhaka, Bangladesh", 6.5, 23.81, 90.41)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)})
# =======================================================

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

def send_notification(place, mag, lat, lon):
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"], # এটা চেক করুন, 'All' বা 'Active Users' না
        "headings": {"en": "⚠️ Earthquake Alert!"},
        "contents": {"en": f"Magnitude {mag} at {place}"},
        "data": {"type": "quake", "mag": mag, "place": place, "lat": lat, "lon": lon}
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_API_KEY}"
    }
    
    # পোস্ট রিকোয়েস্ট পাঠানো
    req = requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)
    
    # রেসপন্স JSON আকারে ফেরত দেওয়া
    return req.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


