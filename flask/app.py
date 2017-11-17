from flask import Flask, render_template, redirect, session
from firebase import firebase 
import os
from flask_wtf import FlaskForm as Form
from wtforms.fields import *
from wtforms.validators import *
from flask_wtf.csrf import CSRFProtect
from firebase.firebase import FirebaseApplication, FirebaseAuthentication
import uuid
import requests
import json
import time
from functools import wraps
#from flask.ext.session import Session


firebase_path = os.environ.get('FIREBASE_PATH')


app = Flask(__name__)
app.secret_key = os.environ.get('APP_KEY')


firebase = firebase.FirebaseApplication(firebase_path, None)


#SESSION_TYPE = 'redis'
#Session(app)

def sign_in_with_email_and_password(email, password):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={0}".format(os.environ.get('APP_KEY'))
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        request_object = requests.post(request_ref, headers=headers, data=data)
        current_user = request_object.json()
        try: 
            reg = current_user["registered"]
            session["auth"] = current_user["idToken"]
            
            # Say it will expire in expiresIn seconds - 5 minutes 
            # session["auth_expiration"] = time.time() + 10
            session["auth_ends_at"] = time.time() + int(current_user["expiresIn"]) - 60*5
            
            print "Hello again"
            print session["auth"]
            return redirect("/api/put")
        except KeyError:
            print "KeyError"
            return redirect("localhost:5000/api/login", code=302)

 

class FirePut(Form):
    photo = StringField('Photo', validators=[DataRequired(), URL(require_tld=True, message=None)])
    lat = DecimalField('Lat', validators=[DataRequired(), NumberRange(min=40.0, max = 43.0)])
    longitude = DecimalField('Long', validators=[DataRequired(), NumberRange(min=-71.0, max = -69.0)])
    artist = StringField('Artist', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    month = StringField('Month', validators=[DataRequired(), AnyOf(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1980, max = 3000)])
    description = TextAreaField('Description', validators=[DataRequired()])
    medium = StringField('Medium', validators=[DataRequired()])

class Validate(Form):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class ArtistPut(Form):
    photo = StringField('Photo', validators=[DataRequired(), URL(require_tld=True, message=None)])
    name = StringField('Name', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[DataRequired()])

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'auth' in session and 'auth_expiration' in session:
            auth = session['auth']
            auth_expiration = session['auth_expiration']
            
            # If the auth token is not expired, then you're still "logged in"
            if auth and auth_expiration and time.time() <= auth_expiration:
                return f(*args, **kwargs)
            
        return redirect('/api/login')
    return decorated



count = 0

@app.route('/api/put', methods=['GET', 'POST'])
@requires_auth
def fireput():
    form = FirePut()
    if form.validate_on_submit():
        firebase.authentication = {"provider": "anonymous"}
        global count
        count += 1
        putData = { 'Photo' : form.photo.data, 'Lat' : form.lat.data,
                    'Long' : form.longitude.data, 'Artist' : form.artist.data,
                    'Title' : form.title.data, 'Month' : form.month.data,
                    'Year' : form.year.data, 'Description' : form.description.data,
                    'Medium' : form.medium.data }
        firebase.put('/murals', uuid.uuid4(), putData)
        return render_template('form-result.html', putData=putData)
    return render_template('My-Form.html', form=form)

@app.route('/api/login', methods=['GET','POST'])
def validate():
    form = Validate()
    if form.validate_on_submit():
        return sign_in_with_email_and_password(form.email.data, form.password.data)
    return render_template('validation-form.html', form=form)

@app.route('/api/new_artist', methods=['GET', 'POST'])
@requires_auth
def artistput():
    form = ArtistPut()
    if form.validate_on_submit():
        putData = { 'photo' : form.photo.data, 'name' : form.name.data,
                    'city' : form.city.data, 'bio' : form.bio.data}
        artists = firebase.get('/', 'artists')
        firebase.put('/artists', str(len(artists)), putData)
        return redirect("localhost:5000/api/put", code=302)
    return render_template('artist-form.html', form=form)

@app.route('/api/get', methods = ['GET'])
def fireget():
    murals = firebase.get('/','murals')
    print(murals)
    return render_template('disp-all.html', murals=murals)


@app.route('/')
def hello_world():
    return firebase.get('/', 'test')
