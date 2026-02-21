from fastapi import APIRouter , HTTPException , status
from schemas.user import UserSignUpModel ,UserLoginModel
from services.user_services import create_user , user_login

router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.post('/signup')
def user_signup(user:UserSignUpModel):
    user_resp = create_user(user)
    return {'status_code':200,  
            'message':'User Successfully created',
            'id' : user_resp    
        }

@router.post("/login")
def login_user(user: UserLoginModel):
    try:
        user_data = user_login(user)
        print(user_data)
        return {
            "status": "success",
            "message": "Login successful",
            "data": user_data['id']
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

