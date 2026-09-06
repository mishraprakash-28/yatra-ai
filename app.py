import os
import math
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    import streamlit as st  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - helps IDE/static analysis when dependency is not installed
    class _StreamlitFallback:
        def __getattr__(self, name):
            raise ModuleNotFoundError("streamlit is required to run this app")

    st = _StreamlitFallback()

import folium  # pyright: ignore[reportMissingImports]

try:
    import importlib

    st_folium = importlib.import_module("streamlit_folium").st_folium
except ModuleNotFoundError:  # pragma: no cover - dependency is required at runtime
    def st_folium(*args, **kwargs):
        raise ModuleNotFoundError("streamlit-folium is required to run this app")
from google import genai


def _get_json(url, headers=None, timeout=15):
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url, form_data, timeout=15):
    request = Request(
        url,
        data=form_data.encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="YatraAI - Smart Travel Companion",
    page_icon="✈️",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(
            circle at 80% 0%,
            #123b60 0%,
            #07101f 35%
        );

    color: white;
}

.main-title {
    font-size: 65px;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -3px;
}

.gradient-text {
    color: #5de1ff;
}

.subtitle {
    color: #9cafc5;
    font-size: 18px;
    line-height: 1.7;
}

.card {
    background: #0d1c2e;
    border: 1px solid #29415c;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 12px;
}

.place-card {
    background: #0c1a2b;
    border: 1px solid #203850;
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 8px;
}

.small-text {
    color: #8195ad;
    font-size: 12px;
}

.ai-box {
    background:
        linear-gradient(
            135deg,
            #102a40,
            #0b1829
        );

    border: 1px solid #31516c;
    border-radius: 20px;
    padding: 25px;
}

.important {
    color: #5de1ff;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# GEMINI SETUP
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    client = None


# =========================================================
# DEFAULT LOCATION
# =========================================================

DEFAULT_LAT = 23.0225
DEFAULT_LON = 72.5714


# =========================================================
# DISTANCE
# =========================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


# =========================================================
# GEOCODING
# =========================================================

def search_location(query):
    url = (
        "https://nominatim.openstreetmap.org/search"
        "?format=json"
        "&limit=1"
        f"&q={quote(query)}"
    )

    try:
        data = _get_json(
            url,
            headers={"User-Agent": "YatraAI-Hackathon-App"},
            timeout=15
        )

        if not data:
            return None

        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "name": data[0]["display_name"].split(",")[0]
        }
    except Exception:
        return None


# =========================================================
# OVERPASS PLACES (WITH MULTIPLE FALLBACKS)
# =========================================================

def get_nearby_places(lat, lon):
    query = f"""
    [out:json][timeout:30];

    (
        nwr(around:7000, {lat}, {lon})["tourism"~"attraction|museum|gallery|viewpoint|zoo|theme_park"];
        nwr(around:7000, {lat}, {lon})["historic"~"monument|castle|archaeological_site|memorial"];
        nwr(around:7000, {lat}, {lon})["tourism"="hotel"];
        nwr(around:7000, {lat}, {lon})["amenity"~"restaurant|cafe"];
        nwr(around:7000, {lat}, {lon})["amenity"~"hospital|police|fire_station"];
    );

    out center tags;
    """

    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]

    data = {}
    for url in OVERPASS_URLS:
        try:
            status, response_data = _post_json(
                url, f"data={quote(query)}", timeout=15
            )
            if status == 200:
                data = response_data
                break
        except Exception:
            continue

    places = []

    for item in data.get("elements", []):
        tags = item.get("tags", {})
        item_lat = item.get("lat")
        item_lon = item.get("lon")

        if item_lat is None:
            center = item.get("center", {})
            item_lat = center.get("lat")
            item_lon = center.get("lon")

        if item_lat is None or item_lon is None:
            continue

        tourism = tags.get("tourism")
        amenity = tags.get("amenity")

        if tourism == "hotel":
            place_type = "hotel"
        elif amenity in ["restaurant", "cafe"]:
            place_type = "food"
        elif amenity in ["hospital", "police", "fire_station"]:
            place_type = "emergency"
        else:
            place_type = "attraction"

        place = {
            "name": tags.get("name", "Unnamed place"),
            "type": place_type,
            "lat": item_lat,
            "lon": item_lon,
            "distance": calculate_distance(lat, lon, item_lat, item_lon)
        }
        places.append(place)

    places.sort(key=lambda x: x["distance"])
    return places


# =========================================================
# WEATHER
# =========================================================

def get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )

    try:
        data = _get_json(url, timeout=15)
        return data.get("current")
    except Exception:
        return None


# =========================================================
# GEMINI ITINERARY
# =========================================================

def generate_itinerary(destination, budget, hours, interest, places):
    if not client:
        return "Gemini API key not configured."

    place_text = "\n".join(
        [
            f"{i+1}. {p['name']} | {p['type']} | {p['distance']:.1f} km"
            for i, p in enumerate(places[:30])
        ]
    )

    prompt = f"""
You are YatraAI, an AI travel planner.

Destination: {destination}
Budget: ₹{budget}
Available time: {hours} hours
Interest: {interest}

Nearby live places:
{place_text}

Create a realistic travel itinerary.

Rules:
1. Prefer places from the supplied list.
2. Do not invent exact ticket prices.
3. Do not invent hotel availability.
4. Do not invent opening hours.
5. Clearly mark estimates.
6. Keep travel practical.
7. Make the answer visually easy to read.
8. Include estimated spending.
9. Include travel tips.

Return:
TITLE
SUMMARY
ITINERARY
TIME:
PLACE:
ACTIVITY:
ESTIMATED SPEND:
TOTAL ESTIMATED COST
TRAVEL TIPS
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini error: {str(e)}"


# =========================================================
# GEMINI CHAT
# =========================================================

def ask_gemini(question, destination, places):
    if not client:
        return "Please configure GEMINI_API_KEY."

    place_text = ", ".join([p["name"] for p in places[:20]])

    prompt = f"""
You are YatraAI, a helpful tourism assistant.

Destination: {destination}
Nearby places: {place_text}

User question: {question}

Give a concise, helpful answer.
Do not invent live information.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return str(e)


# =========================================================
# SESSION STATE
# =========================================================

if "location" not in st.session_state:
    st.session_state.location = {
        "lat": DEFAULT_LAT,
        "lon": DEFAULT_LON,
        "name": "Ahmedabad"
    }

if "places" not in st.session_state:
    st.session_state.places = []

if "chat" not in st.session_state:
    st.session_state.chat = []


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2>✈️ Yatra<span style="color:#5de1ff">AI</span></h2>
            <div class="small-text">AI SMART TRAVEL COMPANION</div>
        </div>
        <div>🟢 Live Travel Data</div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div style="padding-top:50px; padding-bottom:30px;">
        <div class="eyebrow">AI • MAPS • DISCOVERY • PLANNING</div>
        <div class="main-title">One map. <br><span class="gradient-text">Every journey.</span></div>
        <p class="subtitle">
            YatraAI understands your destination, budget, time and interests —
            then turns nearby places into a personalized journey.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SEARCH
# =========================================================

col1, col2 = st.columns([5, 1])

with col1:
    destination = st.text_input("🔎 Search destination", value=st.session_state.location["name"])

with col2:
    search_button = st.button("Explore", use_container_width=True)

if search_button:
    with st.spinner("Finding destination..."):
        result = search_location(destination)

    if result:
        st.session_state.location = result
        with st.spinner("Discovering nearby places..."):
            st.session_state.places = get_nearby_places(result["lat"], result["lon"])
    else:
        st.error("Destination not found.")


# =========================================================
# WEATHER
# =========================================================

weather = get_weather(st.session_state.location["lat"], st.session_state.location["lon"])

if weather:
    w1, w2, w3 = st.columns(3)
    w1.metric("🌡️ Temperature", f"{weather.get('temperature_2m')} °C")
    w2.metric("💧 Humidity", f"{weather.get('relative_humidity_2m')}%")
    w3.metric("💨 Wind", f"{weather.get('wind_speed_10m')} km/h")


# =========================================================
# CURRENT LOCATION
# =========================================================

st.info("📍 For current-location detection, allow location permission in your browser. Then search your current city/area.")


# =========================================================
# LOAD PLACES
# =========================================================

if not st.session_state.places:
    with st.spinner("Loading nearby places..."):
        st.session_state.places = get_nearby_places(
            st.session_state.location["lat"],
            st.session_state.location["lon"]
        )

places = st.session_state.places


# =========================================================
# STATS
# =========================================================

attractions = [p for p in places if p["type"] == "attraction"]
hotels = [p for p in places if p["type"] == "hotel"]
food = [p for p in places if p["type"] == "food"]
emergency = [p for p in places if p["type"] == "emergency"]

s1, s2, s3, s4 = st.columns(4)
s1.metric("🏛️ Attractions", len(attractions))
s2.metric("🏨 Hotels", len(hotels))
s3.metric("🍽️ Food", len(food))
s4.metric("🚨 Emergency", len(emergency))


# =========================================================
# FILTER
# =========================================================

st.subheader("Explore Near You")

category = st.radio(
    "Category",
    ["All", "Attractions", "Hotels", "Food", "Emergency"],
    horizontal=True
)

if category == "Attractions":
    visible = attractions
elif category == "Hotels":
    visible = hotels
elif category == "Food":
    visible = food
elif category == "Emergency":
    visible = emergency
else:
    visible = places


# =========================================================
# MAP
# =========================================================

st.subheader("🗺️ Smart Travel Map")

map_object = folium.Map(
    location=[st.session_state.location["lat"], st.session_state.location["lon"]],
    zoom_start=13
)

folium.Marker(
    [st.session_state.location["lat"], st.session_state.location["lon"]],
    tooltip="Your destination",
    popup=st.session_state.location["name"],
    icon=folium.Icon(color="blue", icon="user")
).add_to(map_object)

for place in visible[:100]:
    if place["type"] == "hotel":
        icon, color = "bed", "purple"
    elif place["type"] == "food":
        icon, color = "cutlery", "orange"
    elif place["type"] == "emergency":
        icon, color = "plus", "red"
    else:
        icon, color = "camera", "green"

    popup = f"""
    <b>{place['name']}</b><br>
    📏 {place['distance']:.1f} km away<br><br>
    <a href="https://www.google.com/maps/dir/?api=1&destination={place['lat']},{place['lon']}" target="_blank">
    🧭 Get Directions
    </a>
    """

    folium.Marker(
        [place["lat"], place["lon"]],
        tooltip=place["name"],
        popup=folium.Popup(popup, max_width=300),
        icon=folium.Icon(color=color, icon=icon)
    ).add_to(map_object)

st_folium(map_object, width="100%", height=560)


# =========================================================
# NEARBY PLACES
# =========================================================

st.subheader("📍 Nearby Recommendations")

for place in visible[:12]:
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        if place["type"] == "hotel":
            st.write("🏨")
        elif place["type"] == "food":
            st.write("🍽️")
        elif place["type"] == "emergency":
            st.write("🚨")
        else:
            st.write("🏛️")

    with col2:
        st.markdown(
            f"**{place['name']}**\n\n<span class='small-text'>{place['distance']:.1f} km • {place['type']}</span>",
            unsafe_allow_html=True
        )

    with col3:
        url = f"https://www.google.com/maps/dir/?api=1&destination={place['lat']},{place['lon']}"
        st.link_button("🧭", url)


# =========================================================
# AI PLANNER
# =========================================================

st.divider()
st.header("🤖 AI Smart Trip Planner")
st.write("Tell YatraAI your budget, available time and travel interest. Gemini will create a personalized itinerary using the live nearby places.")

p1, p2 = st.columns(2)
with p1:
    budget = st.slider("💰 Budget", 500, 20000, 3000, step=500)
with p2:
    hours = st.slider("⏱️ Available time", 2, 16, 8)

interest = st.selectbox(
    "🎯 What do you like?",
    ["Culture & History", "Food & Local Life", "Nature & Relaxation", "Shopping & Markets", "Family & Fun"]
)

if st.button("✨ Generate AI Itinerary", use_container_width=True):
    with st.spinner("Gemini is creating your journey..."):
        result = generate_itinerary(st.session_state.location["name"], budget, hours, interest, places)

    st.markdown(f'<div class="ai-box">{result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)


# =========================================================
# AI CHATBOT
# =========================================================

st.divider()
st.header("💬 Ask YatraAI")
st.write("Ask anything about your trip.")

question = st.text_input("Your question", placeholder="Example: I have ₹2000. What should I visit?")

if st.button("Ask Gemini"):
    if question:
        with st.spinner("YatraAI is thinking..."):
            answer = ask_gemini(question, st.session_state.location["name"], places)

        st.session_state.chat.append({"question": question, "answer": answer})

for item in reversed(st.session_state.chat):
    st.markdown(
        f"""
        <div class="place-card">
        <b>👤 You:</b> {item['question']}<br><br>
        <b>🤖 YatraAI:</b> {item['answer']}
        </div>
        """,
        unsafe_allow_html=True
    )# app.py ke end me add karein
app = st._main

if __name__ == '__main__':
    st._main()
    {
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}