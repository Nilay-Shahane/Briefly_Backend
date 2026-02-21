import os
import boto3
import pytest
from moto import mock_aws
from services.pdf_preprocessing import process_pdf
from services.s3 import upload_file_to_s3
from services.user_services import create_user , user_login 
from unittest.mock import patch , MagicMock
from schemas.user import UserSignUpModel

# Use a fixture to keep the environment clean
@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["S3_BUCKET_NAME"] = "my-test-bucket"

@mock_aws
def test_upload_file_to_s3_success(aws_credentials):
    # Setup mock bucket
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="my-test-bucket")

    file_content = b"hello world"
    filename = "test.txt"
    
    url = upload_file_to_s3(file_content, filename, "text/plain")

    # Assertions
    assert "my-test-bucket" in url
    # Verify the file is actually there (Checking the hash-prefixed name)
    objects = s3.list_objects_v2(Bucket="my-test-bucket")
    assert len(objects["Contents"]) == 1
    assert filename in objects["Contents"][0]["Key"]

@mock_aws
def test_upload_file_to_s3_deduplication(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="my-test-bucket")

    file_content = b"duplicate content"
    
    # First upload
    upload_file_to_s3(file_content, "file.txt", "text/plain")
    # Second upload (should skip via head_object)
    url = upload_file_to_s3(file_content, "file.txt", "text/plain")
    
    assert "my-test-bucket" in url
    
    # Verify ONLY one file exists despite two upload calls
    objects = s3.list_objects_v2(Bucket="my-test-bucket")
    assert len(objects["Contents"]) == 1

def test_process_pdf_logic():
    # Instead of reading a real file, we can use a small bytes object
    fake_pdf_bytes = b"%PDF-1.4 test content"
    result = process_pdf(fake_pdf_bytes)
    
    assert isinstance(result, str)
    assert len(result) > 0

@patch("services.user_services.supabase")
def test_create_user_success(mock_supabase):
    # 1. Setup the mock response
    mock_execute = MagicMock()
    mock_execute.data = [{"id": 1, "email": "test@test.com"}]
    
    # 2. Chain the mock calls to match your function logic
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_execute

    # 3. Run the test
    user = UserSignUpModel(email="test@test.com", password="password", name="Test")
    result = create_user(user)

    assert result[0]["email"] == "test@test.com"

@patch("services.user_services.supabase")
@patch("services.user_services.verify_password")
def test_user_login_success(mock_verify, mock_supabase):
    # Setup: Password is valid
    mock_verify.return_value = True
    
    # Mocking .table().select().eq().single().execute()
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
    # Simulate an empty response
    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

    with pytest.raises(Exception) as exc:
        get_user_history(1)
    assert "History not found" in str(exc.value)


@patch("services.user_services.supabase")
def test_database_error_handling(mock_supabase):
    # Simulate an actual Supabase API error
    mock_supabase.table.return_value.insert.side_effect = APIError({"message": "Database is down", "code": "500"})
    
    user_in = UserSignUpModel(email="err@test.com", password="123", name="Err")
    with pytest.raises(Exception) as exc:
        create_user(user_in)
    assert "Database is down" in str(exc.value)
