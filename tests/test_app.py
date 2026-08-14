"""
Test suite for Mergington High School Activities API
Using AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Arrange: Provide a TestClient for API testing"""
    return TestClient(app)


@pytest.fixture
def mock_activities(monkeypatch):
    """Arrange: Provide fresh test data for each test"""
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    monkeypatch.setattr("src.app.activities", test_activities)
    return test_activities


# ====== GET / Endpoint Tests ======

class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """
        Test GET / redirects to /static/index.html
        Arrange: TestClient ready
        Act: GET /
        Assert: Status 307, Location header correct
        """
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ====== GET /activities Endpoint Tests ======

class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, mock_activities):
        """
        Test GET /activities returns all activities
        Arrange: Mock activities data loaded
        Act: GET /activities
        Assert: Status 200, all activities returned
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_has_correct_structure(self, client, mock_activities):
        """
        Test GET /activities returns correct data structure
        Arrange: Mock activities data loaded
        Act: GET /activities
        Assert: Each activity has required fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_get_activities_reflects_current_participant_count(self, client, mock_activities):
        """
        Test GET /activities shows correct participant counts
        Arrange: Mock activities with known participants
        Act: GET /activities
        Assert: Participant counts match
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 1
        assert len(data["Gym Class"]["participants"]) == 2


# ====== POST /activities/{activity_name}/signup Endpoint Tests ======

class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client, mock_activities):
        """
        Test successful signup of new participant
        Arrange: Activity exists with 2 participants
        Act: POST signup with new email
        Assert: Status 200, email added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "alice@mergington.edu"
        initial_count = len(mock_activities[activity_name]["participants"])

        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert f"Signed up {new_email}" in response.json()["message"]
        assert new_email in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_duplicate_participant_fails(self, client, mock_activities):
        """
        Test signup fails when participant already registered
        Arrange: Activity with existing participant michael@mergington.edu
        Act: POST signup with same email again
        Assert: Status 400, error message about duplicate
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client, mock_activities):
        """
        Test signup fails when activity doesn't exist
        Arrange: Activity "Nonexistent Club" doesn't exist
        Act: POST signup for nonexistent activity
        Assert: Status 404, activity not found error
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_with_special_characters_in_activity_name(self, client, mock_activities):
        """
        Test signup with URL-encoded activity name (e.g., spaces)
        Arrange: Activity "Programming Class" has spaces
        Act: POST signup with URL-encoded activity name
        Assert: Status 200, signup successful
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "bob@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

        # Assert
        assert response.status_code == 200
        assert new_email in mock_activities[activity_name]["participants"]


# ====== DELETE /activities/{activity_name}/signup Endpoint Tests ======

class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_remove_existing_participant_success(self, client, mock_activities):
        """
        Test successful removal of participant
        Arrange: Activity with participant michael@mergington.edu
        Act: DELETE request for michael
        Assert: Status 200, michael removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(mock_activities[activity_name]["participants"])

        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert f"Removed {email}" in response.json()["message"]
        assert email not in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == initial_count - 1

    def test_remove_nonexistent_participant_fails(self, client, mock_activities):
        """
        Test removal fails when participant not signed up
        Arrange: Activity without alice@mergington.edu
        Act: DELETE request for alice
        Assert: Status 404, not signed up error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@mergington.edu"  # Not in Chess Club

        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()

    def test_remove_from_nonexistent_activity_fails(self, client, mock_activities):
        """
        Test removal fails when activity doesn't exist
        Arrange: Activity "Nonexistent Club" doesn't exist
        Act: DELETE from nonexistent activity
        Assert: Status 404, activity not found error
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_participant_from_activity_with_spaces_in_name(self, client, mock_activities):
        """
        Test removal with URL-encoded activity name (spaces)
        Arrange: Activity "Programming Class" with participants
        Act: DELETE with URL-encoded name
        Assert: Status 200, participant removed
        """
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        assert response.status_code == 200
        assert email not in mock_activities[activity_name]["participants"]


# ====== Integration Tests ======

class TestIntegration:
    """Integration tests for complete signup/removal workflows"""

    def test_signup_then_remove_workflow(self, client, mock_activities):
        """
        Test complete workflow: signup, verify in list, then remove
        Arrange: Activity "Gym Class" with known participants
        Act: Add charlie, verify in list, then remove charlie
        Assert: All operations succeed, participant counts correct
        """
        # Arrange
        activity_name = "Gym Class"
        new_email = "charlie@mergington.edu"
        initial_count = len(mock_activities[activity_name]["participants"])

        # Act - Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

        # Assert - Signup successful
        assert signup_response.status_code == 200
        assert new_email in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == initial_count + 1

        # Act - Verify in activities list
        get_response = client.get("/activities")
        activities = get_response.json()

        # Assert - Verify visible
        assert new_email in activities[activity_name]["participants"]

        # Act - Remove participant
        remove_response = client.delete(f"/activities/{activity_name}/signup", params={"email": new_email})

        # Assert - Removal successful
        assert remove_response.status_code == 200
        assert new_email not in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == initial_count

    def test_multiple_signups_same_activity(self, client, mock_activities):
        """
        Test multiple different participants can sign up for same activity
        Arrange: Programming Class activity
        Act: Sign up two different participants
        Assert: Both added successfully
        """
        # Arrange
        activity_name = "Programming Class"
        email1 = "alice@mergington.edu"
        email2 = "bob@mergington.edu"

        # Act
        response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        response2 = client.post(f"/activities/{activity_name}/signup", params={"email": email2})

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in mock_activities[activity_name]["participants"]
        assert email2 in mock_activities[activity_name]["participants"]
        assert len(mock_activities[activity_name]["participants"]) == 3  # emma + alice + bob
