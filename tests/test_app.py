"""Tests for instructor-inspired ACEest Flask implementation."""

from pathlib import Path

import pytest

from aceest import create_app
from aceest.domain import PROGRAM_TEMPLATES, choose_program


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3")})
    with app.test_client() as test_client:
        yield test_client


def add_client(client, name="Asha", **data):
    response = client.post("/api/clients", json={"name": name, **data})
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def test_dashboard_health_and_database(client, tmp_path):
    assert (tmp_path / "test.sqlite3").exists()
    assert b"ACEest Fitness" in client.get("/").data
    result = client.get("/health")
    assert result.status_code == 200
    assert result.get_json()["status"] == "ok"


def test_programs_endpoint(client):
    result = client.get("/api/programs")
    assert result.status_code == 200
    assert set(result.get_json()) == {"Fat Loss", "Muscle Gain", "Beginner"}


@pytest.mark.parametrize("goal", ["Fat Loss", "Muscle Gain", "Beginner"])
def test_instructor_template_selection(goal):
    category, template = choose_program(goal)
    assert category == goal
    assert template in PROGRAM_TEMPLATES[goal]


def test_reject_unknown_goal():
    with pytest.raises(ValueError):
        choose_program("Unrecognized")


def test_create_list_get_update_client(client):
    created = add_client(client, age=29, weight=64.5, height=164,
                         target_weight=60, target_adherence=80,
                         membership_status="Active", membership_end="2026-12-31")
    cid = created["id"]
    assert created["age"] == 29
    assert len(client.get("/api/clients").get_json()) == 1
    assert client.get(f"/api/clients/{cid}").get_json()["weight"] == 64.5
    update = client.patch(f"/api/clients/{cid}", json={"membership_status": "Paused"})
    assert update.status_code == 200
    assert update.get_json()["membership_status"] == "Paused"


@pytest.mark.parametrize("data", [
    {}, {"name": ""}, {"name": " "}, {"name": 1},
    {"name": "X", "age": -1}, {"name": "X", "age": "22"},
    {"name": "X", "weight": 0}, {"name": "X", "weight": True},
    {"name": "X", "target_adherence": 101},
    {"name": "X", "membership_end": "not-a-date"},
    {"name": "X", "membership_status": "Unsupported"},
    {"name": "X", "unknown_column": "not permitted"},
])
def test_reject_invalid_client(client, data):
    result = client.post("/api/clients", json=data)
    assert result.status_code == 400
    assert "error" in result.get_json()


def test_reject_non_json_and_duplicates(client):
    assert client.post("/api/clients", data="abc", content_type="text/plain").status_code == 400
    add_client(client)
    assert client.post("/api/clients", json={"name": "Asha"}).status_code == 409


def test_missing_and_invalid_patch(client):
    assert client.get("/api/clients/999").status_code == 404
    assert client.patch("/api/clients/999", json={"name": "X"}).status_code == 404
    cid = add_client(client)["id"]
    assert client.patch(f"/api/clients/{cid}", json={}).status_code == 400
    assert client.patch(f"/api/clients/{cid}", json={"program": "custom"}).status_code == 400


def test_generate_and_persist_program(client):
    cid = add_client(client)["id"]
    response = client.post(f"/api/clients/{cid}/program", json={"goal": "Muscle Gain"})
    assert response.status_code == 200
    generated = response.get_json()["program"]
    assert generated in PROGRAM_TEMPLATES["Muscle Gain"]
    assert client.get(f"/api/clients/{cid}").get_json()["program"] == generated
    assert client.post(f"/api/clients/{cid}/program", json={"goal": "Unknown"}).status_code == 400


def test_record_weekly_progress(client):
    cid = add_client(client)["id"]
    result = client.post(f"/api/clients/{cid}/progress",
                         json={"week": "2026-W41", "adherence": 85})
    assert result.status_code == 201
    assert client.get(f"/api/clients/{cid}/progress").get_json()[0]["adherence"] == 85


@pytest.mark.parametrize("value", [-1, 101, "80", True])
def test_reject_invalid_adherence(client, value):
    cid = add_client(client)["id"]
    assert client.post(f"/api/clients/{cid}/progress",
                       json={"week": "2026-W41", "adherence": value}).status_code == 400


def test_log_workout_with_exercises(client):
    cid = add_client(client)["id"]
    result = client.post(f"/api/clients/{cid}/workouts", json={
        "date": "2026-10-12", "workout_type": "Strength", "duration_min": 45,
        "notes": "Introduction", "exercises": [
            {"name": "Squat", "sets": 3, "reps": 10, "weight": 20},
            {"name": "Press", "sets": 3, "reps": 8},
        ]})
    assert result.status_code == 201
    workouts = client.get(f"/api/clients/{cid}/workouts").get_json()
    assert len(workouts) == 1
    assert len(workouts[0]["exercises"]) == 2


@pytest.mark.parametrize("data", [
    {"date": "bad", "workout_type": "Cardio", "duration_min": 30},
    {"date": "2026-10-12", "workout_type": "", "duration_min": 30},
    {"date": "2026-10-12", "workout_type": "Cardio", "duration_min": 0},
    {"date": "2026-10-12", "workout_type": "Cardio", "duration_min": 30,
     "exercises": [{"name": "Squat", "sets": 0, "reps": 10}]},
])
def test_reject_invalid_workout(client, data):
    cid = add_client(client)["id"]
    assert client.post(f"/api/clients/{cid}/workouts", json=data).status_code == 400


def test_record_body_metrics(client):
    cid = add_client(client)["id"]
    response = client.post(f"/api/clients/{cid}/metrics",
                           json={"date": "2026-10-12", "weight": 70.5,
                                 "waist": 82, "bodyfat": 18})
    assert response.status_code == 201
    assert client.get(f"/api/clients/{cid}/metrics").get_json()[0]["weight"] == 70.5
    bad = client.post(f"/api/clients/{cid}/metrics",
                      json={"date": "2026-10-12", "weight": -5})
    assert bad.status_code == 400


def test_download_pdf_report(client):
    cid = add_client(client)["id"]
    response = client.get(f"/api/clients/{cid}/report.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert client.get("/api/clients/999/report.pdf").status_code == 404


def test_original_scripts_are_retained(client):
    folder = Path(__file__).resolve().parents[1] / "instructor_versions"
    assert len(list(folder.glob("*.py"))) == 10
