import os
import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock

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

# --- FIX 1: AWS Credentials Fixture ---
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
@mock_aws
def test_upload_file_to_s3_success():
    # Setup mock bucket
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="my-test-bucket")

    file_content = b"hello world"
    filename = "test.txt"
    
    url = upload_file_to_s3(file_content, filename, "text/plain")

    assert "my-test-bucket" in url
    objects = s3.list_objects_v2(Bucket="my-test-bucket")
    assert len(objects["Contents"]) == 1
    # Check that the filename part exists in the S3 Key
    assert any(filename in obj["Key"] for obj in objects["Contents"])

@mock_aws
def test_upload_file_to_s3_deduplication():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="my-test-bucket")

    file_content = b"duplicate content"
    
    # First upload
    upload_file_to_s3(file_content, "file.txt", "text/plain")
    # Second upload (should skip via head_object if your service handles it)
    url = upload_file_to_s3(file_content, "file.txt", "text/plain")
    
    assert "my-test-bucket" in url
    objects = s3.list_objects_v2(Bucket="my-test-bucket")
    assert len(objects["Contents"]) == 1

# --- PDF TESTS ---
# FIX 2: Mocking the actual library used inside process_pdf to avoid empty string errors
@patch("services.pdf_preprocessing.PyPDF2.PdfReader") 
def test_process_pdf_logic(mock_reader):
    # Simulate a PDF with one page of text
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted PDF content"
    mock_reader.return_value.pages = [mock_page]
    
    result = process_pdf(b"fake_pdf_bytes")
    
    assert isinstance(result, str)
    assert result == "Extracted PDF content"

# --- USER SERVICE TESTS ---
@patch("services.user_services.supabase")
def test_create_user_success(mock_supabase):
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 1, "email": "test@test.com"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_execute

    user = UserSignUpModel(email="test@test.com", password="password", name="Test")
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
    # FIX 3: Updated APIError initialization for compatibility
    mock_supabase.table.return_value.insert.side_effect = APIError({"message": "Database is down", "code": "500"})
    
    user_in = UserSignUpModel(email="err@test.com", password="123", name="Err")
    with pytest.raises(Exception) as exc:
        create_user(user_in)
    assert "Database is down" in str(exc.value)