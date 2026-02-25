import os
import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Import the exceptions and models
from postgrest.exceptions import APIError
from schemas.user import UserSignUpModel

# Import the services being tested
from services.pdf_preprocessing import process_pdf
from services.s3 import upload_file_to_s3
from services.user_services import (
    create_user, 
    user_login, 
    save_summary_main, 
    get_user_history, 
    UserLoginModel
)

# --- AWS Credentials Fixture ---
@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["S3_BUCKET_NAME"] = "my-test-bucket"

# --- S3 TESTS ---
@patch("services.s3.s3_client")
def test_upload_file_to_s3_success(mock_s3_client):
    # Setup mock behavior: force a 404 so it proceeds to upload
    error_response = {'Error': {'Code': '404'}}
    mock_s3_client.head_object.side_effect = ClientError(error_response, 'HeadObject')

    file_content = b"hello world"
    filename = "test.txt"
    
    url = upload_file_to_s3(file_content, filename, "text/plain")

    assert filename in url
    # Verify the upload function was actually called
    mock_s3_client.upload_fileobj.assert_called_once()

@patch("services.s3.s3_client")
def test_upload_file_to_s3_deduplication(mock_s3_client):
    # Setup mock behavior: return successfully from head_object, simulating file already exists
    mock_s3_client.head_object.return_value = {}

    file_content = b"duplicate content"
    
    url = upload_file_to_s3(file_content, "file.txt", "text/plain")
    
    assert "file.txt" in url
    # Verify that because it existed, upload was NEVER called
    mock_s3_client.upload_fileobj.assert_not_called()

# --- PDF TESTS ---
@patch("services.pdf_preprocessing.pdfplumber.open") 
def test_process_pdf_logic(mock_pdfplumber_open):
    # 1. Create a fake page that returns our test text
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted PDF content"
    
    # 2. Create a fake PDF object that holds our fake page
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    
    # 3. Tell the mock to return our fake PDF when used in a "with" statement
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
    
    # 4. Run the function
    result = process_pdf(b"fake_pdf_bytes")
    
    # 5. Verify the result
    assert isinstance(result, str)
    assert result == "Extracted PDF content"

# --- USER SERVICE TESTS ---
@patch("services.user_services.supabase")
def test_create_user_success(mock_supabase):
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 1, "email": "test@test.com"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_execute

    user = UserSignUpModel(email="test@test.com", password="password123", name="Test")
    result = create_user(user)

    assert result[0]["email"] == "test@test.com"

@patch("services.user_services.supabase")
@patch("services.user_services.verify_password")
def test_user_login_success(mock_verify, mock_supabase):
    mock_verify.return_value = True
    
    mock_response = MagicMock()
    mock_response.data = {"id": 1, "email": "test@me.com", "password": "hashed_stuff"}
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

    login_in = UserLoginModel(email="test@me.com", password="password123")
    result = user_login(login_in)
    
    assert result["id"] == 1

@patch("services.user_services.supabase")
def test_save_summary_success(mock_supabase):
    mock_response = MagicMock()
    mock_response.data = [{"id": 100, "filename": "doc.pdf"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    result = save_summary_main(1, "doc.pdf", "Short summary", "http://s3...", "bullet", 50)
    assert result[0]["id"] == 100

@patch("services.user_services.supabase")
def test_get_user_history_not_found(mock_supabase):
    mock_response = MagicMock()
    mock_response.data = []
    # Mocking the chain .table().select().eq().order().execute()
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

    with pytest.raises(Exception) as exc:
        get_user_history(1)
    assert "History not found" in str(exc.value)

@patch("services.user_services.supabase")
def test_database_error_handling(mock_supabase):
    mock_supabase.table.return_value.insert.side_effect = APIError({"message": "Database is down", "code": "500"})
    
    user_in = UserSignUpModel(email="err@test.com", password="password123", name="Err")
    with pytest.raises(Exception) as exc:
        create_user(user_in)
    assert "Database is down" in str(exc.value)