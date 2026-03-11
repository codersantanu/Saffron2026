from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)
CORS(app) # Allows your frontend to talk to your backend safely

# --- TiDB Database Configuration ---
# Replace these with your actual TiDB credentials!
DB_HOST = os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com")
DB_USER = os.getenv("DB_USER", "36DbHsyf2Xe9m7z.root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nnR9Hf5R3oioF5jP")
DB_NAME = os.getenv("DB_NAME", "Saffron_Cultivation")
DB_PORT = 4000

# Helper function to connect to TiDB
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

# --- ROUTES ---

@app.route('/')
def home():
    # Serves your frontend dashboard
    return render_template('index.html')

@app.route('/api/sensor', methods=['GET', 'POST'])
def sensor_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # ESP32 sends data here
        data = request.json
        sql = """
            INSERT INTO sensor_data 
            (device_id, temperature, humidity, soil_moisture, air_quality, light_intensity, pwm_value) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data.get('device_id', 'ESP32_SAFFRON_1'),
            data.get('temperature', 0.0),
            data.get('humidity', 0.0),
            data.get('soil_moisture', 0.0),
            data.get('air_quality', 0.0),
            data.get('light_intensity', 0),
            data.get('pwm_value', 0)
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Data logged"}), 201

    elif request.method == 'GET':
        # Dashboard fetches latest data from here
        cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return jsonify(row if row else {})

@app.route('/api/control', methods=['GET', 'POST'])
def device_control():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Dashboard sends manual commands here
        data = request.json
        sql = """
            INSERT INTO device_control 
            (device_id, mode, Relay2_peltier, Relay1_mist_maker, Relay3_exhaust_fan, buzzer_state, pwm_value) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data.get('device_id', 'ESP32_SAFFRON_1'),
            data.get('mode', 'AUTO'),
            bool(data.get('Relay2_peltier', False)),
            bool(data.get('Relay1_mist_maker', False)),
            bool(data.get('Relay3_exhaust_fan', False)),
            bool(data.get('buzzer_state', False)),
            int(data.get('pwm_value', 0))
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Command updated"}), 201

    elif request.method == 'GET':
        # ESP32 and Dashboard fetch the latest command from here
        cursor.execute("SELECT * FROM device_control ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return jsonify(row if row else {})

if __name__ == '__main__':
    app.run(debug=True, port=5000)