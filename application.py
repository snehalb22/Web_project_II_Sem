import os
import pathlib
import requests
from flask import Flask, url_for, redirect, request, flash, session
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_manager, login_user, login_required, LoginManager, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from datetime import datetime
from werkzeug.utils import secure_filename
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from flask_migrate import Migrate
import google.auth.transport.requests


UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
SECRET_KEY = os.urandom(32)
application = app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = SECRET_KEY

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# ----------------------------------------------------------------------------------

# --------------------------------> Table to store products


class ProductsInfo(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer)
    #link = db.Column(db.String(200), nullable=False)
    dateaddes = db.Column(db.DateTime, default=datetime.utcnow)
    imageName = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Task : {self.id}>'


# -----------------------> Table containing details of users
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False, unique=True)
    mobile = db.Column(db.String(20), nullable=False, unique=True)
    address = db.Column(db.String(90))

# -----------------------> Table containing details of orders



class Orders(db.Model):
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1),primary_key=True)
    bookName=db.Column(db.String(40),nullable=True)
    userName=db.Column(db.String(40),nullable=True)
    orderDate = db.Column(db.DateTime, default=datetime.utcnow)
    userId = db.Column(db.String(20), nullable=True)
    


# -------------------------> User Registration Form
class RegsiterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    email = EmailField(validators=[InputRequired(), Length(
        min=4, max=40)], render_kw={"placeholder": "Email"})
    mobile = StringField(validators=[InputRequired(), Length(
        min=10, max=15)], render_kw={"placeholder": "Mobile no."})
    address = StringField(validators=[InputRequired(), Length(
        min=10, max=100)], render_kw={"placeholder": "Address"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    password2 = PasswordField(validators=[InputRequired(), ],
                              render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField("Register")

    def validate_user(self, username, email, mobile):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'User already exists. Please choose a different username.')

        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError(
                'User already exists. Please choose a different email.')

        existing_user_mobile = User.query.filter_by(mobile=mobile.data).first()
        if existing_user_mobile:
            raise ValidationError(
                'User already exists. Please choose a different mobile number.')


# -------------------------------> User Login Form
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


# ------------------------------> For admin to view the products and delete them
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------------------> Admin Homepage
@app.route('/admin', methods=['GET', 'POST'])
def adminHome():
    if 'username' in session and session['username'] == 'admin':
        # --------------> For admin to add new product
        if request.method == 'POST':
            image = request.files['productImage']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            newItem = ProductsInfo(
                name=request.form['productName'],
                author=request.form['productAuthor'],
                description=request.form['productDescription'],
                price=request.form['productPrice'],
                #link=request.form['productLink'],
                imageName=image.filename
            )
            try:
                session['productName'] = request.form['productName']
                db.session.add(newItem)
                db.session.commit()
                flash(f'Product added successfully', 'success')
                return redirect('/admin')
            except:
                return "There was an issue pushing to database"

        # --------------------> For admin to display all the stored products
        else:
            products = ProductsInfo.query.order_by(ProductsInfo.name).all()
            return render_template('Admin/adminPanel.html', products=products)
    else:
        return render_template('Error.html', title='Access Denied', msg="Unable to access admin Homepage. Please signin to continue.")


# -----------------------> For admin to delete a product
@app.route('/delete/<int:id>')
def deleteProduct(id):
    if 'username' in session and session['username'] == 'admin':
        print(id)
        toDelete = ProductsInfo.query.get_or_404(id)
        try:
            db.session.delete(toDelete)
            db.session.commit()
            flash(f'Product deleted', 'danger')
            return redirect('/admin')
        except:
            return "Some error occured while deleting the file"
    else:
        return render_template('Error.html', title="Access Denied!", msg="You need admin priviledges to perform this action!")


# ---------------------------> Function to autofill the details into the update form
@app.route('/update/<int:id>', methods=['GET'])
def updateProduct(id):
    if request.method == 'GET':
        if 'username' in session and session['username'] == 'admin':
            print(id)
            toUpdate = ProductsInfo.query.get_or_404(id)
            print(toUpdate.description)
            return render_template('Admin/update.html', toUpdate=toUpdate, product_id=id)
        else:
            return render_template('Error.html', title="Access Denied!", msg="You need admin priviledges to perform this action!")


# --------------------------> For admin to update the product details
@app.route('/updateproduct', methods=['POST'])
def UpdateProducts():
    if 'username' in session and session['username'] == 'admin':

        name = request.form['productName']
        author = request.form['productAuthor']
        description = request.form['productDescription']
        price = request.form['productPrice']
        #link = request.form['productLink']
        image = request.files['productImage']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            image = image.filename
            db.session.query(ProductsInfo).filter(ProductsInfo.id == request.form['product_id']).update(
                {'name': name, 'author': author, 'description': description, 'price': price, 'imageName': image})
            db.session.commit()
            flash(f'Product updated successfully', 'success')

        else:
            db.session.query(ProductsInfo).filter(ProductsInfo.id == request.form['product_id']).update(
                {'name': name, 'author': author, 'description': description, 'price': price, })
            db.session.commit()
            flash(f'Product updated successfully', 'success')

        return redirect('/admin')
    else:

        return render_template('Error.html', title="Access Denied!", msg="You need admin priviledges to perform this action!")


# --------------------------> Enter order details
@app.route('/ordersDetails', methods=['POST'])
def orderDetails():

    user = session['username']

    print("Hi")
    productId = request.form['productId']
    productName = request.form['productName']
    print(productId)
    print(productName)
    print(user)
    #userResult = User.query.filter(User.username == user).first()
    #print(userResult.id)

    db.session.add(Orders(bookName=productName,userName=user))
    db.session.commit()

    return redirect('/')


# -------------------------> User Homepage
@app.route('/')
def home():
    allProducts = []
    # Adding a username in session with value if doesn't exists any.
    if 'username' not in session:
        session['username'] = 'None'
        session['logged_in'] = False

    try:
        allProducts = ProductsInfo.query.all()
    except:
        pass
    return render_template('home.html', allProducts=allProducts)


# -----------------------------> For logging in admin and normal users
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Adding a username in session with value if doesn't exists any.
    if 'username' not in session:
        session['username'] = 'None'
        session['logged_in'] = False

    form = LoginForm()
    # For admin
    if form.username.data and form.username.data == 'admin':
        if form.password.data == 'admin':
            session['username'] = request.form['username']
            session['logged_in'] = True
            return redirect('/admin')
        else:
            flash(f'Your credentials did not match. Please try again', 'danger')
            return redirect('/login')

    # For normal user
    else:
        if form.validate_on_submit():
            username = User.query.filter_by(
                username=form.username.data).first()
            if username:
                if bcrypt.check_password_hash(username.password, form.password.data):
                    session['username'] = request.form['username']
                    session['logged_in'] = True
                    login_user(username)
                    return redirect('/')
                else:
                    flash(f'Your credentials did not match. Please try again', 'danger')
                    return redirect(url_for('login'))
            else:
                flash(f'Your credentials did not match. Please try again', 'danger')
                return redirect(url_for('login'))
        return render_template('login.html', form=form)


# ---------------------------------> For Logging Out Users
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    session['username'] = 'None'
    session['logged_in'] = False

    return redirect(url_for('login'))

# -----------------------------------> For signing up a user


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegsiterForm()
    if form.validate_on_submit():
        if (form.username.data).lower() == 'admin' or (form.username.data).lower() == 'none':
            flash(f'Username not allowed. Please any other username.', 'danger')
            return redirect(url_for('signup'))
        elif (form.password.data != form.password2.data):
            flash(f'Password mismatch.', 'danger')

        else:
            try:
                hashed_password = bcrypt.generate_password_hash(
                    form.password.data, 12)
                new_user = User(username=form.username.data, password=hashed_password,
                                email=form.email.data, mobile=form.mobile.data,address=form.address.data)
                db.session.add(new_user)
                db.session.commit()
                flash(f'You have signed up successfully. Please login now.', 'success')
                return redirect(url_for('login'))
            except:
                # return render_template('Error.html', title="Integrity Voilation")
                flash(f'User with same details already exists.', 'danger')
                return redirect(url_for('signup'))

    return render_template('register.html', form=form)


# ----------------------------------------> Buying a book
@app.route('/order/<int:productid>')
def order(productid):
    if 'username' in session and session['username'] != 'None':
        try:
            productDetails = ProductsInfo.query.get_or_404(productid)
            print(productDetails.imageName)
            return render_template('order.html', productDetails=productDetails)
        except:
            #!!! Product not found Warning must show up
            return redirect('/')
    else:
        flash(f'To buy, you need to be signed up!', 'danger')
        return redirect('/login')
#----------------------------------------> google login

app.secret_key = "GeekyHuman.com"  #it is necessary to set a password when dealing with OAuth 2.0
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  #this is to set our environment to https because OAuth 2.0 only supports https environments

GOOGLE_CLIENT_ID = "852834445383-k8goc9sjktjuldrq1ic7roa1ifgki1hl.apps.googleusercontent.com"  #enter your client id you got from Google console
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")  #set the path to where the .json file you got Google console is

flow = Flow.from_client_secrets_file(  #Flow is OAuth 2.0 a class that stores all the information on how we want to authorize our users
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],  #here we are specifing what do we get after the authorization
    redirect_uri="http://flaskwebappbook.pythonanywhere.com/callback"  #and the redirect URI is the point where the user will end up after the authorization
)

def login_is_required(function):  #a function to check if the user is authorized or not
    def wrapper(*args, **kwargs):
        if "google_id" not in session:  #authorization required
            return abort(401)
        else:
            return function()

    return wrapper


@app.route("/google_login")  #the page where the user can login
def google_login():
    authorization_url, state = flow.authorization_url()  #asking the flow class for the authorization (login) url
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")  #this is the page that will handle the callback process meaning process after the authorization
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  #state does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    

    session["google_id"] = id_info.get("sub")  #defing the results to show on the page
    session['username'] = id_info.get("name")
    session['logged_in'] = True


    return redirect("/")  #the final page where the authorized users will end up








def getApp():
    return app


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)
