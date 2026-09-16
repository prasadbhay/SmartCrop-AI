from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import tempfile

from ultralytics import YOLO

from backend.auth import (
    login_user,
    create_users_table,
    create_default_users,
    create_user,
    get_all_users
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE = os.path.join(
    BASE_DIR,
    "smartcrop.db"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "runs",
    "classify",
    "potato_health_model_v2",
    "weights",
    "best.pt"
)


# =========================================================
# USER DATABASE SETUP
# =========================================================

create_users_table()
create_default_users()


# =========================================================
# LOAD AI MODEL
# =========================================================

model = YOLO(MODEL_PATH)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "message": "SmartCrop AI Backend is running"
    })


# =========================================================
# SYSTEM STATUS
# =========================================================

@app.route("/api/status")
def status():

    return jsonify({
        "system": "SmartCrop AI",
        "backend": "online",
        "ai": "ready",
        "iot": "ready",
        "spraying": "ready"
    })


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.json or {}

        username = data.get(
            "username",
            ""
        ).strip()

        password = data.get(
            "password",
            ""
        )

        if not username or not password:

            return jsonify({
                "status": "error",
                "message": "Username and password are required."
            }), 400

        user = login_user(
            username,
            password
        )

        if user is None:

            return jsonify({
                "status": "error",
                "message": "Invalid username or password."
            }), 401

        return jsonify({
            "status": "success",
            "message": "Login successful.",
            "user": user
        })

    except Exception as error:

        print(
            "Login error:",
            error
        )

        return jsonify({
            "status": "error",
            "message": "Login failed."
        }), 500


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(username):

    if not username:
        return False

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT role
        FROM users
        WHERE username = ?
    """, (
        username,
    ))

    user = cursor.fetchone()

    connection.close()

    if user is None:
        return False

    return user[0] == "admin"


# =========================================================
# ADMIN - GET ALL USERS
# =========================================================

@app.route("/api/users", methods=["GET"])
def users():

    try:

        admin_username = request.args.get(
            "admin_username",
            ""
        ).strip()

        if not is_admin(admin_username):

            return jsonify({
                "status": "error",
                "message": "Admin access required."
            }), 403

        user_list = get_all_users()

        return jsonify({
            "status": "success",
            "users": user_list
        })

    except Exception as error:

        print(
            "Get users error:",
            error
        )

        return jsonify({
            "status": "error",
            "message": "Unable to load users."
        }), 500


# =========================================================
# ADMIN - CREATE NEW USER
# =========================================================

@app.route("/api/users/create", methods=["POST"])
def create_new_user():

    try:

        data = request.json or {}

        admin_username = data.get(
            "admin_username",
            ""
        ).strip()

        name = data.get(
            "name",
            ""
        ).strip()

        username = data.get(
            "username",
            ""
        ).strip()

        password = data.get(
            "password",
            ""
        )

        role = data.get(
            "role",
            "user"
        ).strip().lower()


        # -------------------------------------------------
        # ADMIN VERIFICATION
        # -------------------------------------------------

        if not is_admin(admin_username):

            return jsonify({
                "status": "error",
                "message": "Only Admin can create new users."
            }), 403


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name:

            return jsonify({
                "status": "error",
                "message": "Name is required."
            }), 400


        if not username:

            return jsonify({
                "status": "error",
                "message": "Username is required."
            }), 400


        if not password:

            return jsonify({
                "status": "error",
                "message": "Password is required."
            }), 400


        if len(username) < 3:

            return jsonify({
                "status": "error",
                "message": "Username must contain at least 3 characters."
            }), 400


        if len(password) < 4:

            return jsonify({
                "status": "error",
                "message": "Password must contain at least 4 characters."
            }), 400


        if role not in [
            "admin",
            "user"
        ]:

            return jsonify({
                "status": "error",
                "message": "Invalid user role."
            }), 400


        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        result = create_user(
            username,
            password,
            name,
            role
        )


        # IMPORTANT:
        # auth.py returns "success": True/False

        if result.get("success") != True:

            return jsonify({
                "status": "error",
                "message": result.get(
                    "message",
                    "Unable to create user."
                )
            }), 400


        return jsonify({
            "status": "success",
            "message": "New user created successfully.",
            "user": result.get("user")
        }), 201


    except Exception as error:

        print(
            "Create user error:",
            error
        )

        return jsonify({
            "status": "error",
            "message": "Unable to create user."
        }), 500


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/api/dashboard")
def dashboard():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        SELECT COUNT(*)
        FROM detections
    """)

    total_scanned = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM detections
        WHERE result = 'Healthy'
    """)

    healthy = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM detections
        WHERE result = 'Diseased / Defected'
    """)

    diseased = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM detections
        WHERE spray_required = 'Yes'
    """)

    spray_operations = cursor.fetchone()[0]


    connection.close()


    return jsonify({
        "total_scanned": total_scanned,
        "healthy": healthy,
        "diseased": diseased,
        "spray_operations": spray_operations
    })


# =========================================================
# DETECTION HISTORY
# =========================================================

@app.route("/api/detections")
def get_detections():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM detections
        ORDER BY id DESC
    """)


    detections = [
        dict(row)
        for row in cursor.fetchall()
    ]


    connection.close()


    return jsonify(
        detections
    )


# =========================================================
# SAVE DETECTION
# =========================================================

@app.route(
    "/api/detections",
    methods=["POST"]
)
def add_detection():

    try:

        data = request.json or {}


        connection = sqlite3.connect(
            DATABASE
        )

        cursor = connection.cursor()


        cursor.execute("""
            INSERT INTO detections
            (
                plant_id,
                result,
                confidence,
                spray_required
            )
            VALUES (?, ?, ?, ?)
        """, (
            data["plant_id"],
            data["result"],
            data["confidence"],
            data["spray_required"]
        ))


        connection.commit()

        connection.close()


        return jsonify({
            "status": "success",
            "message": "Detection saved successfully"
        })


    except Exception as error:

        print(
            "Detection save error:",
            error
        )


        return jsonify({
            "status": "error",
            "message": "Unable to save detection."
        }), 500


# =========================================================
# REAL AI CROP PREDICTION
# =========================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict_crop():

    temp_path = None


    try:

        if "image" not in request.files:

            return jsonify({
                "status": "error",
                "message": "No image uploaded"
            }), 400


        image = request.files["image"]


        if image.filename == "":

            return jsonify({
                "status": "error",
                "message": "Invalid image"
            }), 400


        temp_file = tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False
        )


        temp_path = temp_file.name

        temp_file.close()


        image.save(
            temp_path
        )


        results = model.predict(
            source=temp_path,
            verbose=False
        )


        prediction = results[0].probs


        top_class = int(
            prediction.top1
        )


        confidence = float(
            prediction.top1conf.item()
            * 100
        )


        class_name = results[0].names[
            top_class
        ]


        if class_name.lower() == "healthy":

            detection_result = "Healthy"

            spray_required = "No"

        else:

            detection_result = "Diseased / Defected"

            spray_required = "Yes"


        # -------------------------------------------------
        # CREATE PLANT ID
        # -------------------------------------------------

        connection = sqlite3.connect(
            DATABASE
        )

        cursor = connection.cursor()


        cursor.execute("""
            SELECT COUNT(*)
            FROM detections
        """)


        count = (
            cursor.fetchone()[0]
            + 1
        )


        connection.close()


        plant_id = f"P-{count:03d}"


        # -------------------------------------------------
        # SAVE DETECTION
        # -------------------------------------------------

        connection = sqlite3.connect(
            DATABASE
        )

        cursor = connection.cursor()


        cursor.execute("""
            INSERT INTO detections
            (
                plant_id,
                result,
                confidence,
                spray_required
            )
            VALUES (?, ?, ?, ?)
        """, (
            plant_id,
            detection_result,
            round(
                confidence,
                2
            ),
            spray_required
        ))


        connection.commit()

        connection.close()


        return jsonify({

            "status": "success",

            "plant_id": plant_id,

            "result": detection_result,

            "confidence": round(
                confidence,
                2
            ),

            "spray_required": spray_required

        })


    except Exception as error:

        print(
            "AI prediction error:",
            error
        )


        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:

                os.remove(
                    temp_path
                )

            except Exception:

                pass


# =========================================================
# FARMER COPILOT
# =========================================================

@app.route(
    "/api/copilot",
    methods=["POST"]
)
def copilot():

    try:

        data = request.json or {}


        question = data.get(
            "question",
            ""
        ).strip().lower()


        if not question:

            return jsonify({
                "status": "error",
                "message": "Please enter a question"
            }), 400


        connection = sqlite3.connect(
            DATABASE
        )

        cursor = connection.cursor()


        # -------------------------------------------------
        # TOTAL
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM detections
        """)

        total = cursor.fetchone()[0]


        # -------------------------------------------------
        # HEALTHY
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM detections
            WHERE result = 'Healthy'
        """)

        healthy = cursor.fetchone()[0]


        # -------------------------------------------------
        # DISEASED
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM detections
            WHERE result = 'Diseased / Defected'
        """)

        diseased = cursor.fetchone()[0]


        # -------------------------------------------------
        # SPRAY
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM detections
            WHERE spray_required = 'Yes'
        """)

        spray = cursor.fetchone()[0]


        # -------------------------------------------------
        # LATEST DETECTION
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                plant_id,
                result,
                confidence,
                spray_required,
                created_at
            FROM detections
            ORDER BY id DESC
            LIMIT 1
        """)


        latest = cursor.fetchone()


        connection.close()


        # -------------------------------------------------
        # DISEASED
        # -------------------------------------------------

        if (
            "diseased" in question
            or "disease" in question
            or "affected" in question
        ):

            answer = (
                f"🦠 SmartCrop मध्ये आत्तापर्यंत "
                f"<b>{diseased}</b> diseased/affected "
                f"plants detect झाले आहेत."
            )


        # -------------------------------------------------
        # HEALTHY
        # -------------------------------------------------

        elif "healthy" in question:

            answer = (
                f"🟢 SmartCrop मध्ये आत्तापर्यंत "
                f"<b>{healthy}</b> healthy plants "
                f"detect झाले आहेत."
            )


        # -------------------------------------------------
        # SPRAY
        # -------------------------------------------------

        elif "spray" in question:

            answer = (
                f"💦 SmartCrop data नुसार "
                f"<b>{spray}</b> plants साठी "
                f"targeted spraying required mark केले आहे."
            )


        # -------------------------------------------------
        # FIELD REPORT
        # -------------------------------------------------

        elif (
            "report" in question
            or "field condition" in question
            or "field status" in question
            or "condition" in question
        ):

            answer = (
                f"🌾 <b>SmartCrop Field Report</b><br><br>"
                f"🌱 Total Scanned: <b>{total}</b><br>"
                f"🟢 Healthy: <b>{healthy}</b><br>"
                f"🔴 Diseased: <b>{diseased}</b><br>"
                f"💦 Spray Required: <b>{spray}</b>"
            )


        # -------------------------------------------------
        # LATEST
        # -------------------------------------------------

        elif (
            "latest" in question
            or "last" in question
        ):

            if latest:

                answer = (
                    f"📌 <b>Latest Detection</b><br><br>"
                    f"Plant ID: <b>{latest[0]}</b><br>"
                    f"Result: <b>{latest[1]}</b><br>"
                    f"Confidence: <b>{latest[2]}%</b><br>"
                    f"Spray: <b>{latest[3]}</b>"
                )

            else:

                answer = (
                    "📌 अजून कोणतीही crop detection "
                    "record उपलब्ध नाही."
                )


        # -------------------------------------------------
        # COUNT
        # -------------------------------------------------

        elif (
            "how many" in question
            or "count" in question
            or "total" in question
        ):

            answer = (
                f"📊 SmartCrop मध्ये एकूण "
                f"<b>{total}</b> crop scans झाले आहेत."
            )


        # -------------------------------------------------
        # GREETING
        # -------------------------------------------------

        elif (
            "hello" in question
            or "hi" in question
            or "namaste" in question
        ):

            answer = (
                "👋 नमस्कार! मी "
                "<b>SmartCrop Farmer Copilot</b> आहे. "
                "तुमच्या crop health आणि SmartCrop "
                "field data बद्दल प्रश्न विचारा."
            )


        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        else:

            answer = (
                "🤖 मी SmartCrop च्या field data शी "
                "connected आहे.<br><br>"
                "तुम्ही मला <b>crop health, diseased "
                "plants, spraying, latest detection "
                "किंवा field report</b> बद्दल विचारू शकता."
            )


        return jsonify({
            "status": "success",
            "answer": answer
        })


    except Exception as error:

        print(
            "Copilot error:",
            error
        )


        return jsonify({
            "status": "error",
            "message": "Copilot request failed."
        }), 500


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )