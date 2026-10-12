"""Flask JSON API and a small UI for demonstrating the original ACEest features."""
from datetime import date
from io import BytesIO
import sqlite3

from flask import Blueprint, jsonify, render_template, request, send_file
from fpdf import FPDF

from .database import get_db
from .domain import PROGRAM_TEMPLATES, choose_program

bp = Blueprint("main", __name__)
FIELDS = {"name", "age", "height", "weight", "target_weight", "target_adherence",
          "membership_status", "membership_end"}


def error(message, status=400):
    return jsonify({"error": message}), status


def payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def valid_date(value):
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_client(data, is_new=True):
    if not isinstance(data, dict):
        return "JSON object required"
    if is_new and "name" not in data:
        return "name is required"
    if not data or not set(data).issubset(FIELDS):
        return "provide only valid client fields"
    if "name" in data and (not isinstance(data["name"], str) or not data["name"].strip()):
        return "name must be non-empty"
    if "age" in data and data["age"] is not None and (
        type(data["age"]) is not int or not 1 <= data["age"] <= 120
    ):
        return "age must be an integer between 1 and 120"
    for field in ("height", "weight", "target_weight"):
        if field in data and data[field] is not None and (
            type(data[field]) not in (int, float) or not 0 < data[field] <= 500
        ):
            return f"{field} must be a positive number (up to 500)"
    if "target_adherence" in data and data["target_adherence"] is not None and (
        type(data["target_adherence"]) is not int
        or not 0 <= data["target_adherence"] <= 100
    ):
        return "target_adherence must be an integer from 0 to 100"
    if "membership_status" in data and data["membership_status"] not in (
        "Active", "Paused", "Expired"
    ):
        return "membership_status must be Active, Paused, or Expired"
    if "membership_end" in data and data["membership_end"] is not None and not valid_date(data["membership_end"]):
        return "membership_end must use YYYY-MM-DD"
    return None


def client_or_none(client_id):
    return get_db().execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()


def rows_json(query, params=()):
    return [dict(row) for row in get_db().execute(query, params).fetchall()]


@bp.get("/")
def dashboard():
    return render_template("index.html")


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "ACEest Fitness & Gym"})


@bp.get("/api/programs")
def programs():
    return jsonify(PROGRAM_TEMPLATES)


@bp.get("/api/clients")
def list_clients():
    return jsonify(rows_json("SELECT * FROM clients ORDER BY id"))


@bp.post("/api/clients")
def add_client():
    data = payload()
    problem = validate_client(data)
    if problem:
        return error(problem)
    values = {k: (v.strip() if k == "name" else v) for k, v in data.items()}
    fields = list(values)
    db = get_db()
    try:
        cursor = db.execute(
            f"INSERT INTO clients ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
            tuple(values.values()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("a client with this name already exists", 409)
    return jsonify(dict(client_or_none(cursor.lastrowid))), 201


@bp.get("/api/clients/<int:client_id>")
def get_client(client_id):
    client = client_or_none(client_id)
    if not client:
        return error("client not found", 404)
    return jsonify(dict(client))


@bp.patch("/api/clients/<int:client_id>")
def update_client(client_id):
    if not client_or_none(client_id):
        return error("client not found", 404)
    data = payload()
    problem = validate_client(data, is_new=False)
    if problem:
        return error(problem)
    values = {k: (v.strip() if k == "name" else v) for k, v in data.items()}
    db = get_db()
    try:
        db.execute(
            f"UPDATE clients SET {', '.join(f'{k} = ?' for k in values)} WHERE id = ?",
            (*values.values(), client_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("a client with this name already exists", 409)
    return jsonify(dict(client_or_none(client_id)))


@bp.post("/api/clients/<int:client_id>/program")
def generate_program(client_id):
    if not client_or_none(client_id):
        return error("client not found", 404)
    data = payload()
    if data is None or set(data) - {"goal"}:
        return error("JSON object with optional goal required")
    try:
        category, detail = choose_program(data.get("goal"))
    except ValueError as exc:
        return error(str(exc))
    db = get_db()
    db.execute("UPDATE clients SET program = ? WHERE id = ?", (detail, client_id))
    db.commit()
    return jsonify({"category": category, "program": detail})


@bp.route("/api/clients/<int:client_id>/progress", methods=["GET", "POST"])
def progress(client_id):
    if not client_or_none(client_id):
        return error("client not found", 404)
    if request.method == "GET":
        return jsonify(rows_json("SELECT id, week, adherence FROM progress WHERE client_id=? ORDER BY id", (client_id,)))
    data = payload()
    if not data or not isinstance(data.get("week"), str) or not data["week"].strip() or (
        type(data.get("adherence")) is not int or not 0 <= data["adherence"] <= 100
    ):
        return error("week and integer adherence (0–100) required")
    db = get_db()
    cur = db.execute(
        "INSERT INTO progress (client_id,week,adherence) VALUES (?,?,?)",
        (client_id, data["week"].strip(), data["adherence"]),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "week": data["week"].strip(), "adherence": data["adherence"]}), 201


@bp.route("/api/clients/<int:client_id>/workouts", methods=["GET", "POST"])
def workouts(client_id):
    if not client_or_none(client_id):
        return error("client not found", 404)
    if request.method == "GET":
        data = rows_json("SELECT * FROM workouts WHERE client_id=? ORDER BY date DESC, id DESC", (client_id,))
        for workout in data:
            workout["exercises"] = rows_json(
                "SELECT id, name, sets, reps, weight FROM exercises WHERE workout_id=? ORDER BY id", (workout["id"],)
            )
        return jsonify(data)
    data = payload()
    if not data or not valid_date(data.get("date")):
        return error("date must use YYYY-MM-DD")
    if not isinstance(data.get("workout_type"), str) or not data["workout_type"].strip():
        return error("workout_type is required")
    if type(data.get("duration_min")) is not int or not 1 <= data["duration_min"] <= 1440:
        return error("duration_min must be an integer from 1 to 1440")
    if not isinstance(data.get("notes", ""), str):
        return error("notes must be text")
    exercises = data.get("exercises", [])
    if not isinstance(exercises, list):
        return error("exercises must be a list")
    for item in exercises:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
            return error("each exercise needs a name")
        if any(type(item.get(k)) is not int or not 1 <= item[k] <= 1000 for k in ("sets", "reps")):
            return error("each exercise needs positive integer sets and reps")
        if type(item.get("weight", 0)) not in (int, float) or not 0 <= item.get("weight", 0) <= 2000:
            return error("exercise weight must be nonnegative")
    db = get_db()
    with db:
        cur = db.execute(
            "INSERT INTO workouts (client_id,date,workout_type,duration_min,notes) VALUES (?,?,?,?,?)",
            (client_id, data["date"], data["workout_type"].strip(), data["duration_min"], data.get("notes", "")),
        )
        for item in exercises:
            db.execute(
                "INSERT INTO exercises (workout_id,name,sets,reps,weight) VALUES (?,?,?,?,?)",
                (cur.lastrowid, item["name"].strip(), item["sets"], item["reps"], item.get("weight", 0)),
            )
    return jsonify({"id": cur.lastrowid, "message": "workout added"}), 201


@bp.route("/api/clients/<int:client_id>/metrics", methods=["GET", "POST"])
def metrics(client_id):
    if not client_or_none(client_id):
        return error("client not found", 404)
    if request.method == "GET":
        return jsonify(rows_json("SELECT id,date,weight,waist,bodyfat FROM metrics WHERE client_id=? ORDER BY date", (client_id,)))
    data = payload()
    if not data or not valid_date(data.get("date")):
        return error("date must use YYYY-MM-DD")
    if type(data.get("weight")) not in (int, float) or not 0 < data["weight"] <= 500:
        return error("weight must be a positive number up to 500")
    for field in ("waist", "bodyfat"):
        value = data.get(field)
        if value is not None and (type(value) not in (int, float) or not 0 <= value <= (100 if field == "bodyfat" else 500)):
            return error(f"{field} has an invalid value")
    db = get_db()
    cur = db.execute(
        "INSERT INTO metrics (client_id,date,weight,waist,bodyfat) VALUES (?,?,?,?,?)",
        (client_id, data["date"], data["weight"], data.get("waist"), data.get("bodyfat")),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "message": "metrics saved"}), 201


@bp.get("/api/clients/<int:client_id>/report.pdf")
def report_pdf(client_id):
    client = client_or_none(client_id)
    if client is None:
        return error("client not found", 404)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "ACEest Fitness & Gym - Client Report", ln=1)
    pdf.set_font("Helvetica", size=11)
    # Built-in PDF fonts are Latin-1 only; replace unsupported characters.
    for field in ("id", "name", "age", "height", "weight", "program", "calories",
                  "target_weight", "target_adherence", "membership_status", "membership_end"):
        value = str(client[field]) if client[field] is not None else "N/A"
        line = f"{field.replace('_', ' ').title()}: {value}"
        pdf.multi_cell(0, 8, line.encode("latin-1", errors="replace").decode("latin-1"))
    return send_file(BytesIO(bytes(pdf.output())), mimetype="application/pdf",
                     as_attachment=True, download_name=f"aceest-client-{client_id}.pdf")
