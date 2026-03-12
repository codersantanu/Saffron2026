from flask import Flask, request, jsonify
import pymysql
import os

app = Flask(__name__)

# --- TiDB Database Connection ---
def get_db_connection():
    return pymysql.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="36DbHsyf2Xe9m7z.root",
        password="nnR9Hf5R3oioF5jP",
        database="Saffron_Cultivation",
        cursorclass=pymysql.cursors.DictCursor,
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )# --- ROUTE 1: Receive Sensor Data from ESP32 (POST) ---
@app.route('/api/sensor', methods=['POST'])
def receive_sensor_data():
    data = request.json
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """INSERT INTO sensor_data 
                     (device_id, temperature, humidity, soil_moisture, air_quality, light_intensity, pwm_value)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                data.get('device_id'),
                data.get('temperature'),
                data.get('humidity'),
                data.get('soil_moisture'),
                data.get('air_quality'),
                data.get('light_intensity'),
                data.get('pwm_value')
            ))
        conn.commit()
        return jsonify({"status": "success", "message": "Sensor data logged to TiDB!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

# --- ROUTE 2: Send Control Commands to ESP32 (GET) ---
@app.route('/api/control', methods=['GET'])
def send_control_data():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch the most recent command for this specific ESP32
            sql = """SELECT mode, Relay1_mist_maker, Relay2_peltier, Relay3_exhaust_fan, buzzer_state, pwm_value 
                     FROM device_control 
                     WHERE device_id = 'ESP32_SAFFRON_1' 
                     ORDER BY created_at DESC LIMIT 1"""
            cursor.execute(sql)
            result = cursor.fetchone()

            if result:
                # Map TiDB 1/0 integers to True/False for the ESP32 JSON parser
                return jsonify({
                    "mode": result["mode"],
                    "Relay1_mist_maker": bool(result["Relay1_mist_maker"]),
                    "Relay2_peltier": bool(result["Relay2_peltier"]),
                    "Relay3_exhaust_fan": bool(result["Relay3_exhaust_fan"]),
                    "buzzer_state": bool(result["buzzer_state"]),
                    "pwm_value": result["pwm_value"]
                }), 200
            else:
                # Failsafe: If the table is empty, tell ESP32 to stay in AUTO mode
                return jsonify({"mode": "AUTO"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Run locally on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)