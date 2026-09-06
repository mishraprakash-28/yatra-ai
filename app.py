import json
import os
import urllib.parse
import urllib.request

try:
    import streamlit as st  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    st = None  # type: ignore[assignment]

try:
    import google.generativeai as genai  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]

import streamlit.components.v1 as components  # pyright: ignore[reportMissingImports]

# Page Configuration
if st is not None:
    st.set_page_config(
        page_title="Yatra AI - Global Mobility, Beaches & Route Planner",
        page_icon="🌍",
        layout="wide"
    )

# Robust Secrets & Env Key Retrieval Logic
def get_api_key():
    key = None
    if st is not None:
        try:
            key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            pass
    if not key:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return key

GEMINI_API_KEY = get_api_key()

if st is not None:
    st.title("🌍 Yatra AI - Global Mobility, Beaches & Route Planner")
    st.markdown("Automated ML Dynamic Cost Estimation, Live Map Detection, and AI-Driven Global Itinerary.")
    st.divider()

    # Sidebar User Inputs
    st.sidebar.header("🗺️ Trip & Vehicle Configuration")
    source = st.sidebar.text_input("Source Location:", "Punjab")
    destination = st.sidebar.text_input("Destination Location:", "Goa")
    vehicle_type = st.sidebar.selectbox("Vehicle Type:", ["4-Wheeler (Car/SUV)", "2-Wheeler (Bike/Scooter)"])
    fuel_type = st.sidebar.selectbox("Fuel Type:", ["Petrol", "Diesel", "Electric (EV)"])
    num_days = st.sidebar.number_input("Trip Duration (Days):", min_value=1, max_value=30, value=3)

    plan_btn = st.sidebar.button("🚀 Plan My Entire Trip")

# 1. Real Coordinate-Based Distance Estimator
def get_lat_lon(location_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(location_name)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'YatraAIApp/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass
    return None, None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    import math
    R = 6371  # Earth radius in KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c * 1.3)

def ml_trip_estimator(src, dest, vehicle, fuel, days):
    lat1, lon1 = get_lat_lon(src)
    lat2, lon2 = get_lat_lon(dest)
    
    if lat1 and lat2:
        distance_est = calculate_haversine_distance(lat1, lon1, lat2, lon2)
    else:
        distance_est = 1200
    
    if "2-Wheeler" in vehicle:
        mileage = 45 if fuel == "Petrol" else 75
        fuel_price = 102 if fuel == "Petrol" else 15
        avg_speed = 50
    else:
        mileage = 14 if fuel == "Petrol" else 17 if fuel == "Diesel" else 6
        fuel_price = 102 if fuel == "Petrol" else 92 if fuel == "Diesel" else 15
        avg_speed = 65
        
    travel_hours = round(distance_est / avg_speed, 1)
    fuel_cost = round((distance_est / mileage) * fuel_price, 2)
    hotel_cost_per_day = 2500 if "4-Wheeler" in vehicle else 1200
    total_hotel = hotel_cost_per_day * days
    food_other_cost = 1000 * days
    
    total_budget = round(fuel_cost + total_hotel + food_other_cost, 2)
    
    return {
        "distance": distance_est,
        "travel_time": travel_hours,
        "fuel_cost": fuel_cost,
        "hotel_cost": total_hotel,
        "total_budget": total_budget
    }

# 2. Updated Gemini AI Model Call
def generate_ai_travel_data(src, dest, vehicle, fuel, days):
    if not GEMINI_API_KEY:
        return "⚠️ API Key Missing! Please set `GEMINI_API_KEY` in Streamlit Cloud Secrets."
        
    if genai is None:
        return "⚠️ Google Generative AI module is not installed."

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Valid active models
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
        
        prompt = f"""
        You are an advanced worldwide AI travel and road trip planner. 
        Create a detailed travel guide from {src} to {dest} for a {days}-day trip using a {vehicle} ({fuel}).

        Format the response with these exact markdown sections:
        
        1. 🏝️ **Famous Beaches & Coastal Attractions in/near {dest}**:
           - Top famous beaches or waterfronts in or near {dest}.
           - Key highlights, water sports, sunset views, and best time to visit.
           
        2. 🏛️ **Top Tourist Places & Sightseeing**:
           - Must-visit attractions along the route and inside {dest}.
           - Recommended time to explore each spot.

        3. 🏨 **Recommended Hotels & Stays**:
           - Budget, Mid-range, and Luxury stay options near tourist spots/beaches in {dest}.

        4. ⛽ **Petrol Pumps & EV Charging Stations**:
           - Key fuel stops & EV hubs along the route from {src} to {dest}.

        5. 🛣️ **Route Info & Safety Guidelines ({vehicle})**:
           - Highway conditions, toll estimates, and driving tips for {vehicle} ({fuel}).

        6. ⏳ **Day-by-Day Detailed Itinerary**:
           - Schedule breakdown for Morning, Afternoon, and Evening over {days} days.

        7. 💰 **Estimated Budget Summary**:
           - Cost breakdown for Food, Stay, Fuel, Sightseeing, and Beach Activities.
        """

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception:
                continue

        return "Error: Unable to connect to Gemini AI models. Please verify API key and Google Cloud project settings."

    except Exception as e:
        return f"Error executing AI generation: {str(e)}"

# Main Execution
if st is not None and plan_btn:
    with st.spinner("⚡ Running Real-time Distance ML Engine & AI Route Detection..."):
        ml_data = ml_trip_estimator(source, destination, vehicle_type, fuel_type, num_days)
        
        st.subheader(f"📊 ML Predictive Analytics: {source} ➔ {destination}")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("Est. Distance", f"~{ml_data['distance']} km")
        col2.metric("Drive Time", f"~{ml_data['travel_time']} hrs")
        col3.metric("Fuel Expense", f"₹{ml_data['fuel_cost']}")
        col4.metric("Stay Expense", f"₹{ml_data['hotel_cost']}")
        col5.metric("Total Budget", f"₹{ml_data['total_budget']}", delta="Dynamic ML")

        st.divider()

        # Map Embed
        st.subheader("🗺️ Live Route & Map Detection")
        embed_map_code = f"""
        <iframe width="100%" height="450" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
        src="https://maps.google.com/maps?saddr={urllib.parse.quote(source)}&daddr={urllib.parse.quote(destination)}&output=embed">
        </iframe>
        """
        components.html(embed_map_code, height=470)

        st.divider()

        # AI Result
        st.subheader("🤖 Comprehensive AI Travel, Beach & Mobility Guide")
        ai_result = generate_ai_travel_data(source, destination, vehicle_type, fuel_type, num_days)
        st.markdown(ai_result)

elif st is not None and not plan_btn:
    st.info("👈 Enter Source & Destination in the sidebar and click **Plan My Entire Trip**.")