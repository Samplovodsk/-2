from flask import Flask, request, jsonify, send_from_directory
import sqlite3, os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "data.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT    NOT NULL,
                email   TEXT    NOT NULL UNIQUE,
                age     INTEGER,
                city    TEXT
            )
        """)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/users", methods=["GET"])
def get_users():
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
            return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    age   = data.get("age")
    city  = (data.get("city") or "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    if age is not None:
        try:
            age = int(age)
            if age < 0 or age > 150:
                raise ValueError
        except ValueError:
            return jsonify({"error": "Invalid age"}), 400

    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, age, city) VALUES (?, ?, ?, ?)",
                (name, email, age, city or None)
            )
            row = conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
            return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/<int:uid>", methods=["PUT"])
def update_user(uid):
    data = request.get_json()
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    age   = data.get("age")
    city  = (data.get("city") or "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    if age is not None and age != "":
        try:
            age = int(age)
        except ValueError:
            return jsonify({"error": "Invalid age"}), 400
    else:
        age = None

    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE users SET name=?, email=?, age=?, city=? WHERE id=?",
                (name, email, age, city or None, uid)
            )
            row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if not row:
                return jsonify({"error": "User not found"}), 404
            return jsonify(dict(row))
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/<int:uid>", methods=["DELETE"])
def delete_user(uid):
    try:
        with get_db() as conn:
            cur = conn.execute("DELETE FROM users WHERE id=?", (uid,))
            if cur.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
