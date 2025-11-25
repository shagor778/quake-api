from flask import Flask, jsonify
import requests

app = Flask(__name__)

# শুধু USGS থেকে ডাটা আনার লিংক
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

@app.route('/')
def home():
    return "Simple Quake Server Running"

@app.route('/latest')
def get_latest():
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
        return jsonify(formatted)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
