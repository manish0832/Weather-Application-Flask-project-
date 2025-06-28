from flask import Flask, render_template,request,jsonify,redirect,url_for
import pymysql  as sql
import requests

app=Flask(__name__)
"""@app.route('/')
def index():
    lis=[21,32,4,24,34,23,43,55]
    return f'manish saini {lis}'
"""
@app.route('/home',methods=['GET','POST'])
def home():
    if request.method=="POST":
        city=request.form.get("city")
        api_key = '95ab6a5efadad54952ba40bee3ea1b4a'
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            
            temp = data['main']['temp']
            feels = data['main']['feels_like']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            min_temp = data['main']['temp_min']
            max_temp = data['main']['temp_max']

            info={
                "city": city,
                "temprature" : temp,
                "Feels like" : feels,
                "Humidity" : humidity,
                "pressure" : pressure,
                "minimum Temprature" : min_temp,
                "Maximum Temprature" : max_temp
            }
            return render_template("home.html", info=info)
        else:
            message= "city not found"
            return render_template("home.html", message=message)
            
 
        
        
    return render_template("home.html")
@app.route('/',methods=["GET","POST"])
def signup():
    if request.method=="POST":
        user=request.form.get("username")
        password=request.form.get("password")
        try:
            conn=sql.connect(user='root',password='manish0832',host='localhost',port=3306,database='dsml8am')
            cur=conn.cursor()
            cur.execute("insert into users(username,password) VALUES (%s,%s)",(user,password ))
            conn.commit()
            return redirect(url_for("login"))
        except Exception as e:
            print("error --->", e)    
            return render_template("register.html",e=e)
        else:
            print("log in successfull ")
            return redirect(url_for("login"))
    return render_template("register.html")        
       
    
@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        user=request.form.get("username")
        password=request.form.get("password")
        try:
            conn=sql.connect(user='root',password='manish0832',host='localhost',port=3306,database='dsml8am')
            cur=conn.cursor()
            cur.execute("select * from users where username = %s and password= %s",(user,password ))
            data=cur.fetchone()
            if data:
                return redirect(url_for("home"))
            else:
                message = "invalid username or password"
                return render_template("login.html",message=message)
        except Exception as message:
            return render_template("login.html",message=message)
              
    return render_template('login.html')        
    

    
            
            

       
       
@app.route("/index")
def index():
    names=['manish','rahul','sachin','sunil','vijesh','somil'] 
    return render_template("index.html",names=names)           


if __name__=='__main__':
    app.run(host='localhost',port=5001,debug=True)