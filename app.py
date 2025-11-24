from flask import Flask, jsonify
import requests
import json

app = Flask(__name__)

# কনফিগারেশন
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

@app.route('/')
def home():
    return "Quake Server is Running! Access /latest to get data."

@app.route('/latest')
def get_latest_quakes():
    try:
        # ১. USGS থেকে লাইভ ডাটা আনা
        response = requests.get(USGS_URL)
        data = response.json()
        
        # ২. আমাদের অ্যাপের জন্য ডাটা সুন্দর করে সাজানো
        formatted_data = []
        if "features" in data:
            for quake in data["features"]:
                props = quake["properties"]
                geo = quake["geometry"]["coordinates"]
                
                model = {
                    "place": props["place"],
                    "magnitude": props["mag"],
                    "time": props["time"],
                    "depth": geo[2],
                    "lat": geo[1],
                    "lon": geo[0]
                }
                formatted_data.append(model)
        
        # ৩. JSON রিটার্ন করা (অ্যাপ এটাই পাবে)
        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)