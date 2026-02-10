from database.supabase import supabase
from core.security import hash_password , verify_password
from schemas.user import UserSignUpModel , UserLoginModel
from postgrest.exceptions import APIError
def create_user(user:UserSignUpModel):
    try:
        data = {
            "email": user.email,
            "password": hash_password(user.password),
            "name": user.name
        }

        response = supabase.table("users").insert(data).execute()
        return response.data

    except APIError as e:
        raise Exception(e.message)
    
def user_login(user: UserLoginModel):
    try:
        response = (
            supabase
            .table("users")
            .select("*")
            .eq("email", user.email)
            .single()
            .execute()
        )

        db_user = response.data
        if db_user is None:
            raise Exception("User not found")

        if not verify_password(user.password, db_user["password"]):
            raise Exception("Invalid credentials")

        return db_user

    except APIError as e:
        raise Exception(e.message)
    
def save_summary_main(user_id:int ,filename : str ,  summary : str , s3_url : str , summary_type : str , summary_length : int):
    try:
        data = {
            "user_id": user_id,
            "filename": filename,
            "summary": summary,
            "summary_type": summary_type,
            "summary_length" : summary_length,
            "s3_url": s3_url 
        }
        response = supabase.table('summaries').insert(data).execute()
        return response.data
    
    except APIError as e:
        raise Exception(e.message)
    
def get_user_history(user_id : int):
    try:
        response = (
            supabase
            .table('summaries')
            .select('*')
            .eq('user_id',user_id)
            .order("created_at", desc=True)
            .execute()
        )
        user_hist = response.data
        if not user_hist:
            raise Exception("History not found")
        
        return user_hist
    
    except APIError as e:
        raise Exception(e.message)

