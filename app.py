import os
import streamlit as st  # pyright: ignore[reportMissingImports]
import google.generativeai as genai  # pyright: ignore[reportMissingImports]

# Page Configuration
st.set_page_config(
    page_title="Yatra AI - World Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# AI Setup - Secrets ya Input se key lega
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Header
st.title("✈️ Yatra AI - Global Tourism & Travel Planner")
st.markdown("Search travel recommendations, spots, and itineraries for **ANY TWO CITIES IN THE WORLD**.")

st.divider()

# Sidebar Inputs
st.sidebar.header("🔍 Search Travel Route")
origin = st.sidebar.text_input("Source Location:", "Paris")
destination = st.sidebar.text_input("Destination Location:", "Tokyo")
days = st.sidebar.number_input("Trip Duration (Days):", min_value=1, max_value=15, value=3)

search_btn = st.sidebar.button("🚀 Plan My Trip")

# Gemini API Integration
def get_ai_travel_plan(source, dest, duration):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Act as a expert travel guide. Create a structured travel plan from {source} to {dest} for {duration} days.
        Provide the response in clear Markdown with these sections:
        
        1. 🏛️ **Top Attractions in {dest}**: List top 5 spots with a 1-line description each.
        2. 📅 **{duration}-Day Suggested Itinerary**: Daily breakdown (Morning, Afternoon, Evening).
        3. 🚗 **Travel Options**: Best routes/transportation from {source} to {dest} (Flight, Train, Road).
        4. 💡 **Smart Travel Tips**: Currency, best time to visit, and local culture tips.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error fetching details: {str(e)}"

# Display Logic
if search_btn:
    if not GEMINI_API_KEY:
        st.error("⚠️ API Key is missing! Add `GEMINI_API_KEY` in Streamlit secrets or code.")
    else:
        with st.spinner(f"AI is planning your trip from {origin} to {destination}..."):
            plan_details = get_ai_travel_plan(origin, destination, days)
            
            st.subheader(f"📍 Travel Guide: {origin} ➔ {destination}")
            st.markdown(plan_details)
else:
    st.info("👈 Enter any two locations worldwide in the sidebar and click **Plan My Trip**!")