from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecret")

# --- Database Connection (Railway Compatible) ---
def get_db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.Cursor
    )

# ---------------- WEATHER HOME ----------------
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        city = request.form.get("city")
        api_key = os.environ.get("WEATHER_API_KEY")

        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'

        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            icon_code = data['weather'][0]['icon'][:2]

            icon_map = {
                "01": "wi-day-sunny", "02": "wi-day-cloudy",
                "03": "wi-cloud", "04": "wi-cloudy",
                "09": "wi-showers", "10": "wi-rain",
                "11": "wi-thunderstorm", "13": "wi-snow", "50": "wi-fog"
            }

            info = {
                "city": city.title(),
                "temprature": f"{data['main']['temp']} °C",
                "Feels like": f"{data['main']['feels_like']} °C",
                "Humidity": f"{data['main']['humidity']}%",
                "pressure": f"{data['main']['pressure']} hPa",
                "minimum Temprature": f"{data['main']['temp_min']} °C",
                "Maximum Temprature": f"{data['main']['temp_max']} °C",
                "icon": icon_map.get(icon_code, "wi-day-cloudy")
            }
            return render_template("home.html", info=info)
        else:
            return render_template("home.html", message="City not found.")
    return render_template("home.html")


# ---------------- SIGNUP ----------------
@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            return render_template("register.html", message="Passwords do not match.")

        hashed = generate_password_hash(password)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                return render_template("register.html", message="Username already exists.")

            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))

        except Exception as e:
            return render_template("register.html", message=f"DB Error: {e}")

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username=%s", (username,))
            row = cur.fetchone()

            if row and check_password_hash(row[0], password):
                session['user'] = username
                return redirect(url_for("home"))
            else:
                return render_template("login.html", message="Invalid username or password.")

        except Exception as e:
            return render_template("login.html", message=f"DB Error: {e}")

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))


# ---------------- INDEX ----------------
@app.route("/index")
def index():
    return render_template("index.html")
