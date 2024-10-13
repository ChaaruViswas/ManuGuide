from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
import calendar
from datetime import datetime, timedelta
import plotly.graph_objs as go
from collections import deque
import time
import pyrebase
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

import spacy

# Download necessary NLTK data
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Z1Fjohz4QoT8qzsl1BIHu1k8Um1TjtEF8awUKauw'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Firebase configuration
firebaseConfig = {
    'apiKey': 'AIzaSyAiWX_Ed0G6D_7dHwFVzXnGtUQeNLD_Tds',
    'authDomain': 'ambi19-b040a.firebaseapp.com',
    'databaseURL': 'https://ambi19-b040a-default-rtdb.firebaseio.com',
    'projectId': 'ambi19-b040a',
    'storageBucket': 'ambi19-b040a.appspot.com',
    'messagingSenderId': '275342282731',
    'appId': '1:275342282731:web:1a767a8de5a7a36b8e93ae',
    'measurementId': 'G-FW11RB36TG'
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# Data storage for real-time updates
temperature_data = deque(maxlen=20)
humidity_data = deque(maxlen=20)
time_data = deque(maxlen=20)

cookie_counts = {"Good": 0, "Broken": 0, "Burnt": 0}

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

users = {
    'user@123': {'password': 'user', 'role': 'user'},
    'stake@123': {'password': 'stake', 'role': 'stakeholder'}
}

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id, users[user_id]['role'])
    return None



@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        if email in users and users[email]['password'] == password and users[email]['role'] == user_type:
            user = User(email, users[email]['role'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash(f'Invalid email or password for {user_type}')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/temperature')
@login_required
def temperature():
    temp_data = {'current': 25, 'min': 20, 'max': 30}
    return render_template('temperature.html', data=temp_data)

@app.route('/humidity')
@login_required
def humidity():
    humidity_data = {'current': 60, 'min': 40, 'max': 80}
    return render_template('humidity.html', data=humidity_data)

@app.route('/weight')
@login_required
def weight():
    weight_data = {'current': 250, 'min': 200, 'max': 300}
    return render_template('weight.html', data=weight_data)

@app.route('/status')
@login_required
def status():
    status_data = {'system': 'OK', 'sensors': 'Active', 'connection': 'Stable'}
    return render_template('status.html', data=status_data)

@app.route('/acceptance')
@login_required
def acceptance():
    acceptance_data = {'total': 100, 'accepted': 95, 'rejected': 5}
    return render_template('acceptance.html', data=acceptance_data)

@app.route('/work_orders')
@login_required
def work_orders():
    orders = [
        {'id': 1, 'product': 'Chocolate Chip Cookies', 'quantity': 1000, 'status': 'In Progress'},
        {'id': 2, 'product': 'Oatmeal Raisin Cookies', 'quantity': 500, 'status': 'Pending'},
        {'id': 3, 'product': 'Peanut Butter Cookies', 'quantity': 750, 'status': 'Completed'}
    ]
    return render_template('work_orders.html', orders=orders)

@app.route('/inventory')
@login_required
def inventory():
    inventory_items = [
        {'name': 'Flour', 'quantity': 500, 'unit': 'kg'},
        {'name': 'Sugar', 'quantity': 300, 'unit': 'kg'},
        {'name': 'Chocolate Chips', 'quantity': 100, 'unit': 'kg'},
        {'name': 'Butter', 'quantity': 200, 'unit': 'kg'}
    ]
    return render_template('inventory.html', items=inventory_items)

@app.route('/maintenance')
@login_required
def maintenance():
    current_year = datetime.now().year
    maintenance_days = generate_maintenance_schedule(current_year)
    return render_template('maintenance.html', year=current_year, maintenance_days=maintenance_days)

def generate_maintenance_schedule(year):
    maintenance_days = {}
    equipment = ['Mixer', 'Oven', 'Packaging Machine', 'Cooling Conveyor']
    for month in range(1, 13):
        _, days_in_month = calendar.monthrange(year, month)
        month_schedule = {}
        for equip in equipment:
            num_days = random.randint(1, 2)
            days = sorted(random.sample(range(1, days_in_month + 1), num_days))
            month_schedule[equip] = days
        maintenance_days[month] = month_schedule
    return maintenance_days

@app.route('/quality_check')
@login_required
def quality_check():
    return render_template('quality_check.html')

@app.route('/get_quality_data')
@login_required
def get_quality_data():
    try:
        # Fetch latest data from Firebase
        temp_data = db.child("temperature").get().val()
        humi_data = db.child("humidity").get().val()
        predicted_class = db.child("predicted_class").get().val()
        image_url = db.child("image_url").get().val()

        # Append data for graphs
        temperature_data.append(temp_data)
        humidity_data.append(humi_data)
        time_data.append(time.strftime('%H:%M:%S'))

        # Update cookie classification count
        cookie_counts[predicted_class] += 1
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        temp_data = random.uniform(20, 40)
        humi_data = random.uniform(30, 70)
        predicted_class = random.choice(['Good', 'Broken', 'Burnt'])
        image_url = ''

    # Line chart for temperature
    temp_fig = {
        'data': [go.Scatter(x=list(time_data), y=list(temperature_data), mode='lines', name='Temperature')],
        'layout': go.Layout(title='Temperature over Time', xaxis={'title': 'Time'}, yaxis={'title': 'Temperature (°C)'})
    }

    # Line chart for humidity
    humidity_fig = {
        'data': [go.Scatter(x=list(time_data), y=list(humidity_data), mode='lines', name='Humidity')],
        'layout': go.Layout(title='Humidity over Time', xaxis={'title': 'Time'}, yaxis={'title': 'Humidity (%)'})
    }

    # Bar chart for cookie counts
    cookie_fig = {
        'data': [go.Bar(x=list(cookie_counts.keys()), y=list(cookie_counts.values()))],
        'layout': go.Layout(title='Cookie Classification', xaxis={'title': 'State'}, yaxis={'title': 'Count'})
    }

    return jsonify({
        'temperature': temp_fig,
        'humidity': humidity_fig,
        'cookie_classification': cookie_fig,
        'predicted_class': predicted_class,
        'image_url': image_url
    })

@app.route('/data_visualization')
@login_required
def data_visualization():
    return render_template('data_visualization.html')

@app.route('/api/chart_data')
@login_required
def chart_data():
    labels = ['January', 'February', 'March', 'April', 'May', 'June', 'July']
    production_data = [random.randint(1000, 5000) for _ in range(7)]
    rejection_data = [random.randint(50, 200) for _ in range(7)]
    temperature_data = [random.randint(20, 30) for _ in range(7)]
    humidity_data = [random.randint(40, 80) for _ in range(7)]
    cookie_weight = [random.randint(200, 300) for _ in range(100)]
    inventory_data = [random.randint(500, 1000) for _ in range(7)]
    quality_check_values = [70, 20, 10]
    quality_check_labels = ['Pass', 'Warning', 'Fail']
    
    return jsonify({
        'labels': labels,
        'production': production_data,
        'rejection': rejection_data,
        'temperature': temperature_data,
        'humidity': humidity_data,
        'cookie_weight': cookie_weight,
        'inventory': inventory_data,
        'quality_check_values': quality_check_values,
        'quality_check_labels': quality_check_labels,
        'system_status': 'OK',
        'sensor_status': 'Active',
        'connection_status': 'Stable',
        'production_rate': '95%',
        'maintenance_due': '3 days',
        'alert_status': 'None'
    })

@app.template_filter('month_name')
def month_name_filter(month_number):
    return calendar.month_name[month_number]

@app.template_filter('month_calendar')
def month_calendar_filter(month_number, year):
    cal = calendar.monthcalendar(year, month_number)
    return cal

temperature_data = {'current': 25, 'min': 20, 'max': 30}
humidity_data = {'current': 60, 'min': 40, 'max': 80}
weight_data = {'current': 250, 'min': 200, 'max': 300}
status_data = {'system': 'OK', 'sensors': 'Active', 'connection': 'Stable'}
acceptance_data = {'total': 100, 'accepted': 95, 'rejected': 5}
inventory_items = [
    {'name': 'Flour', 'quantity': 500, 'unit': 'kg'},
    {'name': 'Sugar', 'quantity': 300, 'unit': 'kg'},
    {'name': 'Chocolate Chips', 'quantity': 100, 'unit': 'kg'},
    {'name': 'Butter', 'quantity': 200, 'unit': 'kg'}
]
work_orders = [
    {'id': 1, 'product': 'Chocolate Chip Cookies', 'quantity': 1000, 'status': 'In Progress'},
    {'id': 2, 'product': 'Oatmeal Raisin Cookies', 'quantity': 500, 'status': 'Pending'},
    {'id': 3, 'product': 'Peanut Butter Cookies', 'quantity': 750, 'status': 'Completed'}
]

nlp = spacy.load("en_core_web_sm")

def preprocess_text(text):
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return tokens

def analyze_query(tokens):
    query_set = set(tokens)
    
    if query_set.intersection({'temperature', 'temp'}):
        return f"The current temperature is {temperature_data['current']}°C, with a minimum of {temperature_data['min']}°C and a maximum of {temperature_data['max']}°C."
    elif query_set.intersection({'humidity', 'humid'}):
        return f"The current humidity is {humidity_data['current']}%, with a minimum of {humidity_data['min']}% and a maximum of {humidity_data['max']}%."
    elif query_set.intersection({'weight', 'mass'}):
        return f"The current weight is {weight_data['current']}g, with a minimum of {weight_data['min']}g and a maximum of {weight_data['max']}g."
    elif 'status' in query_set:
        return f"System status: {status_data['system']}, Sensors: {status_data['sensors']}, Connection: {status_data['connection']}."
    elif query_set.intersection({'acceptance', 'reject', 'accept'}):
        return f"Total products: {acceptance_data['total']}, Accepted: {acceptance_data['accepted']}, Rejected: {acceptance_data['rejected']}."
    elif 'inventory' in query_set:
        inventory_summary = ", ".join([f"{item['name']}: {item['quantity']} {item['unit']}" for item in inventory_items])
        return f"Current inventory: {inventory_summary}"
    elif query_set.intersection({'order', 'work'}):
        orders_summary = ", ".join([f"{order['product']}: {order['quantity']} ({order['status']})" for order in work_orders])
        return f"Current work orders: {orders_summary}"
    elif {'total', 'cookie'}.issubset(query_set) or {'total', 'biscuit'}.issubset(query_set):
        return f"Total products: {acceptance_data['total']}"
    elif {'accepted', 'cookie'}.issubset(query_set) or {'accepted', 'biscuit'}.issubset(query_set):
        return f"Accepted products: {acceptance_data['accepted']}"
    elif {'rejected', 'cookie'}.issubset(query_set) or {'rejected', 'biscuit'}.issubset(query_set):
        return f"Rejected products: {acceptance_data['rejected']}"
    else:
        return "I'm sorry, I don't have information about that. Can you please ask about temperature, humidity, weight, status, acceptance, inventory, or work orders?"

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.json
        user_message = data['message']
        
        tokens = preprocess_text(user_message)
        response = analyze_query(tokens)
        
        return jsonify({'response': response})
    except Exception as e:
        app.logger.error(f"Error in chatbot: {str(e)}")
        return jsonify({'response': "I'm sorry, I encountered an error. Please try again later."}), 500

if __name__ == '__main__':
    app.run(debug=True)