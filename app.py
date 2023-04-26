from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
import plotly.express as px

from datetime import datetime
import psutil

app = Flask(__name__) # Create instance and setting URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main_sample.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Set True for debug
db = SQLAlchemy(app) # Initialize SQLAlchemy instance with Flask app

def server_header():
    # server uptime
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    # recent queries from the request context
    queries = getattr(request, 'query_count', None) #TODO!

    return {'uptime': uptime, 'queries': queries}

# -------------------------------------------------------------------------- #

# TODO: Login details here

# -------------------------------------------------------------------------- #

# Get the server uptime and recent queries on site header
def server_header():
    # server uptime
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    # recent queries from the request context
    queries = getattr(request, 'query_count', None)

    return {'uptime': uptime, 'queries': queries}

# Register the function as a context processor
@app.context_processor
def inject_header():
    return server_header()

# Create deafult db and define columns for User
class User(db.Model):
    __tablename__ = 'user'
    index = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))

# Default route, render user table and plot at home.html
# !! This has been moved to @app.route('/custom_table) !!
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/custom_table', methods=['GET'])
def custom_table():
    users = User.query.all()

    # Simple plot to test embedding with JS
    ages = [user.age for user in users]
    fig = px.histogram(x=ages, nbins=len(set(ages)), color_discrete_sequence=['#1693a9'])
    fig.update_layout(width=600, height=400)
    fig.update_xaxes(title_text='Age category')
    fig.update_yaxes(title=None)
    graphJSON = fig.to_json()

    return render_template('custom_table.html', users=users, graphJSON=graphJSON)

# Allow new User object with POST, or render the add.html with GET
@app.route('/add', methods=['GET', 'POST'])
def add():

    # Extract data from form and create new User object 
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        age = request.form['age']
        user = User(name=name, email=email, age=age)
        db.session.add(user)
        db.session.commit()

        # Redirect back to the home page
        return redirect(url_for('home'))

    # Render add.html template if GET request is made
    return render_template('add.html')

# Allow editing existing User object with POST, or render the edit.html with GET
@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):

    # Query for the User object with the specified index
    user = User.query.get_or_404(index)
    if request.method == 'POST':

        # Update User object with the new data from the form
        user.name = request.form['name']
        user.email = request.form['email']
        user.age = request.form['age']
        db.session.commit()

        # Redirect back to the home page
        return redirect(url_for('home'))

    # Render edit.html template if GET request is made
    return render_template('edit.html', user=user)

# Allow deleting existing User object with POST request
@app.route('/delete/<int:index>', methods=['GET', 'POST'])
def delete(index):
    user = User.query.get_or_404(index)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/import', methods=['GET'])
def import_page():
    return render_template('import.html')


# Allow importing existing database
@app.route('/import', methods=['GET', 'POST'])
def import_db():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'database_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['database_file']
        
        # If the user does not select a file, browser may
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Do whatever you need to do with the uploaded file
            # For example, replace the existing database with the uploaded file:
            db_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            existing_db_path = '/path/to/existing/database.db'
            os.replace(db_path, existing_db_path)
            
            flash('File successfully uploaded')
            return redirect(url_for('home'))
        
    # Display the form to upload a file
    return render_template('import.html')

if __name__ == '__main__':

    # Creating all database tables if not exist
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)