import os
from flask import Flask, flash, redirect, render_template, request, session
from datetime import date
from flask_session import Session
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, apology, today

UPLOAD_FOLDER = './images/uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pm.db")


@app.route('/')
@login_required
def index():
    
    ls = db.execute("SELECT * FROM properties WHERE owner_id = :owner_id", owner_id=session['user_id'])
    properties_all = len(ls)
    ls = db.execute('SELECT * FROM properties WHERE owner_id = :owner_id and id in (SELECT property_id FROM (SELECT properties.id as property_id FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id and leases.start <= :today and leases.end >= :today))', owner_id=session['user_id'], today=today())
    properties_occupied = len(ls)

    ls = db.execute("SELECT x.*, properties.name as property_name FROM (SELECT invoices.*, contacts.name as contact_name FROM invoices JOIN contacts on invoices.contact_id = contacts.id WHERE invoices.owner_id = :owner_id and invoices.paid = 0)as x JOIN properties on x.property_id = properties.id", owner_id=session['user_id'])    
    invoices_open = len(ls)
    ls = db.execute("SELECT x.*, properties.name as property_name FROM (SELECT invoices.*, contacts.name as contact_name FROM invoices JOIN contacts on invoices.contact_id = contacts.id WHERE invoices.owner_id = :owner_id and invoices.due_date <= :today and invoices.paid = 0)as x JOIN properties on x.property_id = properties.id", owner_id=session['user_id'], today=today())
    invoices_outstanding = len(ls)

    return render_template("index.html", properties_all=properties_all, properties_occupied=properties_occupied, invoices_open=invoices_open, invoices_outstanding=invoices_outstanding)

# -----------------------------------------------User Management-----------------------------------------------------------

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        """ TODO"""
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if db.execute("SELECT * FROM users WHERE username = :username", username=username):
            return apology("User already exists")

        elif password != confirmation:
            return apology("Passwords does not match")

        else:
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)
            flash("Registered Succesfully")
            return redirect("/login")

    else:
        return render_template('signup.html')



@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        userdata = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        
        if len(userdata) != 1:
            return apology("Username or Password is wrong")
        
        if not check_password_hash(userdata[0]['hash'], password):
            return apology("Username or Password is wrong")


        session["user_id"] = userdata[0]['id']
        flash("Logged in succesfully")
        return redirect("/")
        

    else:
        session.clear()
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

# ----------------------------------------------- User Management End -----------------------------------------------------------
# --------------------------------------------------- Properties ----------------------------------------------------------------

@app.route("/properties")
@login_required
def properties():
    ls = db.execute("SELECT * FROM properties WHERE owner_id = :owner_id", owner_id=session['user_id'])
    return render_template('/properties.html', ls=ls, subtitle='All')


@app.route("/properties_available")
@login_required
def properties_avilable():
    ls = db.execute('SELECT * FROM properties WHERE owner_id = :owner_id and id not in (SELECT property_id FROM (SELECT properties.id as property_id FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id and leases.start <= :today and leases.end >= :today))', owner_id=session['user_id'], today=today())
    return render_template('/properties.html', ls=ls, subtitle='Available')


@app.route("/properties_occupied")
@login_required
def properties_occupied():
    ls = db.execute('SELECT * FROM properties WHERE owner_id = :owner_id and id in (SELECT property_id FROM (SELECT properties.id as property_id FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id and leases.start <= :today and leases.end >= :today))', owner_id=session['user_id'], today=today())
    return render_template('/properties.html', ls=ls, subtitle='Occupied')


@app.route("/add_property", methods=["GET", "POST"])
@login_required
def add_property():

    if request.method == "POST":
        
        name = request.form['name']
        beds = request.form['beds']
        rent = request.form['rent']
        description = request.form['description']

        img = request.files['image']
        print(img.filename)

        path = os.path.join(UPLOAD_FOLDER, img.filename)
        imgname = secure_filename(img.filename)

        while os.path.isfile(path):
            img.filename = f"{img.filename.split('.')[0]}1.{img.filename.split('.')[1]}"
            imgname = secure_filename(img.filename)
            path = os.path.join(UPLOAD_FOLDER, imgname)
            

        if  img and allowed_file(imgname):
            img.save(path)
            
        db.execute("INSERT INTO properties (name, rent, beds, description, owner_id, image) VALUES (:name, :rent, :beds, :description, :owner_id, :image)", name=name, rent=rent, beds=beds, description=description, owner_id=session['user_id'], image=path)
        flash("Property added succesfully")
        return redirect('/properties')
        

    else:
        return render_template("add_property.html")


@app.route("/delete_property", methods=["GET", "POST"])
@login_required
def delete_property():
    if request.method == "POST":

        id = request.form.get('property_id')
        data = db.execute("SELECT * FROM properties WHERE id = :id", id=id)
        db.execute('DELETE FROM properties WHERE id = :id', id=id)
        flash(f"'{data[0]['name']}' has been deleted successfully")
        return redirect("/properties")

    else:
        
        ls = db.execute("SELECT * FROM properties WHERE owner_id = :owner_id", owner_id=session['user_id'])
        return render_template("delete_property.html", properties=ls)


# ------------------------------------------------- Properties End ----------------------------------------------------------------
# --------------------------------------------------- Contacts --------------------------------------------------------------------

@app.route("/contacts")
@login_required
def contacts():
    ls = db.execute("SELECT * FROM contacts where owner_id = :id", id=session['user_id'])
    return render_template('contacts.html', ls=ls, subtitle='All')


@app.route("/currently_leased_contacts")
@login_required
def currently_leased_contacts():
    ls = db.execute("SELECT * FROM contacts WHERE owner_id = :owner_id and id in (SELECT contact_id FROM (SELECT contacts.id as contact_id FROM leases join contacts on leases.contact_id = contacts.id WHERE leases.owner_id = :owner_id and leases.end >= :today))", owner_id=session['user_id'], today=today())
    return render_template('contacts.html', ls=ls, subtitle='Currently Leased')


@app.route("/add_contact", methods=['GET', 'POST'])
@login_required
def add_contact():

    if request.method == "POST":
        name = request.form.get('name')
        phone = request.form.get('phone')
        db.execute("INSERT INTO contacts (name, phone, owner_id) VALUES (:name, :phone, :owner_id)", name=name, phone=phone, owner_id=session['user_id'])
        flash("Contact added succesfully")
        return redirect('/contacts')
    
    else:
        return render_template('add_contact.html')


@app.route("/delete_contact", methods=["GET", "POST"])
@login_required
def delete_contact():
    if request.method == "POST":

        id = request.form.get('contact_id')
        data = db.execute("SELECT * FROM contacts WHERE id = :id", id=id)
        db.execute('DELETE FROM contacts WHERE id = :id', id=id)
        flash(f"'{data[0]['name']}' has been deleted successfully")
        return redirect("/contacts")

    else:
        
        ls = db.execute("SELECT * FROM contacts WHERE owner_id = :owner_id", owner_id=session['user_id'])
        return render_template("delete_contact.html", contacts=ls)

# ----------------------------------------------------- Contacts End ---------------------------------------------------------------
# -------------------------------------------------------- Leases ------------------------------------------------------------------

@app.route("/leases")
@login_required
def leases():
    """TODO"""
    ls = db.execute("SELECT x.id, start, end, property_name, contacts.name as contact_name FROM (SELECT leases.id, leases.start, leases.end, contact_id, properties.name as property_name FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id) as x join contacts on x.contact_id = contacts.id", owner_id=session['user_id'])
    return render_template("/leases.html", ls=ls, subtitle='All')


@app.route("/leases_active")
@login_required
def leases_active():
    ls = db.execute("SELECT x.id, start, end, property_name, contacts.name as contact_name FROM (SELECT leases.id, leases.start, leases.end, contact_id, properties.name as property_name FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id and leases.start <= :today and leases.end >= :today) as x join contacts on x.contact_id = contacts.id", owner_id=session['user_id'], today=today())
    return render_template("/leases.html", ls=ls, subtitle='Active')


@app.route("/leases_upcoming")
@login_required
def leases_upcoming():
    ls = db.execute("SELECT x.id, start, end, property_name, contacts.name as contact_name FROM (SELECT leases.id, leases.start, leases.end, contact_id, properties.name as property_name FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id and leases.start > :today and leases.end > :today) as x join contacts on x.contact_id = contacts.id", owner_id=session['user_id'], today=today())
    return render_template("/leases.html", ls=ls, subtitle='Upcoming')


@app.route("/leases_past")
@login_required
def leases_past():
    ls = db.execute("SELECT x.id, start, end, property_name, contacts.name as contact_name FROM (SELECT leases.id, leases.start, leases.end, contact_id, properties.name as property_name FROM leases join properties on leases.property_id = properties.id WHERE leases.owner_id = :owner_id and leases.start < :today and leases.end < :today) as x join contacts on x.contact_id = contacts.id", owner_id=session['user_id'], today=today())
    return render_template("/leases.html", ls=ls, subtitle='Past')


@app.route("/add_lease", methods=['GET', 'POST'])
@login_required
def add_lease():
    if request.method == 'POST':
        property_id = request.form.get('property_id')
        contact_id = request.form.get('contact_id')
        start = request.form.get('start')
        end = request.form.get('end')
        amount = request.form.get('amount')
        due_date = request.form.get('due_date')

        if start >= end:
            return apology("Start date is after end date")

        intersects = db.execute("SELECT * FROM leases where property_id = :property_id and ((start >= :start and start <= :end) or (end >= :start and end <= :end) or (start <= :start and end >= :end)) and owner_id = :owner_id", property_id=property_id, start=start, end=end, owner_id=session['user_id'])
        if intersects:
            return apology("Sorry, this Property isn't available for the required dates, they intersect another lease.")    

        lease_id = db.execute("INSERT INTO leases (property_id, contact_id, owner_id, start, end, amount) VALUES (:property_id, :contact_id, :owner_id, :start, :end, :amount)", property_id=property_id, contact_id=contact_id, owner_id=session['user_id'], start=start, end=end, amount=amount)
        db.execute("INSERT INTO invoices (amount, due_date, lease_id, contact_id, property_id, owner_id, paid) VALUES (:amount, :due_date, :lease_id, :contact_id, :property_id, :owner_id, 0)", amount=amount, due_date=due_date, lease_id=lease_id, contact_id=contact_id, property_id=property_id, owner_id=session['user_id'])

        flash('Lease added succesfully')
        return redirect("/leases")

    else:
        """TODO"""
        properties = db.execute("SELECT id, name FROM properties WHERE owner_id = :owner_id", owner_id=session['user_id'])
        contacts = db.execute("SELECT id, name FROM contacts WHERE owner_id = :owner_id", owner_id=session['user_id'])
        return render_template("add_lease.html", properties=properties, contacts=contacts)


@app.route("/delete_lease", methods=["GET", "POST"])
@login_required
def delete_lease():
    if request.method == "POST":

        id = request.form.get('lease_id')
        data = db.execute("SELECT * FROM leases WHERE id = :id", id=id)
        db.execute('DELETE FROM leases WHERE id = :id', id=id)
        flash(f"Lease: '{data[0]['id']}' has been deleted successfully")
        return redirect("/leases")

    else:
        
        ls = db.execute("SELECT * FROM leases WHERE owner_id = :owner_id", owner_id=session['user_id'])
        return render_template("delete_lease.html", leases=ls)

# ------------------------------------------------------ Leases End ----------------------------------------------------------------
# ------------------------------------------------------ Accounting ----------------------------------------------------------------

@app.route("/invoices")
@login_required
def invoices():
    ls = db.execute("SELECT x.*, properties.name as property_name FROM (SELECT invoices.*, contacts.name as contact_name FROM invoices JOIN contacts on invoices.contact_id = contacts.id WHERE invoices.owner_id = :owner_id)as x JOIN properties on x.property_id = properties.id", owner_id=session['user_id'])
    return render_template("/invoices.html", ls=ls, subtitle='All')


@app.route("/invoices_outstanding")
@login_required
def invoices_outstanding():
    ls = db.execute("SELECT x.*, properties.name as property_name FROM (SELECT invoices.*, contacts.name as contact_name FROM invoices JOIN contacts on invoices.contact_id = contacts.id WHERE invoices.owner_id = :owner_id and invoices.due_date <= :today and invoices.paid = 0)as x JOIN properties on x.property_id = properties.id", owner_id=session['user_id'], today=today())
    return render_template("/invoices.html", ls=ls, subtitle='Outstanding')


@app.route("/invoices_open")
@login_required
def invoices_open():
    ls = db.execute("SELECT x.*, properties.name as property_name FROM (SELECT invoices.*, contacts.name as contact_name FROM invoices JOIN contacts on invoices.contact_id = contacts.id WHERE invoices.owner_id = :owner_id and invoices.paid = 0)as x JOIN properties on x.property_id = properties.id", owner_id=session['user_id'])
    return render_template("/invoices.html", ls=ls, subtitle='Open')


@app.route("/invoices_paid")
@login_required
def invoices_paid():
    ls = db.execute("SELECT x.*, properties.name as property_name FROM (SELECT invoices.*, contacts.name as contact_name FROM invoices JOIN contacts on invoices.contact_id = contacts.id WHERE invoices.owner_id = :owner_id and invoices.paid = 1)as x JOIN properties on x.property_id = properties.id", owner_id=session['user_id'])
    return render_template("/invoices.html", ls=ls, subtitle='Paid')


@app.route("/delete_invoice", methods=["GET", "POST"])
@login_required
def delete_invoice():
    if request.method == "POST":

        id = request.form.get('invoice_id')
        data = db.execute("SELECT * FROM invoices WHERE id = :id", id=id)
        db.execute('DELETE FROM invoices WHERE id = :id', id=id)
        flash(f"Invoice: '{data[0]['id']}' has been deleted successfully")
        return redirect("/invoices")

    else:
        
        ls = db.execute("SELECT * FROM invoices WHERE owner_id = :owner_id", owner_id=session['user_id'])
        return render_template("delete_invoice.html", invoices=ls)


@app.route("/receive_payment", methods=["GET", "POST"])
@login_required
def receive_payment():
    if request.method == "POST":

        id = request.form.get('invoice_id')
        db.execute('UPDATE invoices SET paid = 1 WHERE id = :id', id=id)
        flash(f"Payment for Invoice: '{id}' has been received successfully")
        return redirect("/invoices")

    else:
        
        ls = db.execute("SELECT * FROM invoices WHERE owner_id = :owner_id and paid = 0", owner_id=session['user_id'])
        return render_template("receive_payment.html", invoices=ls)

# ----------------------------------------------------  Accounting End ----------------------------------------------------------------
# ------------------------------------------------------- Functions ----------------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS