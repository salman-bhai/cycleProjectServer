import json
from flask import Flask, request, Response, render_template, abort, url_for
from flask_httpauth import HTTPDigestAuth
from flask_migrate import Migrate
import sqlite3
import gevent
import time
from flask_httpauth import HTTPDigestAuth

# Flask Variables
app = Flask(__name__)
auth = HTTPDigestAuth()

app.config['SECRET_KEY'] = 'Cycle Project Mentor: Akshay Revankar'

# Database Variables
DATABASE = 'file::memory:?cache=shared'

# Users to access app
# Users to be authenticated
users = {
    "akshay": "revankar",
    "salman": "shah",
    "hrishi": "hiraskar"
}


# Helper Methods
def event_stream(cycle_id):
    while True:
        # database query
        db = sqlite3.connect("file::memory:?cache=shared")
        cur = db.cursor()

        # Query to get user rfid number
        id = (cycle_id,)
        # TODO: Revisit this logic later
        cur.execute("SELECT * FROM rides WHERE cycle_id = ? and status = 0 and paid = 0", id)
        ride = cur.fetchall()

        # when there is new entry with current id
        if ride is not None:
            ride_id = ride[0]
            # Query to get user rfid number
            id = (ride[2],)
            # TODO: Revisit this logic later
            cur.execute("SELECT * FROM users WHERE id = ? ", id)
            user = cur.fetchone()
            rfid_no = user[4]

            # yield rfid and ride id
            yield 'event: user_request\ndata: %s\n\n' % json.dumps({"ride_id":ride_id, "rfid":rfid_no})

        # Every 1 second query database if new ride with tho
        gevent.sleep(1)

"""
Android Code ~ SS ~
"""

@app.route('/red_to_yellow')
def sse_request():
    # Set response method to event-stream
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/qr_code_receive', methods=['POST'])
def qr_code():
    print(str(json.dumps(request.json)))
    email = request.json['email']
    cycle_id = request.json['cycle_id']

    db = sqlite3.connect("file::memory:?cache=shared")
    cur = db.cursor()

    # Query to get user rfid number
    email_id = (email,)
    cur.execute("SELECT * FROM users WHERE email = ? ",email_id)
    user = cur.fetchone()
    user_id = user[0]

    if user == None:
        return json.dumps({'success': False, 'message': 'Kill App Programmer'})

    cycle_id = (cycle_id,)
    cur.execute("SELECT * FROM cycles WHERE id = ? ",cycle_id)
    cycle = cur.fetchone()

    if cycle == None:
        return json.dumps({'success': False, 'message': 'QR Code is wrong'})

    rfid_number = user[4]

    # Query to get user rfid number
    ride = (user_id, cycle_id,)
    cur.execute("INSERT INTO rides('cycle_id, user_id') VALUES(?, ?) ",ride)


    Response(event_stream(), mimetype='text/event-stream')

    # current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # ride = [(cycle_id, user_id, current_time)]
    # c.execute("INSERT INTO rides('cycle_id, user_id, start_time') VALUES(?, ?, ?) ",ride)

    return json.dumps({'success': True})


# Assign RFID to user
@app.route('/assign_rfid', methods=['POST'])
def assign_rfid_to_user():
    pass


# Simple HTTP Login of the website
@app.route('/login', methods=['POST'])
def login():
    # Evaluate Post Parameters from Login
    print(str(json.dumps(request.json)))
    email = request.json['email']
    password = request.json['password']

    db = sqlite3.connect("file::memory:?cache=shared")
    cur = db.cursor()

    email_id = (email,)

    cur = cur.execute("SELECT * FROM users WHERE email = ? and rfid_no IS NOT NULL",email_id)
    user = cur.fetchone()
    print(user)
    if user is None:
        return json.dumps({'success': False, 'message': 'Get your Smart Cycle Card'})

    if password == user[3]:
        return json.dumps({'success': True})

    return json.dumps({'success': False, 'message': 'Email doesn\'t exist'})

# Simple Register User Option
@app.route('/register', methods=['POST'])
def register_user():
    # Evaluate POST Parameters from Register
    print(str(json.dumps(request.json)))
    name = request.json['username']
    email = request.json['email']
    password = request.json['password']

    db = sqlite3.connect("file::memory:?cache=shared")
    cur = db.cursor()

    user_record = (name, email, password)
    cur.execute("INSERT INTO users(name, email, encrypted_password) VALUES(?, ?, ?) ",user_record)
    db.commit()

    return json.dumps({'success': True, 'message': 'Kindly contact administrator for Card to login'})

@app.route('/events')
def sse_request():
	# Set response method to event-stream
    return Response(event_stream(request.args.get('cycle_id', '')), mimetype='text/event-stream')

"""
Web App Code ~ SS ~
"""

# Load Users
@app.route('/load_users', methods=['POST'])
def load_users():
    data = request.json['data']

    db = sqlite3.connect("file::memory:?cache=shared")
    cur = db.cursor()

    if data == "no_rfid_number":
        user_data = cur.execute("SELECT * from users WHERE rfid_no IS NULL")
        user_data = user_data.fetchall()
    elif data == "rfid_number":
        user_data = cur.execute("SELECT * from users where rfid_no IS NOT NULL")
        user_data = user_data.fetchall()

    return json.dumps(user_data)

# Authenticating users from Dictionary
@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html', name='Cycle Project')



# Main Method in the Server code
if __name__ == '__main__':
    # Set server address 0.0.0.0:5000/
    app.run(host="0.0.0.0", port=5000, debug=True)
