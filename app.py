from flask import Flask
app=Flask(__name__)
# __name__ is a built in python variable that holds the name if the current module
@app.route("/")
def hello():
    return "<h1>Hello world! </h1>"

@app.route("/Home")
def home():
    return "This is our home page"
@app.route("/hello")
def hello_world():
    return "<p>manish saini world! </p>"
@app.route("/Hii")
def Hii():
    print("This is our home page")
    
    

# dynamic url....
# string ---><str> ----> ex --> <username>   
# int --><int: value>.  <int : age>
# float --›‹float: value >
@app.route('/home/<user>')    
def dynamic_home(user):
    return f"<h1> hello {user} how are you </h1>"
@app.route('/home/<user>/<int:age>')    
def dynamic_home1(user,age):
    return f"<h1> hello {user} your age is {age}  </h1>"    
@app.route("/home/<user>/<int:m1>/<int:m2>/<int:m3>")
def percentage(user,m1,m2,m3):
   
    if m1<=100 and m2<=100 and m3<=100:
        percent=(m1+m2+m3)/3
        if percent>90 and percent <=100:
            grade='A' 
        elif percent>80 and percent<=90:
            grade='B'
        elif percent>60 and percent<=80: 
            grade='C'
        elif percent>=40 and percent<=60: 
            grade='D'
        else: 
            grade='Fail'       
        return f"<h1 style='color:green'> hey {user} your percent is {percent}% and your grade is {grade}</h1>"
    return "Please enter valid marks"
app.run(host="localhost",port=5001, debug=True)
# host ----> ip adress
# port ----> The port number where the application is run
# debug ----> True -> the error show on the web page  ---> development mode.
# debug ----> False -->the error show on the console --> deployment mode

