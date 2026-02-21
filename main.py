from fastapi import FastAPI
from schemas.user import UserSignUpModel
from services.user_services import create_user
from routers.auth import router as user_router
from routers.summary import router as summary_router
from ml.deep_model import load as deep_load
from ml.static_model import load_model as static_load
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL like "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(summary_router)

@app.on_event('startup')
async def load_models():
    deep_load()
    static_load()
    print('All models loaded')

@app.get('/')
def root():
    return {'message':'Hello FastAPI'}


