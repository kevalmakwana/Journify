from flask import Flask, render_template, request, url_for, redirect, flash, session, jsonify
import urllib.parse
import MySQLdb
from datetime import datetime
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

journify = Flask(__name__)
journify.secret_key = 'random hash'

db = MySQLdb.connect('10.17.1.82', 'keval', 'Keval@11', 'journify_db')

@journify.route("/")
def signup_page():
    return render_template("signup2.html", title='Sign-Up')

@journify.route('/sign-in')
def signin_page():
    return render_template("signin2.html", title='Sign-In')

@journify.route("/signup", methods=['POST'])
def signup():
    global username
    global email
    username = request.form['username']
    username = username.lower() 
    email = request.form['email']
    password = request.form['password']
    if username and email and password:
        cursor = db.cursor()
        cursor.execute("select email from users where email = %s", (email,))
        result = cursor.fetchone()
        if result:
            flash('That e-mail address is already taken. Just sign-in.')
            return redirect(url_for("signin_page"))
        cursor.execute("insert into users (username, email, password) values (%s, %s, %s)", (username, email, password))
        db.commit()
        cursor.close()
        session['username'] = username
        session['email'] = email
        return redirect(url_for("home"))
    flash('Please fill all the fields', 'error')
    return redirect(url_for("signup_page"))

@journify.route('/login', methods=['POST'])
def login():
    global username
    email = request.form['email']
    password = request.form['password']
    cursor = db.cursor()
    cursor.execute("select * from users where email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        if user[1] == password:
            session['username'] = user[0]
            session['email'] = user[2]
            return redirect(url_for("home"))
        else:
            flash('Incorrect password. Try again')
            return redirect(url_for("signin_page"))
    flash('No such user found. Please sign-up first')
    return redirect(url_for("signup_page"))

@journify.route('/search_flight_origin', methods=['GET'])
def search_flight_origin():
    query = request.args.get('q')
    cur = db.cursor()
    cur.execute("SELECT distinct origin FROM flights_new WHERE origin LIKE %s LIMIT 5", ('%' + query + '%',))
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify(results)

@journify.route('/search_flight_destination', methods=['GET'])
def search_flight_destination():
    query = request.args.get('q')
    cur = db.cursor()
    cur.execute("SELECT distinct destination FROM flights_new WHERE destination LIKE %s LIMIT 5", ('%' + query + '%',))
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify(results)

@journify.route('/search_train_origin', methods=['GET'])
def search_train_origin():
    query = request.args.get('q')
    cur = db.cursor()
    cur.execute("SELECT distinct origin FROM trains WHERE origin LIKE %s LIMIT 5", ('%' + query + '%',))
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify(results)

@journify.route('/search_train_destination', methods=['GET'])
def search_train_destination():
    query = request.args.get('q')
    cur = db.cursor()
    cur.execute("SELECT distinct destination FROM trains WHERE destination LIKE %s LIMIT 5", ('%' + query + '%',))
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify(results)

@journify.route('/select_flight', methods=['post'])
def select_flight():
    #Get the selected row data from the form
    flight_no = request.form['flight_no']
    airline = request.form['airline']
    origin = request.form['origin']
    destination = request.form['destination']
    dep_time = request.form['dep_time']
    arr_time = request.form['arr_time']
    dep_date = request.form['dep_date']

    username= session.get('username')
    email = session.get('email')

    # Create the URL with data as query parameters
    #, email=email
    url = url_for('selected_flight', flight_no=flight_no, airline=airline, origin=origin, destination=destination, dep_time=dep_time, arr_time=arr_time, dep_date=dep_date, username=username, email=email)

    return redirect(url)

@journify.route('/selected_flight')
def selected_flight():
    # Get the data from the query parameters
    flight_no = request.args.get('flight_no')
    airline = request.args.get('airline')
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    dep_time_encoded = request.args.get('dep_time')
    arr_time_encoded = request.args.get('arr_time')
    dep_date = request.args.get('dep_date')
    origin_airport = get_airport_info(origin)
    destination_airport = get_airport_info(destination)
    origin_code = origin_airport['iata']
    destination_code = destination_airport['iata']
    origin_name = origin_airport['name']
    destination_name = destination_airport['name']

    # Decode the URL-encoded strings
    dep_time = urllib.parse.unquote(dep_time_encoded)
    arr_time = urllib.parse.unquote(arr_time_encoded)

    # Calculate duration
    dep_datetime = datetime.strptime(dep_time, '%H:%M:%S')
    arr_datetime = datetime.strptime(arr_time, '%H:%M:%S')
    duration = arr_datetime - dep_datetime

    username= session.get('username')
    email = session.get('email')

    return render_template('selected_flight2.html', flight_no=flight_no, airline=airline, origin=origin, destination=destination, dep_time=dep_time, arr_time=arr_time, duration=duration, dep_date=dep_date, username=username, email=email, origin_code=origin_code, origin_name=origin_name, destination_code=destination_code, destination_name=destination_name, title='Book Flight')

def get_airport_info(city_name):
    cursor = db.cursor()
    cursor.execute("SELECT iata from airports where city LIKE %s", (city_name, ))
    results = cursor.fetchone()
    cursor.close()
    code = results[0]
    url = f"https://airport-info.p.rapidapi.com/airport?iata={code}"
    headers = {
        'X-RapidAPI-Key': '381823555cmshfc1a3369bf2536cp13df19jsn3ee538a47d4b',
        'X-RapidAPI-Host': 'airport-info.p.rapidapi.com'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return "Error fetching airport information."

@journify.route('/payment_page_flight', methods=['post'])
def payment_page_flight():
    username = session.get('username')
    email = session.get('email')
    # Get the data from the query parameters
    flight_no = request.form['flight_no']
    airline = request.form['airline']
    origin = request.form['origin']
    destination = request.form['destination']
    dep_time = request.form['dep_time']
    arr_time = request.form['arr_time']
    dep_date = request.form['dep_date']
    duration = request.form['duration']

    return render_template('payment_flight.html', flight_no=flight_no, airline=airline, origin=origin, destination=destination, dep_time=dep_time, arr_time=arr_time, duration=duration, dep_date=dep_date, username=username, email=email, title='Payment Gateway')

@journify.route('/payment_flights', methods=['post', 'get'])
def payment_flights():
    username = session.get('username')
    email = session.get('email')
    # Get the data from the query parameters
    flight_no = request.form['flight_no']
    airline = request.form['airline']
    origin = request.form['origin']
    destination = request.form['destination']
    dep_time = request.form['dep_time']
    arr_time = request.form['arr_time']
    dep_date = request.form['dep_date']

    cursor = db.cursor()
    cursor.execute("insert into user_booked_flight_details (username, email, flight_no, airline, origin, destination, dep_time, arr_time, travel_date, Status) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, email, flight_no, airline, origin, destination, dep_time, arr_time, dep_date, "Journey Not Completed"))
    db.commit()
    cursor.close()

    # send_email_flight(email, flight_no, airline, origin, destination, dep_date, dep_time, arr_time, username)

    return render_template('success.html', title='Booking Confirmed')

@journify.route('/book_flight_ticket', methods=['POST'])
def book_flight_ticket():
    username = session.get('username')
    email = session.get('email')
    # Get the data from the query parameters
    flight_no = request.form['flight_no']
    airline = request.form['airline']
    origin = request.form['origin']
    destination = request.form['destination']
    dep_time = request.form['dep_time']
    arr_time = request.form['arr_time']
    dep_date = request.form['dep_date']
    grand_total = request.form['grand_total']

    cursor = db.cursor()
    cursor.execute("insert into user_booked_flight_details (username, email, flight_no, airline, origin, destination, dep_time, arr_time, travel_date, Status) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, email, flight_no, airline, origin, destination, dep_time, arr_time, dep_date, "Journey Not Completed"))
    db.commit()
    cursor.close()

    # send_email_flight(email, flight_no, airline, origin, destination, dep_date, dep_time, arr_time, username, grand_total)

    return render_template('success.html', title='Booking Confirmed')

def send_email_flight(recipient_email, flight_no, airline, origin, destination, dep_date, dep_time, arr_time, username, total):
    # Define the email address of sender and recipient

    sender_email = 'travelwithjournify682@gmail.com'

    # Define the email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = "Flight Booking Details"

    body = "Dear " + username +", \n Thank you for booking using Journify. \n Your booking details are as follows:" + "\n" 
    details = "Flight Number: " + flight_no + "\n" + "Airline: " + airline + "\n" + "Origin Airport: " + origin + "\n" + "Destination Airport: " + destination + "\n" + "Departure Date: " + dep_date + "\n" + "Departure Time: " + dep_time + "\n" + "Arrival Time: " + arr_time + "\n" + "Amount Paid: " + total + "\n" +  "Thank You!! Eager to serve you again."

    #"Train Number: " + train_name + "\n" + "Train No: " + train_no + "\n" + "Source Station: " + origin + "\n" + "Destination Station: " + destination + "\n" + "Travel Date: " + display_date

    body = body + details

    message.attach(MIMEText(body, 'plain'))

    # Create an SMTP session and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as new_session:
        new_session.starttls()
        new_session.login(sender_email, 'ejacinjqgbonvewi')
        text = message.as_string()
        new_session.sendmail(sender_email, recipient_email, text)

@journify.route('/flight/search', methods=['GET', 'POST'])
def search_flights():
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        dep_date = request.form['dep_date']
        cursor = db.cursor()
        cursor.execute("SELECT * FROM flights_new WHERE origin = %s and destination = %s and valid_from <= %s and valid_till >= %s" , (origin, destination,dep_date, dep_date))
        results = cursor.fetchall()
        username= session.get('username')
        email = session.get('email')
        return render_template('newsearchresultsflight.html', results=results, dep_date=dep_date, username=username, email=email, title='Search Flights')
    return redirect(url_for('flight'))

@journify.route('/train/search', methods=['GET', 'POST'])
def search_trains():
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        travel_date = request.form['travel_date']
        cursor = db.cursor()
        date_obj = datetime.strptime(travel_date, '%Y-%m-%d')
        day_of_week = date_obj.strftime('%A')
        display_date = date_obj.strftime('%d-%m-%y')
        cursor.execute("SELECT * FROM trains WHERE origin = %s and destination = %s and days = %s" , (origin, destination, day_of_week))
        results = cursor.fetchall()
        cursor.close()
        username= session.get('username')
        email = session.get('email')
        #, travel_date=travel_date
        return render_template('train_searchs.html', results=results, username=username, email=email, day_of_week=day_of_week, travel_date=travel_date, display_date=display_date, title='Search Trains')
    return redirect(url_for('train'))

@journify.route('/selected_train')
def selected_train():
    # Get the data from the query parameters
    train_no = request.args.get('train_no')
    train_name = request.args.get('train_name')
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    day_of_week = request.args.get('day_of_week')
    travel_date = request.args.get('travel_date')
    display_date = request.args.get('display_date')

    username= session.get('username')
    email = session.get('email')

    return render_template('selected_train2.html', train_no=train_no, train_name=train_name, origin=origin, destination=destination, day_of_week=day_of_week, travel_date=travel_date, username=username, email=email, display_date=display_date, title='Search Trains')

@journify.route('/select_train', methods=['post'])
def select_train():
    #Get the selected row data from the form
    train_no = request.form['train_no']
    train_name = request.form['train_name']
    origin = request.form['origin']
    destination = request.form['destination']
    day_of_week = request.form['day_of_week']
    travel_date = request.form['travel_date']
    display_date = request.form['display_date']

    username= session.get('username')
    email = session.get('email')

    # Create the URL with data as query parameters
    #, email=email
    url = url_for('selected_train', train_no=train_no, train_name=train_name, origin=origin, destination=destination, day_of_week=day_of_week, travel_date=travel_date, username=username, email=email, display_date=display_date)

    return redirect(url)

@journify.route('/payment_page_train', methods=['post'])
def payment_page_train():
    username = session.get('username')
    email = session.get('email')
    # Get the data from the query parameters
    train_no = request.form['train_no']
    train_name = request.form['train_name']
    origin = request.form['origin']
    destination = request.form['destination']
    day_of_week = request.form['day_of_week']
    travel_date = request.form['travel_date']

    return render_template('payment_train.html', train_no=train_no, train_name=train_name, origin=origin, destination=destination, day_of_week=day_of_week, username=username, email=email, travel_date=travel_date, title='Payment Gateway')

@journify.route('/payment_trains', methods=['post', 'get'])
def payment_trains():
    username = session.get('username')
    email = session.get('email')
    # Get the data from the query parameters
    train_no = request.form['train_no']
    train_name = request.form['train_name']
    origin = request.form['origin']
    destination = request.form['destination']
    day_of_week = request.form['day_of_week']
    travel_date = request.form['travel_date']
    display_date = request.form['display_date']

    cursor = db.cursor()
    cursor.execute("insert into user_booked_train_details (username, email, train_no, train_name, origin, destination, day_of_week, travel_date, Status) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, email, train_no, train_name, origin, destination, day_of_week, travel_date, "Journey Not Completed"))
    db.commit()
    cursor.close()

    # send_email_train(email, train_no, train_name, origin, destination, day_of_week, display_date, username)

    return render_template('success.html', title='Booking Confirmed')

@journify.route('/book_train_ticket', methods=['POST'])
def book_train_ticket():
    username = session.get('username')
    email = session.get('email')
    # Get the data from the query parameters
    train_no = request.form['train_no']
    train_name = request.form['train_name']
    origin = request.form['origin']
    destination = request.form['destination']
    day_of_week = request.form['day_of_week']
    travel_date = request.form['travel_date']
    display_date = request.form['display_date']

    cursor = db.cursor()
    cursor.execute("insert into user_booked_train_details (username, email, train_no, train_name, origin, destination, day_of_week, travel_date, Status) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, email, train_no, train_name, origin, destination, day_of_week, travel_date, "Journey Not Completed"))
    db.commit()
    cursor.close()

    # send_email_train(email, train_no, train_name, origin, destination, day_of_week, display_date, username)

    return render_template('success.html', title='Booking Confirmed')

def send_email_train(recipient_email, train_no, train_name, origin, destination, day_of_week, display_date, username):
    # Define the email address of sender and recipient

    sender_email = 'travelwithjournify682@gmail.com'

    # Define the email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = "Train Booking Details"

    body = "Dear " + username +", \nThank you for booking using Journify. \nYour booking details are as follows:" + "\n" 
    details = "Train Number: " + train_name + "\n" + "Train No: " + train_no + "\n" + "Source Station: " + origin + "\n" + "Destination Station: " + destination + "\n" + "Travel Date: " + display_date + "\n" + "Travel Day: " + day_of_week

    #"Train Number: " + train_name + "\n" + "Train No: " + train_no + "\n" + "Source Station: " + origin + "\n" + "Destination Station: " + destination + "\n" + "Travel Date: " + display_date

    body = body + details + "\nThank You!! Eager to serve you again.."

    message.attach(MIMEText(body, 'plain'))

    # Create an SMTP session and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as new_session:
        new_session.starttls()
        new_session.login(sender_email, 'ejacinjqgbonvewi')
        text = message.as_string()
        new_session.sendmail(sender_email, recipient_email, text)

@journify.route('/home')
def home():
    username= session.get('username')
    email = session.get('email')
    # Create a list of background image file names
    bg_images = ['../static/img/head_img/hawaii.jpg', '../static/img/head_img/secen_final.jpg', '../static/img/head_img/secen_final2.jpg', '../static/img/head_img/secen_final3.jpg', '../static/img/head_img/secen_final4.jpg']

    # select a random background image file name
    bg_image = random.choice(bg_images)
    
    return render_template('home.html', username = username, email=email, bg_image=bg_image, title='Home')

@journify.route('/flight/')
def flight():
    username= session.get('username')
    email = session.get('email')
    return render_template('flight.html', username = username, email=email, title='Search Flights')

@journify.route('/train/')
def train():
    username= session.get('username')
    email = session.get('email')
    return render_template('train.html', username = username, email=email, title='Search Trains')

@journify.route('/holiday/')
def holiday():
    username= session.get('username')
    email = session.get('email')
    return render_template('holiday.html', username = username, email=email, title='Holidays')

@journify.route('/trip/')
def trip():
    username = session.get('username')
    email = session.get('email')

    # By default, show the flight bookings
    selected_option = 'flight'

    # If the user has selected an option, update the selected_option variable
    if 'option' in request.args:
        selected_option = request.args['option']

    # Fetch the bookings from the MySQL database based on the selected option
    cursor = db.cursor()
    if selected_option == 'flight':
        cursor.execute("SELECT * FROM user_booked_flight_details where username = %s and email = %s", (username, email))
        bookings = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM user_booked_train_details")
        bookings = cursor.fetchall()
    cursor.close()

    # Render the HTML template with the bookings data
    return render_template('trip.html', bookings=bookings, selected_option=selected_option, username=username, email=email, title='My Trips')

@journify.route('/profile/')
def user():
    username= session.get('username')
    email = session.get('email')
    return render_template('user.html', username = username, email = email, title='My Profile')

@journify.route('/forgot_password')
def forgot_password():
    return render_template('forgotpassword.html', title='Forgot Password')

@journify.route('/create_password', methods=['post'])
def create_password():
    receipent_email = request.form['email']

    cursor = db.cursor()
    cursor.execute("select * from users where email = %s", (receipent_email,))
    user = cursor.fetchone()
    cursor.close()

    new_password = generate_password()

    if user:
        cursor=db.cursor()
        cursor.execute("update users set password = %s where email = %s", (new_password, receipent_email))
        db.commit()
        cursor.close()
        # send_password(receipent_email, user[0], new_password)
        return redirect(url_for("signin_page"))
    
    flash('No such user found. Please sign-up first')
    return redirect(url_for("signup_page"))

def generate_password():
    length = 8
    lower_case = string.ascii_lowercase
    upper_case = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation
    characters = lower_case + upper_case + digits + symbols
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def send_password(recipient_email, username, new_password):
    # Define the email address of sender and recipient

    sender_email = 'travelwithjournify682@gmail.com'

    # Define the email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = "Password Reset"

    body = "Dear " + username + ",\n\nYour password for Journify has been reset. \n\n"
    body += "New Password: " + new_password.center(20) + "\n\n"
    body += "Thank you!\nJournify Team"

    message.attach(MIMEText(body, 'plain'))

    # Create an SMTP session and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as new_session:
        new_session.starttls()
        new_session.login(sender_email, 'ejacinjqgbonvewi')
        text = message.as_string()
        new_session.sendmail(sender_email, recipient_email, text)
