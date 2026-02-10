from fastapi import APIRouter , HTTPException , status,File , UploadFile , Form
from services.user_services import get_user_history , save_summary_main
from schemas.summary import SummaryModel , SummaryType
from services.pdf_preprocessing import process_pdf
from ml.static_model import predict as predict_static
from ml.deep_model import predict as predict_deep
from services.s3 import upload_file_to_s3
router = APIRouter(
    prefix='/summary',
    tags=['Summary']
)

@router.get('/user-history/{user_id}' , status_code = status.HTTP_200_OK)
async def user_history(user_id):
    response = get_user_history(user_id)
    if not response:
        raise HTTPException(
           status_code = status.HTTP_404_NOT_FOUND,
           detail="User history not found"  
        )
    return {
        'message' : 'User history fetched successfully',
        'data' : response
    }

@router.post('/save-summary')
async def save_summary(
    user_id: int = Form(...),
    summary_type: SummaryType = Form(...),
    max_length : int = Form(...),
    file: UploadFile = File(...)
):
    filename = file.filename
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    file_bytes = await file.read()
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file"
        )
    
    text = process_pdf(file_bytes)
    if summary_type == SummaryType.static: 
        summary = predict_static(text,max_length)
    else : summary = predict_deep(text,max_length)

    s3_url = upload_file_to_s3(file_bytes , filename , file.content_type)
    
    db_data = save_summary_main(
        user_id=user_id,
        filename=filename,
        summary=summary,
        s3_url=s3_url,
        summary_type=summary_type,
        summary_length = max_length
    )

    return {
        "message": "Summary saved successfully",
        "data": db_data
    }



    

