import os
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from google import genai

st.set_page_config(
    page_title="YatraAI — Smart Tourism Companion",
    page_icon="🧭",
    layout="wide",
)

# -----------------------------
# Config
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or st.secrets.get(
    "GEMINI_MODEL", "gemini-3.8-flash"
)

HEADERS = {
    "User-Agent": "YatraAI-Hackathon/1.0 (tourism demo)"
}

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: #08111f;
    color: #eef4ff;
}
.hero {
    padding: 26px 28px;
    border: 1px solid #263a55;
    border-radius: 20px;
    background: linear-gradient(135deg, #10243a, #0b1728);
    margin-bottom: 18px;
}
.hero h1 { margin: 0; font-size: 42px; }
.hero p { margin: 8px 0 0; color: #a9bbd4; font-size: 17px; }
.card {
    border: 1px solid #263a55;
    border-radius: 16px;
    padding: 16px;
    background: #0d1a2b;
    margin-bottom: 12px;
}
.small { color: #a9bbd4; font-size: 13px; }
.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    background: #183a5e;
    color: #d9ecff;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def geocode(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]

@st.cache_data(ttl=900, show_spinner=False)
def nearby_places(lat, lon, radius=5000):
    query = f"""
    [out:json][timeout:25];
    (
      nwr(around:{radius},{lat},{lon})["tourism"~"attraction|museum|gallery|viewpoint|zoo|theme_park"];
      nwr(around:{radius},{lat},{lon})["historic"~"monument|castle|archaeological_site|memorial"];
      nwr(around:{radius},{lat},{lon})["tourism"="hotel"];
      nwr(around:{radius},{lat},{lon})["amenity"~"restaurant|cafe"];
      nwr(around:{radius},{lat},{lon})["amenity"="hospital"];
      nwr(around:{radius},{lat},{lon})["amenity"="police"];
      nwr(around:{radius},{lat},{lon})["amenity"="fire_station"];
    );
    out center tags;
    """
    r = requests.post(
        "https://overpass-api.de/api/interpreter",
        data=query,
        headers=HEADERS,
        timeout=45,
    )
    r.raise_for_status()

    rows = []
    for x in r.json().get("elements", []):
        tags = x.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        xlat = x.get("lat", x.get("center", {}).get("lat"))
        xlon = x.get("lon", x.get("center", {}).get("lon"))
        if xlat is None or xlon is None:
            continue

        if tags.get("tourism") == "hotel":
            category = "Hotel"
        elif tags.get("amenity") == "restaurant":
            category = "Restaurant"
        elif tags.get("amenity") == "cafe":
            category = "Cafe"
        elif tags.get("amenity") == "hospital":
            category = "Hospital"
        elif tags.get("amenity") == "police":
            category = "Police"
        elif tags.get("amenity") == "fire_station":
            category = "Fire Station"
        elif tags.get("historic"):
            category = "Historic Place"
        else:
            category = "Tourist Attraction"

        rows.append({
            "name": name,
            "category": category,
            "lat": float(xlat),
            "lon": float(xlon),
        })

    # Remove duplicates while keeping the first occurrence.
    seen = set()
    unique = []
    for row in rows:
        key = (row["name"].lower(), round(row["lat"], 5), round(row["lon"], 5))
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique

@st.cache_data(ttl=900, show_spinner=False)
def weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def maps_url(lat, lon):
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

def distance_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, asin, sqrt
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

def gemini_text(prompt):
    if not GEMINI_API_KEY:
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Gemini error: {e}"

def build_itinerary(place_name, budget, hours, interest, attractions, hotels, restaurants):
    attractions_text = "\n".join(
        f"- {x['name']} ({x['category']})"
        for x in attractions[:18]
    ) or "No attractions found."

    restaurants_text = "\n".join(
        f"- {x['name']} ({x['category']})"
        for x in restaurants[:10]
    ) or "No food places found."

    hotels_text = "\n".join(
        f"- {x['name']}"
        for x in hotels[:10]
    ) or "No hotels found."

    prompt = f"""
You are YatraAI, an AI tourism planner.

Create a practical tourism itinerary for:
Destination: {place_name}
Budget: INR {budget}
Available time: {hours} hours
Interest: {interest}

Nearby attractions:
{attractions_text}

Nearby restaurants/cafes:
{restaurants_text}

Nearby hotels:
{hotels_text}

Requirements:
1. Make a time-based itinerary from start to finish.
2. Prioritize places matching the interest.
3. Keep it realistic for the available time.
4. Give estimated local travel time between stops.
5. Mention approximate spending categories without inventing exact ticket prices.
6. Suggest one food stop.
7. Add a short budget breakdown.
8. End with 3 smart travel tips.
9. Keep the answer concise and presentation/demo friendly.
"""
    return gemini_text(prompt)

def ask_gemini(question, context):
    prompt = f"""
You are YatraAI, a helpful tourism assistant.
Answer the user's question using the available local context below.
Do not invent exact live prices, opening hours, availability, or distances.
If data is missing, say so clearly.

User question:
{question}

Local context:
{context}
"""
    return gemini_text(prompt)

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
  <div class="badge">AI • MAPS • WEATHER • BUDGET • ITINERARY</div>
  <h1>🧭 YatraAI</h1>
  <p>One map. Every journey. Your AI-powered smart tourism companion.</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("⚙️ Trip Planner")
    destination = st.text_input(
        "Destination / City",
        value="Ahmedabad, India",
        placeholder="e.g. Jaipur, India",
    )
    budget = st.slider("Budget (₹)", 500, 100000, 5000, step=500)
    hours = st.slider("Available time (hours)", 2, 24, 8)
    interest = st.selectbox(
        "What are you interested in?",
        ["Heritage", "Nature", "Food", "Culture", "Family", "Photography", "Mixed"],
    )
    radius = st.slider("Search radius (km)", 1, 20, 5)

    if st.button("🔎 Explore Destination", use_container_width=True):
        st.session_state.pop("selected_destination", None)
        st.session_state.pop("last_plan", None)
        st.rerun()

# -----------------------------
# Location
# -----------------------------
with st.spinner("Finding your destination..."):
    loc = geocode(destination)

if not loc:
    st.error("Destination not found. Try a city name such as Jaipur, Delhi, Ahmedabad, Goa, etc.")
    st.stop()

lat, lon, display_name = loc
st.session_state["selected_destination"] = display_name

with st.spinner("Finding nearby places..."):
    places = nearby_places(lat, lon, radius * 1000)

attractions = [x for x in places if x["category"] in ["Tourist Attraction", "Historic Place"]]
hotels = [x for x in places if x["category"] == "Hotel"]
restaurants = [x for x in places if x["category"] in ["Restaurant", "Cafe"]]
emergency = [x for x in places if x["category"] in ["Hospital", "Police", "Fire Station"]]

# -----------------------------
# Metrics
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("📍 Attractions", len(attractions))
c2.metric("🏨 Hotels", len(hotels))
c3.metric("🍽️ Food", len(restaurants))
c4.metric("🚑 Emergency", len(emergency))

# -----------------------------
# Weather
# -----------------------------
try:
    w = weather(lat, lon)
    current = w.get("current", {})
    st.info(
        f"🌤️ Current weather: **{current.get('temperature_2m', '—')}°C**  •  "
        f"Feels like **{current.get('apparent_temperature', '—')}°C**  •  "
        f"Wind **{current.get('wind_speed_10m', '—')} km/h**"
    )
except Exception:
    st.warning("Weather data is temporarily unavailable.")

# -----------------------------
# Map
# -----------------------------
st.subheader("🗺️ Explore on Map")

m = folium.Map(location=[lat, lon], zoom_start=13, control_scale=True)
folium.Marker(
    [lat, lon],
    tooltip="Your destination",
    popup=display_name,
    icon=folium.Icon(color="blue", icon="home"),
).add_to(m)

icons = {
    "Tourist Attraction": ("green", "camera"),
    "Historic Place": ("darkgreen", "university"),
    "Hotel": ("purple", "bed"),
    "Restaurant": ("orange", "cutlery"),
    "Cafe": ("orange", "coffee"),
    "Hospital": ("red", "plus"),
    "Police": ("red", "shield"),
    "Fire Station": ("red", "fire"),
}

for p in places[:150]:
    color, icon = icons.get(p["category"], ("gray", "info-sign"))
    popup = f"""
    <b>{p['name']}</b><br>
    {p['category']}<br><br>
    <a href="{maps_url(p['lat'], p['lon'])}" target="_blank">Open directions ↗</a>
    """
    folium.Marker(
        [p["lat"], p["lon"]],
        tooltip=f"{p['name']} • {p['category']}",
        popup=folium.Popup(popup, max_width=280),
        icon=folium.Icon(color=color, icon=icon),
    ).add_to(m)

st_folium(m, width=None, height=520, returned_objects=[])

# -----------------------------
# Nearby lists
# -----------------------------
st.subheader("✨ Nearby Recommendations")

tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Attractions", "🏨 Hotels", "🍽️ Food", "🚨 Emergency"])

def render_list(items, limit=10):
    if not items:
        st.info("No nearby places found in the selected radius.")
        return
    for p in items[:limit]:
        d = distance_km(lat, lon, p["lat"], p["lon"])
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"**{p['name']}**  \n"
                f"<span class='small'>{p['category']} • {d:.1f} km away</span>",
                unsafe_allow_html=True,
            )
        with col2:
            st.link_button("Directions", maps_url(p["lat"], p["lon"]))

with tab1:
    render_list(attractions, 12)
with tab2:
    render_list(hotels, 12)
with tab3:
    render_list(restaurants, 12)
with tab4:
    render_list(emergency, 12)

# -----------------------------
# AI itinerary
# -----------------------------
st.subheader("🤖 AI Trip Planner")

if st.button("✨ Generate My AI Itinerary", use_container_width=True):
    with st.spinner("Gemini is creating your personalized itinerary..."):
        plan = build_itinerary(
            display_name,
            budget,
            hours,
            interest,
            attractions,
            hotels,
            restaurants,
        )
    if plan:
        st.session_state["last_plan"] = plan
    else:
        st.session_state["last_plan"] = (
            "Add your Gemini API key in Streamlit Secrets to enable the live AI itinerary."
        )

if "last_plan" in st.session_state:
    st.markdown(
        f"<div class='card'>{st.session_state['last_plan'].replace(chr(10), '<br>')}</div>",
        unsafe_allow_html=True,
    )

# -----------------------------
# Chatbot
# -----------------------------
st.subheader("💬 Ask YatraAI")

context_items = places[:80]
context = "\n".join(
    f"- {x['name']} | {x['category']} | {distance_km(lat, lon, x['lat'], x['lon']):.1f} km"
    for x in context_items
)

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask: best places for 1 day? cheap food? heritage spots?")
if question:
    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask_gemini(question, context)
        if not answer:
            answer = "Add your Gemini API key in Streamlit Secrets to enable the AI chatbot."
        st.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})

# -----------------------------
# Footer
# -----------------------------
st.divider()
st.caption(
    "YatraAI hackathon demo • Map data: OpenStreetMap/Overpass • Weather: Open-Meteo • "
    "AI: Google Gemini • Directions: Google Maps"
)
