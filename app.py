from flask import Flask, request, jsonify, render_template
import mysql.connector
import time
import os

app = Flask(__name__)

# -------- CONFIG --------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 4000)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": 10
}

API_KEY = os.getenv("API_KEY")

# -------- GLOBAL STATE --------
last_seen = 0
collect_data = True

# -------- DB CONNECTION --------
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")


# -------- HEARTBEAT (IMPORTANT) --------


# -------- RECEIVE DATA --------
@app.route("/api/data")
def receive_data():
    global last_seen, collect_data

    key = request.args.get("key")
    if key != API_KEY:
        return "Invalid API Key", 403

    current_time = time.time()

    # ✅ Update connection time
    last_seen = current_time

    if not collect_data:
        return "Stopped"

    try:
        s1 = float(request.args.get("s1"))
        s2 = float(request.args.get("s2"))
        s3 = float(request.args.get("s3"))
    except:
        return "Invalid sensor values", 400

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s,%s,%s)",
            (s1, s2, s3)
        )

        db.commit()
        cursor.close()
        db.close()

        return "Saved"

    except Exception as e:
        return str(e), 500


# -------- STATUS --------
@app.route("/status")
def status():
    global last_seen

    diff = time.time() - last_seen

    if diff < 20:
        state = "Connected"
    else:
        state = "Disconnected"

    return jsonify({
        "status": state,
        "last_seen_seconds": int(diff)
    })

# -------- START / STOP --------
@app.route("/start")
def start():
    global collect_data
    collect_data = True
    return "Started"


@app.route("/stop")
def stop():
    global collect_data
    collect_data = False
    return "Stopped"


# -------- GET DATA --------
@app.route("/api/data")
def receive_data():
    global last_seen, collect_data

    key = request.args.get("key")
    if key != API_KEY:
        return "Invalid API Key", 403

    # ✅ THIS MUST BE FIRST
    last_seen = time.time()

    if not collect_data:
        return "Stopped"


# -------- SEARCH --------
@app.route("/search", methods=["POST"])
def search():
    start = request.form.get("start")
    end = request.form.get("end")

    if start:
        start = start.replace("T", " ")
    if end:
        end = end.replace("T", " ")

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, sensor1, sensor2, sensor3, timestamp
            FROM sensor_db
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY id DESC
        """, (start, end))

        data = cursor.fetchall()

        for row in data:
            if row["timestamp"]:
                row["timestamp"] = row["timestamp"].strftime("%d/%m/%Y %H:%M:%S")

        cursor.close()
        db.close()

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})


# -------- DOWNLOAD CSV --------
@app.route("/download", methods=["POST"])
def download():
    import csv
    from io import StringIO

    start = request.form.get("start")
    end = request.form.get("end")

    if start:
        start = start.replace("T", " ")
    if end:
        end = end.replace("T", " ")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, sensor1, sensor2, sensor3, timestamp
        FROM sensor_db
        WHERE timestamp BETWEEN %s AND %s
        ORDER BY id DESC
    """, (start, end))

    data = cursor.fetchall()

    si = StringIO()
    writer = csv.writer(si)

    writer.writerow(["ID", "Sensor1", "Sensor2", "Sensor3", "Timestamp"])

    for row in data:
        writer.writerow([
            row["id"],
            row["sensor1"],
            row["sensor2"],
            row["sensor3"],
            row["timestamp"]
        ])

    output = si.getvalue()

    cursor.close()
    db.close()

    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=data.csv'
    }


if __name__ == "__main__":
    app.run(debug=True)
