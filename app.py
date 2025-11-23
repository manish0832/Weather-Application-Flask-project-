from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql as sql
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random string

# 🌤 Weather Page
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        city = request.form.get("city")
        api_key = '95ab6a5efadad54952ba40bee3ea1b4a'  # Replace with your actual OpenWeatherMap API key
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'

        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            icon_code = data['weather'][0]['icon'][:2]
            icon_map = {
                "01": "wi-day-sunny", "02": "wi-day-cloudy", "03": "wi-cloud", "04": "wi-cloudy",
                "09": "wi-showers", "10": "wi-rain", "11": "wi-thunderstorm", "13": "wi-snow", "50": "wi-fog"
            }
            icon_class = icon_map.get(icon_code, "wi-day-cloudy")

            info = {
                "city": city.title(),
                "temprature": f"{data['main']['temp']} °C",
                "Feels like": f"{data['main']['feels_like']} °C",
                "Humidity": f"{data['main']['humidity']}%",
                "pressure": f"{data['main']['pressure']} hPa",
                "minimum Temprature": f"{data['main']['temp_min']} °C",
                "Maximum Temprature": f"{data['main']['temp_max']} °C",
                "icon": icon_class
            }
            return render_template("home.html", info=info)
        else:
            return render_template("home.html", message="City not found.")
    return render_template("home.html")


# 📝 Register (username + password only)
@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            return render_template("register.html", message="Passwords do not match.")

        hashed_password = generate_password_hash(password)

        # add your own root,password,host,port and database naame for sql connectivity
        try:
            conn = sql.connect(user='root', password='manish0832', host='localhost', port=3306, database='dsml8am')
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                return render_template("register.html", message="Username already exists.")
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            return redirect(url_for("login"))
        except Exception as e:
            return render_template("register.html", message=f"Database Error: {e}")
    return render_template("register.html")


# 🔐 Login Route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = sql.connect(user='root', password='manish0832', host='localhost', port=3306, database='dsml8am')
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = cur.fetchone()

            if result and check_password_hash(result[0], password):
                session['user'] = username
                return redirect(url_for("home"))
            else:
                return render_template("login.html", message="Invalid username or password.")
        except Exception as e:
            return render_template("login.html", message=f"Database Error: {e}")
    return render_template("login.html")


# 🚪 Logout
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))


# 📘 About Page
@app.route("/index")
def index():
    names = ['manish']
    return render_template("index.html", names=names)


if __name__ == "__main__":
    app.run()
