import os
import requests
import json
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, flash, send_from_directory
from collections.abc import MutableMapping
import pyrebase
import sys
from datetime import timedelta
import secrets
from sympy import *
import latex2mathml.converter as conv
import re
import math as M
import numpy as np
from flask_wtf.csrf import CSRFProtect
import firebase_admin
from firebase_admin import credentials, auth
import time

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
cred = credentials.Certificate("mathwiz-759df-firebase-adminsdk-aoe28-bf1fa44c3a.json")
firebase_admin.initialize_app(cred)
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
app.permanent_session_lifetime = timedelta(minutes=60)
csrf = CSRFProtect(app)



@app.before_request
def clear_messages():
    session.pop('_flashes', [])

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
            auth.set_custom_user_claims(user['localId'], {Role : True})
            data = {"Username" : Username ,"FirstName": FirstName , "LastName": LastName,  "Email": Email, "Age": Age } 
            db.child("Users").push(data)
            session['email'] = Email
            session['localId'] = user['localId']
            session['idToken'] = user['idToken']
            user_data = db.child("Users").get()
            user_id = 0
            for user in user_data.each():
                if  user.val().get("Email") == session['email']:
                    user_id = user.key()
            session['user_id'] = user_id
            return redirect("/")
        except:
            flash("Email already exists", "danger")
            return render_template("signup.html")

@app.route('/')
def home(methods=['GET', 'POST']):
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("signin.html")

@app.route("/loginuser", methods=['POST'])
def loginuser():
    if request.method == 'POST':
        try:
            email=request.form['email']
            password=request.form['password']
            user=auth_pyrebase.sign_in_with_email_and_password(email, password)
            token = user['idToken']
            session.permanent = True
            session['email'] = email
            session['logged_in'] = True
            session['localId'] = user['localId']
            session['idToken'] = token
            user_data = db.child("Users").get()
            for user in user_data.each():
                if user.val().get("Email") == session['email']:
                    user_id = user.key()
            session['user_id'] = user_id
            return redirect('/')
        except requests.exceptions.HTTPError as e:
            error_json = e.args[1]
            error = json.loads(error_json)['error']['message']
            if error == "INVALID_PASSWORD":
                # The password is invalid
                flash("Invalid password")
                return render_template("signin.html")
            elif error == "EMAIL_NOT_FOUND":
                # The email is not registered
                flash("Email not registered")
                return render_template("signin.html")
            else:
                # Some other error occurred
                flash("Unknown error:")
                return render_template("signin.html")



@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('localId', None)
    session.pop('idToken', None)
    session['logged_in'] = False
    return redirect("/")

@app.route('/calculus')
def calculus():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('User') is True):
        flash("You do not have access to this page, upgrade to premium to access this page")
        return render_template('index.html')
    return render_template('calculus.html')

@app.route('/calculus/integration')
def integral_problem():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('User') is True):
        return redirect('/')
    return render_template('integrate.html')

@app.route('/calculus/indefiniteintegral')
def indefinte_integral():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('User') is True):
        return redirect('/')
    return render_template('indefiniteintegrate.html')

@app.route('/calculus/definiteintegral')
def definiteintegral_render():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('User') is True):
        return redirect('/')
    return render_template('definiteintegral.html')

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
                results_string =   "("+num+")" + "/" + "(" + denom + ")" 
                results_string = '\int ' + latex(sympify(integral)) + 'dx = ' + latex(sympify(results_string))
                results_string = conv.convert(results_string)
            else:
                results_string =   "("+str(num)+")" 
                results_string = '\int ' + latex(sympify(integral)) + 'dx = ' + latex(sympify(results_string))
                results_string = conv.convert(results_string)
            db.child('Users').child(session['user_id']).child('Problems').push({"Calculus" : results_string  })

            return render_template("solvedintegral.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedintegral.html", result=results_string, error=e)

@app.route('/calculus/solveintegral', methods = ['POST'])
def solveintegral():
    if request.method == 'POST':
        results_string = ""
        try:
            integral = request.form['expression']
            integral=integral.replace("e^(", "exp(")
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
            results_string = ""
            if (denom!='1'):
                results_string =   "("+num+")" + "/" + "(" + denom + ")" 
                results_string = '\int ' + latex(sympify(integral)) + 'dx = ' + latex(sympify(results_string)) + "+C"
                results_string = conv.convert(results_string)
            else:
                results_string =   "("+str(num)+")" 
                results_string = '\int ' + latex(sympify(integral)) + 'dx = ' + latex(sympify(results_string)) + "+C"
                results_string = conv.convert(results_string)

            db.child('Users').child( session['user_id']).child('Problems').push({"Calculus" :   results_string   })
            return render_template("solvedintegral.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedintegral.html", result=results_string, error=e)

@app.route('/calculus/differentiation')
def derviative_problem():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('User') is True):
        return redirect('/')
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
            results_string = ""
            if (denom!='1'):
                results_string = "("+str(num)+")" + "/" + "(" + str(denom) + ")"
                results_string ='\\frac{d}{dx}  ' + latex(sympify(derivative)) + ' = ' + latex(sympify(results_string))            
                results_string = conv.convert(results_string)   
            else:
                results_string = "("+str(num)+")"
                results_string ='\\frac{d}{dx}  ' + latex(sympify(derivative)) + ' = ' + latex(sympify(results_string))            
                results_string = conv.convert(results_string) 

            db.child('Users').child( session['user_id']).child('Problems').push({"Calculus" :  results_string   })

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
            matrix =0
    
            if np.linalg.det(coeficients)!=0:
                solutions =np.dot( np.linalg.inv(coeficients),constants )
                results_string = " -> x = " + str(round(solutions[0],2)) + ", y = " + str(round(solutions[1],2))
                system1 = str(a) + "x + " + str(b) + "y " + ' = ' + str(c) + " , " + str(a2) + "x + " + str(b2) + "y =  " + str(c2)+ " "
                results_string = system1 + results_string
                results_string = conv.convert(results_string)
                db.child('Users').child( session['user_id']).child('Problems').push({"Algebra" :  results_string   })
                return render_template("solvedsysequation.html", result=results_string, error=None)

            
            #if the determinant is 0 that means there is no solution or infinite solutions
            else:
                matrix = np.concatenate((coeficients, np.reshape(constants, (-1, 1))), axis=1)
                M = Matrix(matrix)
                M = M.rref()
                solutions = M[1]
                if len(solutions) == 1:
                    system1 = str(a) + "x + " + str(b) + "y "
                    system2 = ", " + str(a2) + "x + " + str(b2) + "y = " + str(c2)
                    results_string = "System has Infinite Solutions"
                    results_string = (system1) + " = " +str(c) + ((system2)) + ' = ' + str(c2) +'\n ->'+ latex((results_string))
                    results_string = conv.convert(results_string) 
                    db.child('Users').child( session['user_id']).child('Problems').push({"Algebra" : results_string })
                    return render_template("solvedsysequation.html", result=results_string)  

                elif len(solutions) == 2:
                    system1 = str(a) + "x + " + str(b) + "y "
                    system2 = ", " + str(a2) + "x + " + str(b2) + "y = " + str(c2)
                    system1 =  ((system1))
                    results_string = "System has No Solutions"
                    results_string = (system1) + " = " +str(c) + ((system2)) + ' = ' + str(c2) +' -> '+  latex(results_string)
                    results_string =  ((results_string))
                    results_string = conv.convert(results_string)                    
                    db.child('Users').child( session['user_id']).child('Problems').push({"Algebra" : results_string})
                    return render_template("solvedsysequation.html", result=results_string)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedsysequation.html", result=results_string, error=e)


@app.route('/algebra/quadratic')
def quadratic_problem():
    return render_template("quadratic.html")

@app.route('/algebra/solvequadratic', methods = ['POST'])
def solvequadratic():
     if request.method == 'POST':
        results_string = ""
        try:
            a = str(request.form['aval'])
            if a.find('.'):
                a = float(a)
            else:
                a = int(a)
            b = str(request.form['bval'])
            if b.find('.'):
                b = float(b)
            else:
                b = int(b)
            c = str(request.form['cval'])
            if c.find('.'):
                c = float(c)
            else:
                c = int(c)    
            tempval = sqrt((b**2)-(4*a*c))
            answer1 = ((-1*b) + tempval)/(2*a)
            answer2 = ((-1*b) - tempval)/(2*a)
            if answer1 == answer2:
                answer1 = round(answer1, 1)
                if str(answer1).find('.0')>0:
                    answer1 = int(answer1)
                results_string = "x = " + str(answer1) 
                if a==1:
                    a = "x^2 + " + str(b) + "x + " + str(c) + " = 0  => "
                else:
                    a = str(a) + "x^2 + " + str(b) + "x + " + str(c) + " = 0  => "
                results_string = a + results_string
                results_string = conv.convert(results_string)
                
            else:
                if str(answer1).find('.0') > 0:
                    answer1 = int(answer1)
                if str(answer2).find('.0') > 0:
                    answer2 = int(answer2)       
                answer1 = round(answer1, 1)
                answer2 = round(answer2, 1)
                results_string = "x = " + str(answer1) + ", " + str(answer2)   
                if a==1:
                    a = "x^2 + " + str(b) + "x + " + str(c) + " = 0  => "
                else:         
                    a = str(a) + "x^2 + " + str(b) + "x + " + str(c) + " = 0  => "
                results_string = a + results_string
                results_string = conv.convert(results_string) 
            db.child('Users').child( session['user_id']).child('Problems').push({"Algebra" : results_string})
            return render_template("solvedquadratic.html", result=results_string, error=None)
        except (ValueError, TypeError, AttributeError) as e:
            return render_template("solvedquadratic.html", result=results_string, error=e)


@app.route('/geometry')
def geometry():
    return render_template('geometry.html')

@app.route('/geometry/volume')
def volume():
    return render_template('volume.html')

@app.route('/geometry/volume/sphere')
def sphere():
    return render_template('sphere.html')

@app.route('/geometry/volume/solvesphere', methods=['POST'])
def solvesphere():
    if request.method == 'POST':
        results_string = ""
        r = float(request.form['radius'])
        u = request.form['units']
        if u == "meters":
            end = " m" + "\u00b3"
        elif u == "inches":
            end = " in" + "\u00b3"
        elif u == "centimeters":
            end = " cm" + "\u00b3"
        elif u == "yards":
            end = " yd" + "\u00b3"
        vol = 4/3*M.pi*(r**3)
        vol = round(vol, 2)
        results_string = 'V  =  ' + latex(simplify('4/3*r^3')) + ' ' + latex(simplify('pi'))  + ' = ' + str(vol) + end
        results_string = conv.convert(results_string)
        db.child('Users').child( session['user_id']).child('Problems').push({"Geometry" : results_string})
        return render_template('solvesphere.html', result = results_string)

@app.route('/geometry/volume/rectangularprism')
def rectangularprism():
    return render_template('rectangularprism.html')

@app.route('/geometry/volume/solverecprism', methods=['POST'])
def solverecprism():
    if request.method == 'POST':
        l = float(request.form['length'])
        w = float(request.form['width'])
        h = float(request.form['height'])
        u = request.form['units']
        if u == "meters":
            end = " m" + "\u00b3"
        elif u == "inches":
            end = " in" + "\u00b3"
        elif u == "centimeters":
            end = " cm" + "\u00b3"
        elif u == "yards":
            end = " yd" + "\u00b3"
        vol = l*w*h
        vol = round(vol, 2)
        results_string = 'V  =  ' +  'length*width*height'+ ' = ' + str(vol) + end
        results_string = conv.convert(results_string)
        db.child('Users').child( session['user_id']).child('Problems').push({"Geometry" : results_string})
        return render_template('solverecprism.html', result = results_string)

@app.route('/geometry/volume/cone')
def cone():
    return render_template('cone.html')

@app.route('/geometry/volume/solvecone', methods=['POST'])
def solvecone():
    if request.method == 'POST':
        r = float(request.form['radius'])
        h = float(request.form['height'])
        u = request.form['units']
        if u == "meters":
            end = " m" + "\u00b3"
        elif u == "inches":
            end = " in" + "\u00b3"
        elif u == "centimeters":
            end = " cm" + "\u00b3"
        elif u == "yards":
            end = " yd" + "\u00b3"
        vol = M.pi*(r*r)*(h/3)
        vol = round(vol, 2)
        results_string = 'V  =  ' +  latex(simplify('1/3'))+''+ latex(simplify('pi'))+' '+ latex(simplify('r^2')) + 'h'+ ' = ' + str(vol) + end
        results_string = conv.convert(results_string)
        db.child('Users').child( session['user_id']).child('Problems').push({"Geometry" : results_string})
        return render_template('solvecone.html', result = results_string)

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
        u = request.form['units']
        if u == "meters":
            end = " m" + "\u00b2"
        elif u == "inches":
            end = " in" + "\u00b2"
        elif u == "centimeters":
            end = " cm" + "\u00b2"
        elif u == "yards":
            end = " yd" + "\u00b2"
        area = M.pi * Radius * Radius
        results_string = 'A =  '+ latex(simplify('pi')) + ' ' +latex(simplify('r^2')) + ' = ' + str(area) + end
        results_string = conv.convert(results_string)
        db.child('Users').child( session['user_id']).child('Problems').push({"Geometry" : results_string})
        return render_template('solvecircle.html', result=results_string)

@app.route('/geometry/area/rectangle')
def rectangle():
    return render_template('rectangle.html')

@app.route('/geometry/area/solverectangle', methods=['POST'])
def solverectangle():
    if request.method == 'POST':
        length = float(request.form['length'])
        width = float(request.form['width'])
        u = request.form['units']
        if u == "meters":
            end = " m" + "\u00b2"
        elif u == "inches":
            end = " in" + "\u00b2"
        elif u == "centimeters":
            end = " cm" + "\u00b2"
        elif u == "yards":
            end = " yd" + "\u00b2"
        area = length * width
        results_string = 'A =  '+ latex(('length')) + ' * ' +latex((' height')) + ' = ' + str(area) + end
        results_string = conv.convert(results_string)

        db.child('Users').child( session['user_id']).child('Problems').push({"Geometry" : results_string})
        return render_template('solverectangle.html', result=results_string)

@app.route('/geometry/area/triangle')
def triangle():
    return render_template('triangle.html')

@app.route('/geometry/area/solvetriangle', methods=['POST'])
def solvetriangle():
    if request.method == 'POST':
        height = float(request.form['height'])
        base = float(request.form['base'])
        u = request.form['units']
        if u == "meters":
            end = " m" + "\u00b2"
        elif u == "inches":
            end = " in" + "\u00b2"
        elif u == "centimeters":
            end = " cm" + "\u00b2"
        elif u == "yards":
            end = " yd" + "\u00b2"
        area = height * base
        area = area /2
        results_string = 'A =  '+ latex(sympify('1/2')) + ('base * height')  + ' = ' + str(area) + end
        results_string = conv.convert(results_string)

        return render_template('solvetriangle.html', result=results_string)

@app.route('/viewprofile', methods=['POST'])
def viewprofile():
    if request.method == 'POST':
        claims = auth.verify_id_token(session['idToken'])
        email=session['email']
        users=db.child("Users").order_by_child("Email").equal_to(email).get().val()
        if (claims.get('admin') is True):
            return render_template("viewprofile.html", users=users, a='Admin')
        elif(claims.get('Premium') is True):
            return render_template('viewprofile.html', users=users, a='Premium')
        elif (claims.get('User') is True):
            return render_template('viewprofile.html', users=users, a='User')

@app.route('/editprofile')
def editprofile():
    claims = auth.verify_id_token(session['idToken'])
    ab=''
    if (claims.get('admin') is True):
        return render_template('editprofileAdmin.html', a='Admin')
    elif(claims.get('Premium') is True):
        return render_template('editprofile.html', a='Premium')
    elif(claims.get('User') is True):
        return render_template('editprofile.html', a='User')

@app.route('/modifyprofile', methods=['POST'])
def modifyprofile():
    if request.method =='POST':
        form_keys = []
        form_data = []
        for key, value in request.form.items():
            if (key not in ['csrf_token','Upgrade']):
                if (value.strip()):
                    form_keys.append(key)
                    form_data.append(value)    
        if len(form_data) == 0:
            flash('At Least one of these fields needs to have input')
            return redirect('/editprofile')
        else:
            '''
            Gets the current value of the child 
            '''
            email = session['email']
            user=db.child("Users").order_by_child("Email").equal_to(email).get().val()
            user_id = list(user.keys())[0]
            userObject = db.child("Users").child(user_id)
            user_data = user[user_id]
            email_to_modify = []
            password_to_modify = []
            for x,y in zip(form_keys, form_data):
                if (x !='Password'):
                    if (x == 'Email'):
                        email_to_modify.append(y)
                    user_data[x] = y
                else:
                    password_to_modify.append(y)
            if (len(email_to_modify) !=0):
                session['email'] = email_to_modify[0]
                user= auth.update_user(session['localId'], email=email_to_modify[0])
            if (len(password_to_modify) !=0):
                user = auth.update_user(session['localId'], password = password_to_modify[0])
            userObject.update(user_data)
            flash('Profile Modified Succesfully')
            return redirect('/')


@app.route('/upgrade', methods=['POST'])
def upgrade():
    email = session['email']
    user = auth.get_user_by_email(email)
    auth.set_custom_user_claims(user.uid, {"Premium" : True})
    return redirect('/logout')

@app.route('/deleteprofile')
def deleteprofile():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('admin') is True):
        return render_template('deleteprofile.html', a='Admin')
    elif (claims.get('Premium') is True):
        return render_template('deleteprofile.html', a='Premium')
    elif(claims.get('User') is True):
        return render_template('deleteprofile.html', a='User')

@app.route('/deleteaccount', methods=['POST'])
def deleteaccount():
    email = session['email']
    user=db.child("Users").order_by_child("Email").equal_to(email).get().val()
    user_id = list(user.keys())[0]
    user_data = user[user_id]
    auth_pyrebase.delete_user_account(session['idToken'])
    db.child("Users").child(user_id).remove()
    session.pop('email', None)
    session.pop('user_type', None)
    session.pop('localId', None)
    session.pop('idToken', None)
    session['logged_in'] = False
    return redirect('/')


@app.route('/history')
def history():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('User') is True):
        email = session['email']
        user = db.child('Users').order_by_child("Email").equal_to(email).get().val()
        user_id = list(user.keys())[0]
        user_data = user[user_id]
        try:
            history = user_data['Problems'].values()

        except:
            flash('No History')
            return render_template('history.html', a='None')
        return render_template('history.html', problems=history, a='User')
    if(claims.get('Premium') is True):
        email = session['email']
        user = db.child('Users').order_by_child("Email").equal_to(email).get().val()
        user_id = list(user.keys())[0]
        user_data = user[user_id]
        try:
            history = user_data['Problems'].values()
        except:
            flash('No History')
            return render_template('history.html', a='None')
        return render_template('history.html', problems=history, a='Premium')
    
    elif (claims.get('admin') is True):
        email = session['email']
        user = db.child('Users').order_by_child("Email").equal_to(email).get().val()
        user_id = list(user.keys())[0]
        user_data = user[user_id]
        try:
            history = user_data['Problems'].values()
        except:
            flash('No History')
            return render_template('history.html', a='None')
        return render_template('history.html', problems=history, a='admin')

@app.route('/userHistory')
def userHistory():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('admin') is True):
        users = db.child('Users').child('/').get()
        user_list = [] 
        user_name = []
        for user in users:
            cur = user.key()
            if db.child('Users').child(cur).child('Problems').get().val() is not None:
                user_name.append(db.child('Users').child(cur).child('Email').get().val())
                user_list.append( db.child("Users").child(cur).child('Problems').get().val())
        myList = []
        for  prb , name in zip(user_list,user_name):
            for key, value in prb.items():
                myList.append((name , value))
    return render_template('historyAdmin.html', problems=myList  )




@app.route('/viewallusers', methods=['POST']) 
def viewallusers():
    claims = auth.verify_id_token(session['idToken'])
    if (claims.get('admin') is True):
        users = db.child('Users').child('/').get().val()
        users_claims = []
        for user in users.items():
            user_id = user[0]
            user_data = users[user_id]
            email = user_data['Email']
            userobject = auth.get_user_by_email(email)
            users_claims.append(auth.get_user(userobject.uid).custom_claims.keys())
        '''
        return a list of claims and do a for loop for each claim and for each user value
        '''
        return render_template('viewallusers.html', users=users, list_of_claims=users_claims, zip=zip, list=list)
    else:
        return redirect('/')


@app.route('/viewauser', methods=['POST'])
def viewauser():
    email = request.form['Email']
    users=db.child("Users").order_by_child("Email").equal_to(session['email']).get().val()
    claims = auth.verify_id_token(session['idToken'])
    if len(email) == 0:
        flash('Please Enter an Email')
        return render_template('viewprofile.html', users=users, a='Admin')
    try:
        userobject = auth.get_user_by_email(email)
    except firebase_admin._auth_utils.UserNotFoundError:
        flash('User Not Found')
        if (claims.get('admin') is True):
            return render_template('viewprofile.html' ,users=users, a='Admin')
        else:
            flash('You are not an Admin')
            if (claims.get('Premium') is True):
                return render_template('viewprofile.html' ,users=users, a='Premium')
            else:
                return render_template('viewprofile.html' ,users=users, a='User')
    
    if (claims.get('admin') is False):
        flash('You are not an Admin')
        if (claims.get('Premium') is True):
            return render_template('viewprofile.html' ,users=users, a='Premium')
        else:
            return render_template('viewprofile.html' ,users=users, a='User')
    
    print(len(email))
    if len(email) == 0:
        flash('Please Enter an Email')
        return render_template('viewuser.html', users=users, a='Admin')
        
    users=db.child("Users").order_by_child("Email").equal_to(email).get().val()
    if (claims.get('admin') is True):
        usertype = auth.get_user(userobject.uid).custom_claims.keys()
        return render_template('viewaprofile.html', users=users, a=usertype, list=list)
    else:
        flash('You are not an Admin')
        return render_template('viewprofile')
    

@app.route('/modifyuser')
def modifyuser():
    return render_template('modifyauser.html')


@app.route('/changeuser', methods=['POST'])
def changeuser():
    claims = auth.verify_id_token(session['idToken'])
    if claims.get('admin') is True:
        form_keys = []
        form_data = []
        for key, value in request.form.items():
            if (key not in ['csrf_token', 'originalemail']):
                if (value.strip()):
                    form_keys.append(key)
                    form_data.append(value)    
        if len(form_data) == 0:
            flash('At Least one of these fields needs to have input')
            return redirect('/modifyuser')
        else:
            '''
            Gets the current value of the child 
            '''
            email = request.form['originalemail']
            try:
                user=db.child("Users").order_by_child("Email").equal_to(email).get().val()
                user_id = list(user.keys())[0]
                userObject = db.child("Users").child(user_id)
                user_data = user[user_id]
                email_to_modify = []
                password_to_modify = []
                for x,y in zip(form_keys, form_data):
                    if (x !='Password'):
                        if (x == 'Email'):
                            email_to_modify.append(y)
                        user_data[x] = y
                    else:
                        password_to_modify.append(y)
                if (len(email_to_modify) !=0):
                    usercredobject = auth.get_user_by_email(email)
                    user= auth.update_user(usercredobject.uid, email=email_to_modify[0])
                if (len(password_to_modify) !=0):
                    usercredobject = auth.get_user_by_email(email)
                    user = auth.update_user(usercredobject.uid, password = password_to_modify[0])
                userObject.update(user_data)
                flash('Profile Modified Succesfully')
                return redirect('/')
            except:
                flash('User Not Found')
                return render_template('modifyauser.html')
    else:
            return redirect('/')


@app.route('/downgrade', methods=['POST'])
def downgrade():
    try:
        user = auth.get_user_by_email(session['email'])
    except firebase_admin.auth.UserNotFoundError:
        flash('User Does Not Exist')
        return render_template('editprofile.html')
    claims = user.custom_claims
    if claims=={'Premium': True}:
        try:        
            users=db.child("Users").order_by_child("Email").equal_to(session['email']).get().val()
            auth.set_custom_user_claims(user.uid, {"User" : True})
            claims= auth.get_user(user.uid).custom_claims
            return redirect('/logout')
        except:
            flash('Error downgrading user')
            return render_template('editprofile.html')
    else:
        flash('User is not Premium ')
        return render_template('editprofile.html')

@app.route('/grantadmin')
def addRole():
    return render_template('grantadmin.html')

@app.route('/addAdmin', methods=['POST'])
def addAdmin():
    email = request.form['email']
    try:
        user = auth.get_user_by_email(email)
    except firebase_admin._auth_utils.UserNotFoundError:
        flash('User Does Not Exist')
        return render_template('grantadmin.html')
    
    if user.custom_claims.get('admin') is True:
        flash('User is already an Admin')
        return render_template('grantadmin.html')
    elif user.custom_claims.get('Premium') is True:
        auth.set_custom_user_claims(user.uid, {"Premium" : False})
    elif user.custom_claims.get('User') is True:
        auth.set_custom_user_claims(user.uid, {"User" : False})

    auth.set_custom_user_claims(user.uid, {"admin" : True})
    return redirect('/')
  

@app.route('/revokeadmin')
def removeRole():
    return render_template('removeadmin.html')

@app.route('/removeadmin', methods=['POST'])
def revokeAdmin():
    claims = auth.verify_id_token(session['idToken'])
    if claims.get('admin') is True:
        Role = request.form['Role']
        user = auth.get_user_by_email(session['email'])
        auth.set_custom_user_claims(user.uid, {'admin': False})
        auth.set_custom_user_claims(user.uid, {Role: True})
        flash('Admin Revoked  Succesfully')
        return redirect('/logout')
    else:
        return redirect('/')

@app.route('/deleteuser')
def deleteuser():
    return render_template('deleteuser.html')

@app.route('/deleteUser', methods=['POST'])
def deleteaUser():
    if request.method =='POST':
        try:
            claims = auth.verify_id_token(session['idToken'])
            if claims.get('admin') is True:
                email = request.form['email']
                user = auth.get_user_by_email(email)
                auth.delete_user(user.uid)
                user=db.child("Users").order_by_child("Email").equal_to(email).get().val()
                user_id = list(user.keys())[0]
                db.child("Users").child(user_id).remove()
                return redirect('/')
            else:
                return redirect('/')
        except:
            flash('User Does Not Exist')
            return redirect('/deleteuser')
       
@app.route('/upgradeuser')
def upgradeuser():
    claims = auth.verify_id_token(session['idToken'])
    if claims.get('admin') is True:
        return render_template('upgradeuser.html')
    else:
        return ('/')

@app.route('/performuserupgrade', methods=['POST'])
def performuserupgrade():
    try:
        user = auth.get_user_by_email(request.form['email'])
    except firebase_admin.auth.UserNotFoundError:
        flash('User Does Not Exist')
        return render_template('upgradeuser.html')
    
    claims = user.custom_claims
    if claims=={'User': True}:
        try:        
            users=db.child("Users").order_by_child("Email").equal_to(request.form['email']).get().val()
            auth.set_custom_user_claims(user.uid, {"Premium" : True})
            claims= auth.get_user(user.uid).custom_claims
            return render_template('upgradeduser.html',users=users, a='Premium')
        except:
            flash('Error upgrading user')
            return render_template('upgradeuser.html')
    else:
        flash('User is not non-Premium ')
        return render_template('upgradeuser.html' )

@app.route('/downgradeuser')
def downgradeuser():
    claims = auth.verify_id_token(session['idToken'])
    if claims.get('admin') is True:
        return render_template('downgradeuser.html')
    else:
        return ('/')

@app.route('/performuserdowngrade', methods=['POST'])
def performuserdowngrade():
    email = request.form['email']
    try:
        user = auth.get_user_by_email(email)
    except:
        flash('User Does Not Exist')
        return render_template('downgradeuser.html')
    
    if user.custom_claims.get('Premium') is True:
        auth.set_custom_user_claims(user.uid, {"Premium" : False})
    elif user.custom_claims.get('User') is True:
        flash('User is  already a Non-Premium User')
        return render_template('downgradeuser.html')
    
    elif user.custom_claims.get('admin') is True:
        flash('User is an Admin')
        return render_template('downgradeuser.html')
    
    auth.set_custom_user_claims(user.uid, {"User" : True})
    return redirect('/')
  


     

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5001, debug=True)
