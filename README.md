# 🧭 YatraAI — AI Smart Tourism & Travel Companion

**One map. Every journey.**

YatraAI is a hackathon-ready Streamlit app that combines maps, nearby tourism places, hotels, restaurants, emergency services, weather, budget planning, and Google Gemini AI itinerary/chat.

## Features

- 🗺️ Interactive tourism map
- 📍 Destination search/geocoding
- 🏛️ Nearby tourist & historic places
- 🏨 Nearby hotels
- 🍽️ Restaurants & cafes
- 🚑 Hospitals, police & fire stations
- 📏 Distance from selected destination
- 🧭 Google Maps directions
- 🌤️ Live weather from Open-Meteo
- 💰 Budget planner
- ⏱️ Time-based trip planning
- 🤖 Gemini AI itinerary
- 💬 Gemini AI tourism chatbot
- 📱 Responsive Streamlit UI

## Run locally

### 1. Install Python

Python 3.10+ is recommended.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Gemini API key

Copy `.env.example` to `.env` and add your key.

For local testing, you can also set the environment variable directly.

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
streamlit run app.py
```

### 4. Start the app

```bash
streamlit run app.py
```

The terminal will show a local address such as:

```text
http://localhost:8501
```

## GitHub upload

Create a new GitHub repository, for example:

```text
yatra-ai
```

Upload:

```text
app.py
requirements.txt
.env.example
.gitignore
README.md
```

**Never upload your real `.env` or Gemini API key.**

## Deploy on Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Sign in with GitHub.
3. Click **Create app**.
4. Select your GitHub repository.
5. Branch: `main`
6. Main file: `app.py`
7. Click **Deploy**.
8. Open **Settings → Secrets** and add:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-3.8-flash"
```

After deployment, Streamlit will give you a public URL similar to:

```text
https://your-app-name.streamlit.app
```

Use that URL for your hackathon live demo.

## Data/API notes

YatraAI uses public services for the demo:

- OpenStreetMap Nominatim — geocoding
- Overpass API — nearby OpenStreetMap places
- Open-Meteo — weather
- Google Maps — directions
- Google Gemini API — AI

Public APIs can have rate limits. For a hackathon demo, keep requests reasonable.

## Troubleshooting

### Gemini error

Check that `GEMINI_API_KEY` is correctly configured in Streamlit Secrets and that the selected model is available to your API key/project.

You can change the model using:

```toml
GEMINI_MODEL = "your-available-model"
```

### No places found

Try increasing the **Search radius** or use a more specific city/destination.

### App is slow

Public geocoding/Overpass services may be temporarily slow. The app caches some API results to reduce repeated requests.
