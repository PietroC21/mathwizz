# COP4521TermProject
----------------------------------------------------------------------------
Website name:if we fix it mathwiz.live
Domain: .live
---------------------------------------------------------------------------------
Project Description:
---------------------------------------------------------------------------------
Math Problem Solving Application that can solve the following Problems with RBAC 
  * Single Integrals Definite and Indefinite (Premium and Admin)
  * Derivatives (Premium and Admin)
  * Algebra (Quadratic Equations and System of Equations)
  * Geometry (Area of Shapes)
Flask is our Web Development Framework
---------------------------------------------------------------------------------
Security: 
  * Firebase for User Authentication 
      * Its on built in Authentication service
  * CSRF Token protection 
      * Protecting form data from malicious JS code using Flaskwtf CSRF Protect 
      
----------------------------------------------------------------------------------
Database: 
  * We have a NoSQL database on Firebase
----------------------------------------------------------------------------------
Libraries required for the project:
  * refer to requirements.txt 
-----------------------------------------------------------------------------------
How to run project:
  *Clone the repository 
  *Create a python virtual environment
  `pip3 install -r requirements.txt`
  `python3 app.py`
