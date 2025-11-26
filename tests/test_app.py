import os
import sys
from fastapi.testclient import TestClient
from urllib.parse import quote

# Ensure project root is on sys.path so `src.app` can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.app import app


client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expected activity present
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "pytest-user@example.com"

    # Ensure clean state: email should not be present initially
    before = client.get("/activities").json()
    assert email not in before[activity]["participants"]

    # Sign up
    url_signup = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    resp = client.post(url_signup)
    assert resp.status_code == 200
    assert email in resp.json().get("message", "")

    # Confirm added
    after = client.get("/activities").json()
    assert email in after[activity]["participants"]

    # Unregister
    url_delete = f"/activities/{quote(activity)}/participants?email={quote(email)}"
    resp = client.delete(url_delete)
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Confirm removed
    final = client.get("/activities").json()
    assert email not in final[activity]["participants"]


def test_signup_duplicate_fails():
    """Test that signing up twice with same email fails."""
    activity = "Programming Class"
    email = "duplicate-test@example.com"

    # First signup should succeed
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    resp1 = client.post(url)
    assert resp1.status_code == 200

    # Second signup should fail
    resp2 = client.post(url)
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json().get("detail", "").lower()

    # Clean up
    client.delete(f"/activities/{quote(activity)}/participants?email={quote(email)}")


def test_signup_nonexistent_activity():
    """Test that signing up for non-existent activity returns 404."""
    activity = "Nonexistent Activity"
    email = "test@example.com"

    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    resp = client.post(url)
    assert resp.status_code == 404
    assert "Activity not found" in resp.json().get("detail", "")


def test_unregister_nonexistent_activity():
    """Test that unregistering from non-existent activity returns 404."""
    activity = "Nonexistent Activity"
    email = "test@example.com"

    url = f"/activities/{quote(activity)}/participants?email={quote(email)}"
    resp = client.delete(url)
    assert resp.status_code == 404
    assert "Activity not found" in resp.json().get("detail", "")


def test_unregister_nonexistent_participant():
    """Test that unregistering a non-existent participant returns 404."""
    activity = "Basketball Team"
    email = "nonexistent@example.com"

    url = f"/activities/{quote(activity)}/participants?email={quote(email)}"
    resp = client.delete(url)
    assert resp.status_code == 404
    assert "Participant not found" in resp.json().get("detail", "")


def test_activity_max_participants():
    """Test that activity data includes max_participants."""
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    
    for activity_name, details in data.items():
        assert "max_participants" in details
        assert isinstance(details["max_participants"], int)
        assert details["max_participants"] > 0


def test_activity_structure():
    """Test that each activity has all required fields."""
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    
    required_fields = ["description", "schedule", "max_participants", "participants"]
    
    for activity_name, details in data.items():
        for field in required_fields:
            assert field in details, f"Missing field '{field}' in activity '{activity_name}'"
        assert isinstance(details["participants"], list)

