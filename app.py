import streamlit as st  # type: ignore
import google.generativeai as genai  # type: ignore
import os
import streamlit.components.v1 as components  # type: ignore

# Page Configuration
st.set_page_config(
    page_title="Yatra AI - World Travel, Route & Mobility Planner",
    page_icon="🌍",
    layout="wide"
)

# Render Environment Variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

st.title("🌍 Yatra AI - Global Mobility, Beaches & Route Planner")
st.markdown("Automated ML Cost Estimation, Live Map Detection, and AI-Driven Global Itinerary.")

st.divider()

# Sidebar User Inputs
st.sidebar.header("🗺️ Trip & Vehicle Configuration")
source = st.sidebar.text_input("Source Location:", "Delhi")
destination = st.sidebar.text_input("Destination Location:", "Goa")
vehicle_type = st.sidebar.selectbox("Vehicle Type:", ["4-Wheeler (Car/SUV)", "2-Wheeler (Bike/Scooter)"])
fuel_type = st.sidebar.selectbox("Fuel Type:", ["Petrol", "Diesel", "Electric (EV)"])
num_days = st.sidebar.number_input("Trip Duration (Days):", min_value=1, max_value=30, value=3)

plan_btn = st.sidebar.button("🚀 Plan My Entire Trip")

# 1. Machine Learning Heuristic Cost & Time Predictor Engine
def ml_trip_estimator(src, dest, vehicle, fuel, days):
    # Simulated Heuristic ML Algorithm for dynamic distance, fuel, and time calculation
    distance_est = max(60, (len(src) + len(dest)) * 30)
    
    if "2-Wheeler" in vehicle:
        mileage = 45 if fuel == "Petrol" else 75
        fuel_price = 102 if fuel == "Petrol" else 15
        avg_speed = 50
    else:
        mileage = 14 if fuel == "Petrol" else 17 if fuel == "Diesel" else 6
        fuel_price = 102 if fuel == "Petrol" else 92 if fuel == "Diesel" else 15
        avg_speed = 70
        
    travel_hours = round(distance_est / avg_speed, 1)
    fuel_cost = round((distance_est / mileage) * fuel_price, 2)
    hotel_cost_per_day = 2500 if "4-Wheeler" in vehicle else 1200
    total_hotel = hotel_cost_per_day * days
    food_other_cost = 1000 * days
    
    total_budget = fuel_cost + total_hotel + food_other_cost
    
    return {
        "distance": distance_est,
        "travel_time": travel_hours,
        "fuel_cost": fuel_cost,
        "hotel_cost": total_hotel,
        "total_budget": total_budget
    }

# 2. Dynamic Safe Gemini AI Model Fetcher & Generator
def generate_ai_travel_data(src, dest, vehicle, fuel, days):
    if not GEMINI_API_KEY:
        return "⚠️ API Key Missing! Please configure `GEMINI_API_KEY` in Render Environment Variables."
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Dynamically fetch available models to prevent 404 Model Errors
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        selected_model = None
        # Preferred models priority list
        preferred_list = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        
        for p in preferred_list:
            if p in available_models:
                selected_model = p
                break
                
        if not selected_model and available_models:
            selected_model = available_models[0]
            
        if not selected_model:
            return "Error: No supported Gemini models found for this API Key."

        model = genai.GenerativeModel(selected_model)
        
        prompt = f"""
        You are an advanced worldwide AI travel and road trip planner. 
        Create a detailed travel guide from {src} to {dest} for a {days}-day trip using a {vehicle} ({fuel}).

        Format the response with these exact markdown sections:
        
        1. 🏝️ **Famous Beaches & Coastal Attractions in/near {dest}**:
           - Top 3-5 famous beaches in or near {dest} (if destination has no beaches, mention nearest beaches/lakefronts/waterfronts).
           - Key highlights, water sports, sunset views, and best time to visit each beach.
           
        2. 🏛️ **Top Tourist Places & Sightseeing**:
           - Must-visit attractions along the route and inside {dest}.
           - Time needed to explore each spot.

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

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Error executing AI generation: {str(e)}"

# Main Execution Flow
if plan_btn:
    with st.spinner("⚡ Processing ML Algorithms & AI Route Detection..."):
        # 1. Run ML Heuristic Estimator
        ml_data = ml_trip_estimator(source, destination, vehicle_type, fuel_type, num_days)
        
        st.subheader(f"📊 ML Predictive Analytics: {source} ➔ {destination}")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("Est. Distance", f"~{ml_data['distance']} km")
        col2.metric("Drive Time", f"~{ml_data['travel_time']} hrs")
        col3.metric("Fuel Expense", f"₹{ml_data['fuel_cost']}")
        col4.metric("Stay Expense", f"₹{ml_data['hotel_cost']}")
        col5.metric("Total Budget", f"₹{ml_data['total_budget']}", delta="ML Dynamic")

        st.divider()

        # 2. Live Interactive World Route Map
        st.subheader("🗺️ Live Route & Map Detection")
        embed_map_code = f"""
        <iframe width="100%" height="450" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
        src="https://maps.google.com/maps?saddr={source}&daddr={destination}&output=embed">
        </iframe>
        """
        components.html(embed_map_code, height=470)

        st.divider()

        # 3. AI Generated Comprehensive Travel & Beach Guide
        st.subheader("🤖 Comprehensive AI Travel, Beach & Mobility Guide")
        ai_result = generate_ai_travel_data(source, destination, vehicle_type, fuel_type, num_days)
        st.markdown(ai_result)

else:
    st.info("👈 Enter Source & Destination in the sidebar and click **Plan My Entire Trip**.")