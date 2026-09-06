import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Yatra AI - Smart Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Header Section
st.title("✈️ Yatra AI - Smart Travel & Tourism Planner")
st.markdown("Discover the best tourist spots, routes, and itineraries between any two destinations!")

st.divider()

# Search Inputs
st.sidebar.header("🔍 Search Travel Route")
origin = st.sidebar.text_input("Source Location (Kahan se?):", "Delhi")
destination = st.sidebar.text_input("Destination Location (Kahan tak?):", "Agra")
travel_type = st.sidebar.selectbox("Travel Preference:", ["All", "Historical", "Nature", "Adventure", "Food & Cultural"])
search_btn = st.sidebar.button("🔎 Search Tourist Destinations")

# Display Results upon Search
if search_btn or origin:
    st.subheader(f"📍 Exploring Options from **{origin}** to **{destination}**")
    
    # Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Top Attractions", "🗺️ Suggested Itinerary", "🚗 How to Reach", "💡 Travel Tips"])

    with tab1:
        st.markdown(f"### 🌟 Popular Tourist Spots in & around {destination}")
        
        # Sample Data (Can be linked with Gemini API / Google Places API)
        places_data = [
            {"Spot Name": "Taj Mahal", "Category": "Historical", "Best Time": "Sunrise / Sunset", "Est. Time Needed": "2-3 Hours"},
            {"Spot Name": "Agra Fort", "Category": "Historical", "Best Time": "Morning", "Est. Time Needed": "2 Hours"},
            {"Spot Name": "Mehtab Bagh", "Category": "Nature / Viewpoint", "Best Time": "Evening", "Est. Time Needed": "1 Hour"},
            {"Spot Name": "Fatehpur Sikri", "Category": "Historical", "Best Time": "Afternoon", "Est. Time Needed": "3 Hours"},
            {"Spot Name": "Sadak Bazaar", "Category": "Food & Cultural", "Best Time": "Evening", "Est. Time Needed": "2 Hours"}
        ]
        
        df = pd.DataFrame(places_data)
        
        if travel_type != "All":
            df = df[df["Category"] == travel_type]
            
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.markdown(f"### 📅 Recommended 2-Day Itinerary for {destination}")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(" Day 1: Heritage & Views")
            st.write("• **Morning:** Arrive at destination & Check-in.")
            st.write("• **10:00 AM:** Visit the main monument/attraction.")
            st.write("• **01:30 PM:** Enjoy authentic local cuisine for lunch.")
            st.write("• **05:00 PM:** Sunset view at popular local viewpoint.")
            
        with col2:
            st.info(" Day 2: Culture & Shopping")
            st.write("• **09:00 AM:** Explore nearby historical markets or secondary spots.")
            st.write("• **01:00 PM:** Street food walk & souvenir shopping.")
            st.write("• **04:00 PM:** Departure back to source location.")

    with tab3:
        st.markdown(f"### 🚌 Travel Options from {origin} to {destination}")
        col_bus, col_train, col_flight = st.columns(3)
        
        with col_bus:
            st.metric(label="🚌 Bus / Road", value="3-4 Hours", delta="Budget Friendly")
            st.write("Expressways available. Regular Volvo & State buses run daily.")
            
        with col_train:
            st.metric(label="🚆 Train", value="2 Hours", delta="Fastest")
            st.write("Multiple express trains connected directly between stations.")
            
        with col_flight:
            st.metric(label="✈️ Flight", value="Direct / Connecting", delta="Convenient")
            st.write("Check nearest airport connectivity for long distances.")

    with tab4:
        st.markdown("### 🎒 Smart Travel Advice")
        st.success("✔ **Best Season:** October to March is ideal for comfortable sightseeing.")
        st.warning("⚡ **Pre-booking:** Book tickets for major monuments online in advance to avoid queues.")
        st.error("🚨 **Local Tip:** Keep local currency/cash handy for local transport and street food.")

st.divider()
st.caption("Powered by Yatra AI • Built with Streamlit")