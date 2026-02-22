import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app # Assuming your FastAPI instance is here
import io

client = TestClient(app)

### Logic: Testing the SIGNUP Route
@patch("routers.auth.create_user") # We patch the function WHERE it's imported in auth.py
def test_user_signup_endpoint(mock_create):
    # Setup: Tell the mock what to return so the router doesn't crash
    mock_create.return_value = [{"id": 1, "email": "test@test.com"}]
    
    # Action: The TestClient 'hits' your API like a real browser would
    response = client.post(
        "/users/signup", 
        json={"email": "test@test.com", "password": "password123", "name": "Test User"}
    )
    
    # Verification
    assert response.status_code == 200
    assert response.json()["message"] == "User Successfully created"
    assert "id" in response.json()

### Logic: Testing the LOGIN Route (Failure Scenario)
@patch("routers.auth.user_login")
def test_login_endpoint_unauthorized(mock_login):
    # Setup: Simulate an error being raised by the service layer
    mock_login.side_effect = Exception("User not found")
    
    response = client.post(
        "/users/login", 
        json={"email": "wrong@test.com", "password": "wrong"}
    )
    
    # Verification: Does the router correctly convert the error to 401?
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"

## 1. Logic: Testing User History (GET)
@patch("routers.summary.get_user_history")
def test_get_user_history_success(mock_get_history):
    # Setup: Mock list of past summaries
    mock_get_history.return_value = [{"id": 1, "filename": "test.pdf", "summary": "..."}]
    
    response = client.get("/summary/user-history/1")
    
    assert response.status_code == 200
    assert response.json()["message"] == "User history fetched successfully"
    assert len(response.json()["data"]) == 1

## 2. Logic: Testing Summary Save (POST with File)
@patch("routers.summary.process_pdf")
@patch("routers.summary.predict_static")
@patch("routers.summary.upload_file_to_s3")
@patch("routers.summary.save_summary_main")
def test_save_summary_success(mock_save_db, mock_s3, mock_predict, mock_process):
    # Setup Mocks
    mock_process.return_value = "Extracted text from PDF"
    mock_predict.return_value = "This is a summary"
    mock_s3.return_value = "https://s3-url.com/test.pdf"
    mock_save_db.return_value = {"id": 10, "status": "saved"}

    # Prepare fake PDF file
    file_content = b"%PDF-1.4 simulated content"
    file_tuple = ("test.pdf", io.BytesIO(file_content), "application/pdf")

    # Form Data
    data = {
        "user_id": 1,
        "summary_type": "static",
        "max_length": 5
    }

    # Action: Perform Multipart/form-data request
    response = client.post(
        "/summary/save-summary",
        data=data,
        files={"file": file_tuple}
    )

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Summary saved successfully"
    assert response.json()["data"]["id"] == 10
    
    # Verify the chain was called
    mock_process.assert_called_once()
    mock_predict.assert_called_once_with("Extracted text from PDF", 5)

## 3. Logic: Testing Error for Non-PDF files
def test_save_summary_invalid_type():
    file_tuple = ("test.txt", io.BytesIO(b"hello"), "text/plain")
    data = {"user_id": 1, "summary_type": "static", "max_length": 5}

    response = client.post("/summary/save-summary", data=data, files={"file": file_tuple})
    
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]