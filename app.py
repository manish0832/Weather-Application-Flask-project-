from datetime import datetime
import os

import pymysql
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecret")

OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5"

ICON_MAP = {
    "01": "wi-day-sunny",
    "02": "wi-day-cloudy",
    "03": "wi-cloud",
    "04": "wi-cloudy",
    "09": "wi-showers",
    "10": "wi-rain",
    "11": "wi-thunderstorm",
    "13": "wi-snow",
    "50": "wi-fog",
}


def get_db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.Cursor,
    )


def get_api_key():
    return os.environ.get("WEATHER_API_KEY")


def get_weather_icon(icon_code):
    return ICON_MAP.get(icon_code[:2], "wi-day-cloudy")


def format_temp(value):
    return f"{round(value)} C"


def format_time(timestamp, timezone_offset):
    return datetime.utcfromtimestamp(timestamp + timezone_offset).strftime("%I:%M %p")


def add_recent_search(city_name):
    recent = session.get("recent_searches", [])
    cleaned = [item for item in recent if item.lower() != city_name.lower()]
    cleaned.insert(0, city_name)
    session["recent_searches"] = cleaned[:6]
    session.modified = True


def build_weather_dashboard(city=None, lat=None, lon=None):
    api_key = get_api_key()
    if not api_key:
        return None, "Missing WEATHER_API_KEY environment variable."

    params = {"appid": api_key, "units": "metric"}
    if city:
        params["q"] = city
    else:
        params["lat"] = lat
        params["lon"] = lon

    weather_response = requests.get(f"{OPENWEATHER_BASE}/weather", params=params, timeout=10)
    if weather_response.status_code != 200:
        return None, "We could not find weather for that location."

    weather_data = weather_response.json()
    coord = weather_data.get("coord", {})

    forecast_params = {
        "lat": coord.get("lat"),
        "lon": coord.get("lon"),
        "appid": api_key,
        "units": "metric",
    }
    forecast_response = requests.get(f"{OPENWEATHER_BASE}/forecast", params=forecast_params, timeout=10)
    forecast_data = forecast_response.json() if forecast_response.status_code == 200 else {"list": []}

    timezone_offset = weather_data.get("timezone", 0)
    weather = weather_data["weather"][0]
    main = weather_data["main"]
    wind = weather_data.get("wind", {})
    sys = weather_data.get("sys", {})

    forecast_cards = []
    seen_days = set()
    for item in forecast_data.get("list", []):
        day_key = datetime.utcfromtimestamp(item["dt"] + timezone_offset).strftime("%Y-%m-%d")
        hour_key = datetime.utcfromtimestamp(item["dt"] + timezone_offset).strftime("%H:%M")
        if day_key in seen_days or hour_key not in {"12:00", "15:00"}:
            continue
        seen_days.add(day_key)
        forecast_cards.append(
            {
                "day": datetime.utcfromtimestamp(item["dt"] + timezone_offset).strftime("%a"),
                "date": datetime.utcfromtimestamp(item["dt"] + timezone_offset).strftime("%d %b"),
                "temp": format_temp(item["main"]["temp"]),
                "description": item["weather"][0]["description"].title(),
                "icon": get_weather_icon(item["weather"][0]["icon"]),
            }
        )
        if len(forecast_cards) == 5:
            break

    dashboard = {
        "location": f"{weather_data.get('name', 'Unknown')}, {sys.get('country', '')}".strip(", "),
        "condition": weather["description"].title(),
        "icon": get_weather_icon(weather["icon"]),
        "temperature": format_temp(main["temp"]),
        "feels_like": format_temp(main["feels_like"]),
        "high": format_temp(main["temp_max"]),
        "low": format_temp(main["temp_min"]),
        "humidity": f"{main['humidity']}%",
        "pressure": f"{main['pressure']} hPa",
        "visibility": f"{round(weather_data.get('visibility', 0) / 1000, 1)} km",
        "wind_speed": f"{wind.get('speed', 0)} m/s",
        "sunrise": format_time(sys.get("sunrise", 0), timezone_offset),
        "sunset": format_time(sys.get("sunset", 0), timezone_offset),
        "cloudiness": f"{weather_data.get('clouds', {}).get('all', 0)}%",
        "forecast": forecast_cards,
        "highlights": [
            {"label": "Feels like", "value": format_temp(main["feels_like"]), "icon": "fa-solid fa-temperature-three-quarters"},
            {"label": "Humidity", "value": f"{main['humidity']}%", "icon": "fa-solid fa-droplet"},
            {"label": "Wind", "value": f"{wind.get('speed', 0)} m/s", "icon": "fa-solid fa-wind"},
            {"label": "Visibility", "value": f"{round(weather_data.get('visibility', 0) / 1000, 1)} km", "icon": "fa-regular fa-eye"},
            {"label": "Pressure", "value": f"{main['pressure']} hPa", "icon": "fa-solid fa-gauge-high"},
            {"label": "Cloud cover", "value": f"{weather_data.get('clouds', {}).get('all', 0)}%", "icon": "fa-solid fa-cloud"},
        ],
    }

    add_recent_search(weather_data.get("name", city or "Current Location"))
    return dashboard, None


@app.route("/home", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    dashboard = None
    message = None
    city_query = ""

    if request.method == "POST":
        city_query = (request.form.get("city") or "").strip()
        if not city_query:
            message = "Enter a city name to load the dashboard."
        else:
            dashboard, message = build_weather_dashboard(city=city_query)
    elif request.args.get("city"):
        city_query = request.args.get("city", "").strip()
        dashboard, message = build_weather_dashboard(city=city_query)

    return render_template(
        "home.html",
        dashboard=dashboard,
        message=message,
        city_query=city_query,
        recent_searches=session.get("recent_searches", []),
    )


@app.route("/weather/current-location")
def weather_current_location():
    if "user" not in session:
        return redirect(url_for("login"))

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:
        return redirect(url_for("home"))

    dashboard, message = build_weather_dashboard(lat=lat, lon=lon)
    return render_template(
        "home.html",
        dashboard=dashboard,
        message=message,
        city_query="",
        recent_searches=session.get("recent_searches", []),
    )


@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not username or not password:
            return render_template("register.html", message="Username and password are required.")

        if password != confirm:
            return render_template("register.html", message="Passwords do not match.")

        hashed = generate_password_hash(password)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                conn.close()
                return render_template("register.html", message="Username already exists.")

            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except Exception as exc:
            return render_template("register.html", message=f"DB Error: {exc}")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password")

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username=%s", (username,))
            row = cur.fetchone()
            conn.close()

            if row and check_password_hash(row[0], password):
                session["user"] = username
                return redirect(url_for("home"))
            return render_template("login.html", message="Invalid username or password.")
        except Exception as exc:
            return render_template("login.html", message=f"DB Error: {exc}")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/index")
def index():
    features = [
        "Smart weather dashboard with current conditions and trend cards",
        "Five-day forecast preview with quick city recall",
        "Location-based lookup from the browser for instant nearby weather",
        "Responsive SaaS-style experience with persistent light and dark themes",
    ]
    return render_template("index.html", features=features)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
