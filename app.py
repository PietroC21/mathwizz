import os
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import pyrebase
import sys
import requests
from datetime import timedelta
import secrets
from sympy import *
import latex2mathml.converter as conv
from collections.abc import MutableMapping
import re
import math as M


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
config = {
    'apiKey': os.getenv('APIKEY'),
    'authDomain': os.getenv('AUTHDOMAIN'),
    'projectId': os.getenv('PROJECTID'),
    'storageBucket':os.getenv('STORAGEBUCKET'),
    'messagingSenderId': os.getenv('MESSAGINGSENDERID'),
    'appId': os.getenv('APPID'),
    'measurementId': os.getenv('MEASUREMENTID'),
    'databaseURL': os.getenv('DATABASEURL'),
    'serviceAccount': os.getenv('SERVICEACCOUNT')

}
firebase = pyrebase.initialize_app(config)


# authenticate a user with their email and password
auth_pyrebase = firebase.auth()

# get the user's token and use it to access the Firebase REST API
db = firebase.database()
user_id = ""

app=Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = os.getenv('SECRETKEY')
app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    return render_template("signup.html")
    
@app.route("/registeruser", methods=['POST'])
def registeruser():
    if request.method == 'POST':  
        try:        
            Username=request.form['Username']
            FirstName=request.form['FirstName']
            LastName=request.form['LastName']
            Password=request.form['Password']
            Email=request.form['Email']
            Age=request.form['Age']
            Role=request.form['Role']
            user=auth_pyrebase.create_user_with_email_and_password(Email, Password)
            user_id = ""
            data = {"Username" : Username ,"FirstName": FirstName , "LastName": LastName,  "Email": Email, "Age": Age } 
            data2 = {"P1": "" , "P2": "" , "P3": "", "P4": "", "P5": ""}
            db.child(Role).push(data)

            user_data = db.child(Role).get()
            for user in user_data.each():
                if  user.val().get("Email") == Email:
                    user_id = user.key()
            db.child("Problems").child(user_id).push(data2)
            return redirect("/")
        except:
            flash('User already exists.')
            return redirect('/signup')


@app.route('/')
def home(methods=['GET', 'POST']):
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("signin.html")

@app.route("/loginuser", methods=['POST'])
def loginuser():
    if request.method == 'POST':
        email=request.form['email']

        password=request.form['password']
        try:
            user=auth_pyrebase.sign_in_with_email_and_password(email, password)
            session.permanent = True
            session['email'] = email
            session['logged_in'] = True

            user_data = db.child("PremiumUser").get()
            for user in user_data.each():
                if  user.val().get("Email") == session['email']:
                    session['user_type'] = 'Premium'
                    return redirect('/')

            session['user_type'] = 'regular'
            return redirect('/')
        except:
            flash('User does not Exist')
            return redirect('/login')
            

@app.route('/logout')
def logout():
    session.pop('email', None)
    session['logged_in'] = False
    return redirect("/")


@app.route('/calculus')
def calculus():
    return render_template('calculus.html')

@app.route('/calculus/integration')
def integral_problem():
    return render_template('integrate.html')


@app.route('/calculus/solveddefiniteintegral', methods=['POST'])
def definiteintegral():
    if request.method == 'POST':
        try:
            integral = request.form['expression']
            lowerbound = request.form['lower']
            upperbound = request.form['upper']
            integral=integral.replace("e^(", "exp(")
            for i in range(0, len(integral), 1):
                if (integral[i].isnumeric() and i!=len(integral)-1):
                    if (integral[i+1].isalpha() == True and integral[i+1].isnumeric() == False):
                        integral=integral[:i+1] +'*'+ integral[i+1:]
            x=symbols('x')
            result = integrate(integral, (x, lowerbound, upperbound))
            num, denom = fraction(result)
            num=str(num)
            denom=str(denom)
            num=num.replace("exp(", "e^(")
            denom=denom.replace("exp(", "e^(")
            results_string = ""
            user_id = ""
            if (denom!='1'):
                results_string = "("+num+")" + "/" + "(" + denom + ")"
                results_string =  latex(sympify(results_string))
                results_string = conv.convert(results_string)
            else:
                results_string = "("+str(num)+")" 
                results_string =  latex(sympify(results_string))
                results_string = conv.convert(results_string)

            user_data = db.child("PremiumUser").get()
            for user in user_data.each():
                if  user.val().get("Email") == session['email']:
                    user_id = user.key()
            db.child("Problems").child(user_id).update({"P1" : results_string})

            return render_template("solvedintegral.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedintegral.html", result=results_string, error=e)

@app.route('/calculus/solveintegral', methods = ['POST'])
def solveintegral():
    if request.method == 'POST':
        try:
            integral = request.form['expression']
            integral=integral.replace("e^(", "exp(")
            print(integral)
            integral=integral.replace("^", "**")
            for i in range(0, len(integral), 1):
                if (integral[i].isnumeric() and i!=len(integral)-1):
                    if (integral[i+1].isalpha() == True and integral[i+1].isnumeric() == False):
                        integral=integral[:i+1] +'*'+ integral[i+1:]
            x=symbols('x')
            result = integrate(integral, x)
            num, denom = fraction(result)
            num=str(num)
            denom=str(denom)
            num=num.replace("exp(", "e^(")
            denom=denom.replace("exp(", "e^(")
            print("numerator", num)
            print("denominator", denom)
            results_string = ""
            if (denom!='1'):
                results_string = "("+num+")" + "/" + "(" + denom + ")" +  "+C"
                results_string =  latex(sympify(results_string))
                results_string = conv.convert(results_string)
            else:
                results_string = "("+str(num)+")" + "+C"
                results_string =  latex(sympify(results_string))
                results_string = conv.convert(results_string)
            return render_template("solvedintegral.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedintegral.html", result=results_string, error=e)


@app.route('/calculus/differentiation')
def derviative_problem():
    return render_template("differentiate.html")

@app.route('/calculus/solvederivative', methods=['POST'])
def solvederivative():
    if request.method == 'POST':
        try:
            derivative = request.form['expression']
            derivative = derivative.replace("e^(", "exp(")
            derivative = derivative.replace("^", "**")
            for i in range(0, len(derivative), 1):
                if (derivative[i].isnumeric() and i!=len(derivative)-1):
                    if (derivative[i+1].isalpha() == True and derivative[i+1].isnumeric() == False):
                        derivative=derivative[:i+1] +'*'+ derivative[i+1:]
            x=symbols('x')
            result = diff(derivative, x)
            num, denom = fraction(result)
            num=str(num)
            denom=str(denom)
            num=num.replace("exp(", "e^(")
            denom=denom.replace("exp(", "e^(")
            print("numerator", num)
            print("denominator", denom)
            results_string = ""
            if (denom!='1'):
                results_string = "("+str(num)+")" + "/" + "(" + str(denom) + ")"
                results_string =  latex(sympify(results_string))
                results_string = conv.convert(results_string)               
            else:
                results_string = "("+str(num)+")"
                results_string =  latex(sympify(results_string))
                results_string = conv.convert(results_string)
                db.child("PremiumUser").child(user_id).update({"P1": results_string  })

            return render_template("solvedderivative.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedderivative.html", result=results_string, error=e)
            
@app.route('/algebra')
def algebra():
    return render_template('algebra.html')

@app.route('/algebra/sysequation')
def sysequation_problem():
    return render_template("sysequation.html")

@app.route('/algebra/solvesysequation', methods = ['POST'])
def solveysequation():
    if request.method == 'POST':
        results_string = ""
        try:
            a = int(request.form['aval'])
            b = int(request.form['bval'])
            c = int(request.form['cval'])
            a2 = int(request.form['a2val'])
            b2 = int(request.form['b2val'])
            c2 = int(request.form['c2val'])
            coeficients = np.array([[a, b], [a2, b2]])
            constants = np.array([c, c2])
            solutions = np.linalg.inv(coeficients).dot(constants)
            results_string = "x = " + str(round(solutions[0],2)) + ", y = " + str(round(solutions[1],2))
            return render_template("solvedquadratic.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedquadratic.html", result=results_string, error=e)

@app.route('/algebra/quadratic')
def quadratic_problem():
    return render_template("quadratic.html")

@app.route('/algebra/solvequadratic', methods = ['POST'])
def solvequadratic():
    if request.method == 'POST':
        results_string = ""
        try:
            a = int(request.form['aval'])
            b = int(request.form['bval'])
            c = int(request.form['cval'])
            tempval = sqrt((b**2)-(4*a*c))
            answer1 = ((-1*b) + tempval)/(2*a)
            print(answer1)
            answer2 = ((-1*b) - tempval)/(2*a)
            print(answer2)
            results_string = "x = " + str(answer1) + ", " + str(answer2)
            return render_template("solvedquadratic.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedquadratic.html", result=results_string, error=e)


@app.route('/geometry')
def geometry():
    return render_template('geometry.html')

@app.route('/geometry/area')
def area():
    return render_template('area.html')

@app.route('/geometry/area/circle')
def circle():
    return render_template('circle.html')

@app.route('/geometry/area/solvecircle', methods=['POST'])
def solvecircle():
    if request.method == 'POST':
        Radius = request.form['radius']
        Radius = float(Radius)
        area = M.pi * Radius * Radius
        print(area)
        return render_template('solvecircle.html', area=area)

@app.route('/geometry/area/rectangle')
def rectangle():
    return render_template('rectangle.html')

@app.route('/geometry/area/solverectangle', methods=['POST'])
def solverectangle():
    if request.method == 'POST':
        length = float(request.form['length'])
        width = float(request.form['width'])
        area = length * width
        return render_template('solverectangle.html', area=area)

@app.route('/geometry/area/triangle')
def triangle():
    return render_template('triangle.html')

@app.route('/geometry/area/solvetriangle', methods=['POST'])
def solvetriangle():
    if request.method == 'POST':
        height = float(request.form['height'])
        base = float(request.form['base'])
        area = height * base
        area = area /2
        return render_template('solvetriangle.html', area=area)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")