import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from models import Staff, Customer, Event, db


app = Flask(__name__)

# Load default config and override config from an environment variable

app.config.update(dict(
	DEBUG=True,
	SECRET_KEY='development key',
	USERNAME='owner',
	PASSWORD='pass',
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'catering.db')
))

app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
db.init_app(app)

@app.before_request
def before_request():
    g.user = None
    if 'staff_id' in session:
        g.user = Staff.query.filter_by(id=session['staff_id']).first()
    elif 'cust_id' in session:
        g.user = Customer.query.filter_by(id=session['cust_id']).first()


@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	db.drop_all()
	db.create_all()
	print('Intialized Database')

#we will automatically go to the login page
@app.route('/')
def login():
	return render_template('login.html')

#if they click login as owner from the login page we will see if they type in the correct user and pass combo
@app.route('/loginOwner<what>', methods=['GET', 'POST'])
def loginOwner(what):
    if what =="enter":
        db.session.commit()

        error = None
        if request.method == 'POST':
            if request.form['username'] != app.config['USERNAME']:
                error = 'Invalid username'
            elif request.form['password'] != app.config['PASSWORD']:
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                flash('You were logged in')
                events = Event.query.all()

                return render_template('loggedInOwner.html', events=events)
            return render_template('loginOwner.html')
    else:
        return render_template('login.html')

@app.route('/loginStaff<what>', methods=['GET', 'POST'])
def loginStaff(what):
    if what == "enter":
        if request.method == 'POST': 
            
            staff = Staff.query.filter_by(username=request.form['username']).first()

            
            if staff is None: 
                error = "Invalid Username" 
            elif request.form['password'] != staff.password:
                error = "invalid password"
            else:
                session['staff_id'] = staff.id
                allEvents = Event.query.all()
                myEvents = Staff.query.filter_by(id = session['staff_id']).first().events.all()
                availableEvents = []
                for event in allEvents:
                    if event not in myEvents:
                        if len(event.workers.all()) < 3:
                            availableEvents.append(event)
                        
                return render_template('loggedInStaff.html', availableEvents = availableEvents, myEvents = myEvents)

        return render_template('loginStaff.html')
    else:
        return render_template('login.html')

@app.route('/loginCustomer<what>', methods=['GET', 'POST'])
def loginCustomer(what):
    if what =="enter":
        if request.method == 'POST': 
            
            cust = Customer.query.filter_by(username=request.form['username']).first()
            
            if cust is None: 
                error = "Invalid Username" 
            elif request.form['password'] != cust.password:
                error = "invalid password"
            else:
                allEvents = Event.query.all()
                myEvents = []
                for event in allEvents:
                    if int(event.customer_id) == int(cust.id):
                        myEvents.append(event)
                session['cust_id'] = cust.id
                return render_template('loggedInCustomer.html', myEvents = myEvents)

        return render_template('loginCustomer.html')
    else:
        return render_template('login.html')

@app.route('/loggedInOwner<what>')
def staffCreateOrLogOut(what):
    if what == 'create':
        return render_template('createStaff.html')
    else:
        return render_template('login.html')

@app.route('/createStaff', methods = ['POST'])
def createStaff():
    #first check if username already exists
    db.session.add(Staff(request.form['username'], request.form['password']))
    db.session.commit()
    events = Event.query.all()
    return render_template('loggedInOwner.html', events = events)

@app.route('/login<ownerStaffOrCus>', methods = ['GET'])
def logInAs(ownerStaffOrCus):
    if ownerStaffOrCus == 'owner':
        return render_template('logInOwner.html')
    elif ownerStaffOrCus == 'staff':
        return render_template('logInStaff.html')
    elif ownerStaffOrCus == 'customer':
        return render_template('logInCustomer.html')
    else:
        return render_template('createAccount.html')

@app.route('/createAccount', methods = ['POST'])
def createAccount():
    #check if username already exists
    #if username already exists, redirect them back to create account, but tell them
    #the user already exists
    cust = Customer(request.form['username'], request.form['password'])
    db.session.add(cust)
    db.session.commit()
    session['cust_id'] = cust.id
    return render_template('login.html')

@app.route('/createStaff')
def logOut():
    return render_template('login.html')

@app.route('/loggedInStaff<what><event_id>', methods = ['POST', 'GET'])
def staffFunctions(what, event_id):
    staff = Staff.query.filter_by(id = session['staff_id']).first()
    events = Event.query.all()
    availableEvents = []

    
    if what == "logout":
        return render_template('login.html')
    elif what == "add":
        staff.events.append(Event.query.filter_by(id = event_id).first())
        db.session.commit()
        thisEvent = Event.query.filter_by(id = event_id).first()
        myEvents = Staff.query.filter_by(id = session['staff_id']).first().events.all()
        for event in events:
            if event not in myEvents:
                if len(event.workers.all()) < 3:
                    availableEvents.append(event)

        return render_template('loggedInStaff.html', availableEvents = availableEvents, myEvents = myEvents)
    else:
        return render_template('loggedInStaff.html')


@app.route('/loggedInCustomer<what><event_id>', methods = ['POST', 'GET'])
def custFunctions(what, event_id):
    if what == "logout":
        return render_template('login.html')
    elif what == "create":
        return render_template('createEvent.html')
    else:#they are cancelling an event
        deleteEvent = Event.query.get_or_404(event_id)
        db.session.delete(deleteEvent)
        db.session.commit()
        allEvents = Event.query.all()
        myEvents = []
        for event in allEvents:
            if int(event.customer_id) == int(session['cust_id']):
                myEvents.append(event)
        
        return render_template('loggedInCustomer.html', myEvents = myEvents)



@app.route('/createEvent<what>', methods = ['POST','GET'])
def createEvent(what):
        if what == "create":
            checkDate = None
            date = request.form['date']
            events = Event.query.all()
            num = int(0)
            for event in events:
                if date == event.date:
                    checkDate = "We are not available to cater on the requested day, please choose another day. We would love to serve you."
            
            if checkDate == None:
                db.session.add(Event(request.form['date'], request.form['name'], session['cust_id']))
                db.session.commit()
                allEvents = Event.query.all()
                myEvents = []
                for event in allEvents:
                    if int(event.customer_id) == int(session['cust_id']):
                        myEvents.append(event)
                return render_template('loggedInCustomer.html', myEvents = myEvents, checkDate = checkDate)
            else:
                return render_template('createEvent.html', checkDate = checkDate)
        else:
            return render_template('login.html')

@app.route('/createAccount')
def logOutR():
    return render_template('login.html')

