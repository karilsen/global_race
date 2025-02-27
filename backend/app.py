from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from flask_cors import CORS
import random
import uuid
from shapely.geometry import Point, LineString
from math import radians, cos, sin, sqrt, atan2

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///global_race.db'
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

locations = [
    {"name": "Eiffel Tower", "latitude": 48.8584, "longitude": 2.2945},
    {"name": "Statue of Liberty", "latitude": 40.6892, "longitude": -74.0445},
    {"name": "Great Wall of China", "latitude": 40.4319, "longitude": 116.5704},
    {"name": "Sydney Opera House", "latitude": -33.8568, "longitude": 151.2153},
    {"name": "Skånland Båtlag", "latitude": 68.58404, "longitude": 16.56120},
    {"name": "Taj Mahal", "latitude": 27.1751, "longitude": 78.0421},
    {"name": "Machu Picchu", "latitude": -13.1631, "longitude": -72.5450},
    {"name": "Colosseum", "latitude": 41.8902, "longitude": 12.4922},
    {"name": "Pyramids of Giza", "latitude": 29.9792, "longitude": 31.1342},
    {"name": "Big Ben", "latitude": 51.5007, "longitude": -0.1246},
    {"name": "Mount Everest", "latitude": 27.9881, "longitude": 86.9250},
    {"name": "Niagara Falls", "latitude": 43.0896, "longitude": -79.0849},
    {"name": "Tokyo Tower", "latitude": 35.6586, "longitude": 139.7454},
    {"name": "Christ the Redeemer", "latitude": -22.9519, "longitude": -43.2105},
    {"name": "Burj Khalifa", "latitude": 25.1972, "longitude": 55.2744},
    {"name": "Angkor Wat", "latitude": 13.4125, "longitude": 103.8670},
    {"name": "The Louvre", "latitude": 48.8606, "longitude": 2.3376},
    {"name": "Golden Gate Bridge", "latitude": 37.8199, "longitude": -122.4783},
    {"name": "Victoria Falls", "latitude": -17.9246, "longitude": 25.8573},
    {"name": "The Vatican City", "latitude": 41.9029, "longitude": 12.4534},
    {"name": "Stonehenge", "latitude": 51.1789, "longitude": -1.8262},
    {"name": "The Blue Lagoon", "latitude": 63.8804, "longitude": -22.4503},
    {"name": "Hollywood Sign", "latitude": 34.1341, "longitude": -118.3217}
]




# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    traveler_id = db.Column(db.String(50), unique=True, default=lambda: str(uuid.uuid4()))

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

# Initialize Database
with app.app_context():
    db.create_all()

    # Pre-populate tasks only if the database is empty
    if not Task.query.first():
        for loc in locations:  # ✅ Use the existing `locations` list
            db.session.add(Task(location_name=loc["name"], latitude=loc["latitude"], longitude=loc["longitude"]))
        db.session.commit()
        print(f"{len(locations)} locations added to the database as tasks.")


# User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400
    
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password_hash=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully", "traveler_id": new_user.traveler_id})

# User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({"message": "Login successful", "access_token": access_token, "traveler_id": user.traveler_id})
    return jsonify({"message": "Invalid credentials"}), 401

# Get Random Task
@app.route('/get_task', methods=['GET'])
def get_task():
    task = random.choice(Task.query.all())
    return jsonify({
        "location_name": task.location_name,
        "latitude": task.latitude,
        "longitude": task.longitude
    })

# Nearest Point Calculation
@app.route('/nearest-point', methods=['POST'])
def nearest_point():
    try:
        data = request.json
        point = Point(data["lon"], data["lat"])
        line = LineString(data["line_coords"])
        nearest = line.interpolate(line.project(point))
        return jsonify({"nearest_lat": nearest.y, "nearest_lon": nearest.x})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/locations", methods=["GET"])
def get_locations():
    return jsonify(locations)


@app.route("/check-task", methods=["POST"])
def check_task():
    try:
        data = request.json
        player_lat = data.get("latitude")
        player_lon = data.get("longitude")
        task_name = data.get("task_name")

        task = Task.query.filter_by(location_name=task_name).first()
        if not task:
            return jsonify({"success": False, "message": "Task not found"}), 404

        distance = haversine(player_lat, player_lon, task.latitude, task.longitude)

        if distance < 1:  # ✅ Players must be within 1 km
            return jsonify({"success": True, "message": f"Task completed! You were {distance:.2f} km away."})
        else:
            return jsonify({"success": False, "message": f"Not close enough. You are {distance:.2f} km away. Keep searching!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Distance in km



if __name__ == '__main__':
    app.run(debug=True)
