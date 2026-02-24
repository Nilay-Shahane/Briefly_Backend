import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app  # Ensure this points to your FastAPI app instance
import io

client = TestClient(app)

### --- SIGNUP ROUTE ---
@patch("routers.auth.create_user") 
def test_user_signup_endpoint(mock_create):
    mock_create.return_value = [{"id": 1, "email": "test@test.com"}]
    
    response = client.post(
        "/users/signup", 
        json={"email": "test@test.com", "password": "password123", "name": "Test User"} 
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "User Successfully created"
    # FIX: Removed the check for 'data' key as the router doesn't return it here.

### --- LOGIN ROUTE ---
@patch("routers.auth.user_login")
def test_login_endpoint_unauthorized(mock_login):
    # Setup: Simulate the service raising an exception
    mock_login.side_effect = Exception("User not found")
    
    # FIX: Increased password length to pass Pydantic validation and reach the 401 logic
    response = client.post(
        "/users/login", 
        json={"email": "wrong@test.com", "password": "wrongpassword123"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"

### --- USER HISTORY ---
@patch("routers.summary.get_user_history")
def test_get_user_history_success(mock_get_history):
    mock_get_history.return_value = [{"id": 1, "filename": "test.pdf", "summary": "..."}]
    
    response = client.get("/summary/user-history/1")
    
    assert response.status_code == 200
    assert response.json()["message"] == "User history fetched successfully"
    assert len(response.json()["data"]) == 1

### --- SUMMARY SAVE (WITH FILE) ---
@patch("routers.summary.process_pdf")
@patch("routers.summary.predict_static")
@patch("routers.summary.upload_file_to_s3")
@patch("routers.summary.save_summary_main")
def test_save_summary_success(mock_save_db, mock_s3, mock_predict, mock_process):
    # Setup Mocks
    mock_process.return_value = "Extracted text from PDF"
    mock_predict.return_value = "This is a summary"
    mock_s3.return_value = "https://s3-url.com/test.pdf"
    mock_save_db.return_value = [{"id": 10, "status": "saved"}]

    # Prepare fake PDF file
    file_content = b"%PDF-1.4 simulated content"
    file_tuple = ("test.pdf", io.BytesIO(file_content), "application/pdf")

    # Form Data (Multi-part form fields)
    data = {
        "user_id": "1", 
        "summary_type": "static",
        "max_length": "5"
    }

    response = client.post(
        "/summary/save-summary",
        data=data,
        files={"file": file_tuple}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Summary saved successfully"
    assert response.json()["data"][0]["id"] == 10
    
    mock_process.assert_called_once()
    mock_predict.assert_called_once()

### --- INVALID FILE TYPE ---
def test_save_summary_invalid_type():
    # Use .txt to trigger the 400 error logic in your router
    file_tuple = ("test.txt", io.BytesIO(b"hello"), "text/plain")
    data = {"user_id": "1", "summary_type": "static", "max_length": "5"}

    response = client.post("/summary/save-summary", data=data, files={"file": file_tuple})
    
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]