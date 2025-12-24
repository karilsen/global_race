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
    {"name": "Hollywood Sign", "latitude": 34.1341, "longitude": -118.3217},
    {"name": "Great Barrier Reef", "latitude": -18.2871, "longitude": 147.7017},
    {"name": "Mount Kilimanjaro", "latitude": -3.0674, "longitude": 37.3541},
    {"name": "Sagrada Familia", "latitude": 41.4036, "longitude": 2.1744},
    {"name": "The Kremlin", "latitude": 55.7520, "longitude": 37.6175},
    {"name": "Forbidden City", "latitude": 39.9166, "longitude": 116.3904},
    {"name": "Acropolis of Athens", "latitude": 37.9715, "longitude": 23.7262},
    {"name": "Easter Island", "latitude": -27.1121, "longitude": -109.3490},
    {"name": "Grand Canyon", "latitude": 36.1069, "longitude": -112.1129},
    {"name": "Dead Sea", "latitude": 31.5583, "longitude": 35.4967},
    {"name": "The Alhambra", "latitude": 37.1764, "longitude": -3.5881},
    {"name": "Edinburgh Castle", "latitude": 55.9487, "longitude": -3.1999},
    {"name": "Neuschwanstein Castle", "latitude": 47.5576, "longitude": 10.7498},
    {"name": "Mesa Verde National Park", "latitude": 37.1811, "longitude": -108.4878},
    {"name": "Uluru (Ayers Rock)", "latitude": -25.3446, "longitude": 131.0369},
    {"name": "The Matterhorn", "latitude": 45.9765, "longitude": 7.6585},
    {"name": "Hagia Sophia", "latitude": 41.0086, "longitude": 28.9802},
    {"name": "The Hermitage Museum", "latitude": 59.9399, "longitude": 30.3118},
    {"name": "Giant's Causeway", "latitude": 55.2404, "longitude": -6.5209},
    {"name": "The Great Sphinx of Giza", "latitude": 29.9754, "longitude": 31.1376},
    {"name": "The Moai Statues", "latitude": -27.1218, "longitude": -109.3663},
    {"name": "The Blue Mosque", "latitude": 41.0055, "longitude": 28.9769},
    {"name": "The Trevi Fountain", "latitude": 41.9009, "longitude": 12.4833},
    {"name": "The Spanish Steps", "latitude": 41.9054, "longitude": 12.4828},
    {"name": "The Brandenburg Gate", "latitude": 52.5162, "longitude": 13.3777},
    {"name": "The Atomium", "latitude": 50.8949, "longitude": 4.3413},
    {"name": "The Petronas Towers", "latitude": 3.1579, "longitude": 101.7118},
    {"name": "The CN Tower", "latitude": 43.6426, "longitude": -79.3871},
    {"name": "The Space Needle", "latitude": 47.6205, "longitude": -122.3493},
    {"name": "The Rock of Gibraltar", "latitude": 36.1433, "longitude": -5.3535}
]




# User Model
# User Model (Now only stores nickname, score, and correct locations)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    total_score = db.Column(db.Integer, default=0)
    correct_locations = db.Column(db.Integer, default=0)


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
    nickname = data.get('nickname')

    if not nickname:
        return jsonify({"message": "Nickname is required"}), 400

    existing_user = User.query.filter_by(nickname=nickname).first()
    if existing_user:
        return jsonify({"message": "Nickname already taken"}), 400

    new_user = User(nickname=nickname)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Registration successful",
        "nickname": new_user.nickname
    })


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


@app.route('/update-score', methods=['POST'])
def update_score():
    data = request.json
    nickname = data.get('nickname')
    points = data.get('points', 0)
    bonus_points = data.get('bonus_points', 0)
    correct_location = data.get('correct')

    try:
        points = int(points)
        bonus_points = int(bonus_points)
    except (TypeError, ValueError):
        return jsonify({"message": "Points and bonus_points must be numbers"}), 400

    user = User.query.filter_by(nickname=nickname).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.total_score += points + bonus_points
    if correct_location:
        user.correct_locations += 1

    db.session.commit()
    return jsonify({
        "message": "Score updated successfully",
        "total_score": user.total_score,
        "correct_locations": user.correct_locations,
        "applied_points": points,
        "applied_bonus_points": bonus_points
    })

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    users = User.query.order_by(User.total_score.desc()).limit(10).all()
    leaderboard_data = [
        {"nickname": user.nickname, "total_score": user.total_score, "correct_locations": user.correct_locations}
        for user in users
    ]
    return jsonify(leaderboard_data)



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

        success = distance < 100  # Players must be within 100 km
        bonus_points = 50 if distance <= 10 else 0

        if success:
            response = {
                "success": True,
                "message": f"Task completed! You were {distance:.2f} km away.",
                "distance_km": round(distance, 2),
                "bonus_points": bonus_points
            }
            if bonus_points:
                response["message"] += f" Bonus awarded: {bonus_points} points for being within 10 km."
            return jsonify(response)

        return jsonify({
            "success": False,
            "message": f"Not close enough. You are {distance:.2f} km away. Keep searching!",
            "distance_km": round(distance, 2),
            "bonus_points": 0
        })

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
    app.run(debug=False)
