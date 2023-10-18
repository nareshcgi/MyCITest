from flask import Flask, Response, render_template, jsonify, request, session, g
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import timedelta, datetime
import uuid, atexit

# ****** START: DEFAULT SECURITY CONFIGURATION **********
default_user = "naresh"
default_password = "naresh"

app = Flask(__name__, static_folder='ui')
app.config.update(
    DEBUG=True,
    SECRET_KEY="secret_sauce",
    SESSION_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    REMEMBER_COOKIE_DURATION=timedelta(days=2)
)
remember_seconds = 60  # 30 seconds
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=remember_seconds)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_message="Invalid resource or access denied."

# ****** END: DEFAULT SECURITY CONFIGURATION *********

# ****** START: ENABLE CORS *********
CORS(app)
cors = CORS(app, resources={"/api/*": {"origins": "*"}})
# ****** END: ENABLE CORS *********

# ****** START: ENABLE CSRF *********
# Have cookie sent
app.config["SECURITY_CSRF_COOKIE_NAME"] = "XSRF-TOKEN"

# Don't have csrf tokens expire (they are invalid after logout)
app.config["WTF_CSRF_TIME_LIMIT"] = None

# You can't get the cookie until you are logged in.
#app.config["SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS"] = True
csrf = CSRFProtect(app)
csrf.init_app(app)
# ****** END: ENABLE CSRF *********

# ****** START: ALL COMMON METHODS GOES HERE *********
def generateUserId():
    user_uid = len(users) + 1
    return user_uid, generateUUID()

def generateUUID():
    return str(uuid.uuid4())

# User related methods
def get_user(user_id: int):
    for user in users:
        if int(user["id"]) == int(user_id):
            return user
    return None

# User related methods
def getUserByUserName(username):
    for user in users:
        if int(user["username"]) == username:
            return user
    return None

class User(UserMixin):
    ...

def userExists(username):
    for user in users:
        if user["username"] == username:
            return True
    return False

def check_session_timeout():
    if 'user_id' not in session:
        return False  # User not logged in
    last_active = session.get('last_active', None)
    if last_active and datetime.now() - last_active > app.permanent_session_lifetime:
        return True  # Session has expired
    session['last_active'] = datetime.now()
    return False  # Session is still active

# ****** END: ALL COMMON METHODS GOES HERE *********

# ****** STAET: ALL GLOBAL STORE GOES HERE *********
excluded_routes = ['login']
users = [
    {
        "id": 1,
        "uuid": generateUUID(),
        "username": default_user,
        "password": default_password,
    }
]
# ****** END: ALL GLOBAL STORE GOES HERE *********

# ****** START: ALL API DEF GOES HERE *********
@app.route("/api/user", methods=["PUT"])
@login_required
@csrf.exempt
def addUser():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not userExists(username):
        users.append({
            "id": len(users) + 1,
            "username": username,
            "password": password,
            "uuid": generateUUID()
        })
        return jsonify({"success": True, "message": "User {} Added Successfully!".format(username)})
    else:
        return jsonify({"message":"User Already Exists!"})

@app.route("/api/user", methods=["GET"])
@login_required
@csrf.exempt
def getUser():
    user = get_user(current_user.id)
    return jsonify({"username": user["username"], "uuid": user["uuid"]})

@app.route("/api/login", methods=["POST"])
@csrf.exempt
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    for user in users:
        if user["username"] == username and user["password"] == password:
            user_model = User()
            user_model.id = user["id"]
            user_model.username = user["username"]
            print("User {} logged in successfully!".format(username))
            login_user(user_model)
            g.user=user
            session['user'] = user
            session['last_active'] = datetime.now()
            return jsonify({"login": True})
    return jsonify({"login": False})

@app.route("/api/logout")
@login_required
@csrf.exempt
def logout():
    logout_user()
    return jsonify({"logout": True})

@app.route("/api/getsession")
@csrf.exempt
def check_session():
    if current_user.is_authenticated:
        return jsonify({"login": True})
    return jsonify({"login": False})


@app.route("/api/keepsessionalive", methods=["GET"])
@login_required
@csrf.exempt
def keepSessionAlive():
    # dummy call to keep session alive
    pass

@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')      
# ****** END: ALL API DEF GOES HERE *********

# ****** START: ALL HANDLERS GOES HERE *********
# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    print("401 error: {}-{}-{}".format(e.description, e.code, e))
    return Response('<p>{}</p>'.format(e.description))

# callback to reload the user object
@login_manager.user_loader
def user_loader(id: int):
    user = get_user(id)
    if user:
        user_model = User()
        user_model.id = user["id"]
        return user_model
    return None

@app.before_request
def before_request():
    print("inside before request {}- Endpoint: {}".format(datetime.now(),request.endpoint))
    if request.endpoint in excluded_routes:
        return
    print("session: {}".format(session.values()))
    print("Last Active: {}".format(session.get('last_active', None)))
    session.permanent = True
    print("inside before request {}- Current User: {}".format(datetime.now(),current_user))
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=remember_seconds)
    session['last_active'] = datetime.now()
    session.modified = True
    g.user = current_user
# ****** END: ALL HANDLERS GOES HERE *********

# ****** START: Schedule Jobs *********
scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', seconds=40)
def job1():
    #scheduler.print_jobs()
    dt = datetime.now()
    #print("Scheduled job executed: {} - {}".format(users,dt))
    print("Job1 - Scheduled job executed: {}".format(dt))

@scheduler.scheduled_job('interval', seconds=60)
def job2():
    dt = datetime.now()
    print("Job2 - Scheduled job executed: {}".format(dt))

#scheduler = BackgroundScheduler()
#scheduler.add_job(job, 'interval', seconds=30)
if not scheduler.running:
    scheduler.start()

#@app.before_first_request
#def start_scheduler():
#    scheduler.start()

def stop_scheduler(exception=None):
    scheduler.shutdown()
    print("Scheduler stopped")

atexit.register(stop_scheduler)
#@app.teardown_appcontext

# ****** END: Schedule Jobs *********

