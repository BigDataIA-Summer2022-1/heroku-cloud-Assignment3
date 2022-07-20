#build new cloud to test
import numpy as np
import pandas as pd
import pathlib
import string
import time
from fastapi import Request
from PIL import Image
import boto3 
from io import StringIO
from fastapi import Form
from io import BytesIO
import botocore
import random
import logging
import logging.config
import logging.handlers
from fastapi import FastAPI
import uvicorn
from fastapi.security import  OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException,Request, Response
from sqlalchemy.orm import Session
import api.services as services, api.models as model, api.schemas as schemas
from api.database import SessionLocal, engine
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import File, UploadFile
import keras

model.Base.metadata.create_all(bind=engine, tables=None, checkfirst=True)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @app.middleware("http")
# async def db_session_middleware(request: Request, call_next):
#     response = Response("Internal server error", status_code=500)
#     try:
#         request.state.db = SessionLocal()
#         response = await call_next(request)
#     finally:
#         request.state.db.close()
#     return response


# # Dependency
# def get_db(request: Request):
#     return request.state.db


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return services.create_user(db=db, user=user)

@app.post('/token')
async def generate_token(db: Session = Depends(get_db),form_data: OAuth2PasswordRequestForm = Depends()):
    user = services.authenticate_user(db,form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )

    return await services.create_token(user)

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = services.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    
    return response

@app.post("/def_or_ok/")
async def def_or_ok(file: bytes = File(...)):
    '''
    The purpose of this API is to predict and check if the uploaded image is a defective product or an ok product.
    Input: bytes = File(...) Object
    Returns the probabilities of the product is a defective product or an ok product
    '''
    width, height = 300, 300
    image = Image.open(BytesIO(file)).convert('L')
    img = image.resize((width, height), Image.ANTIALIAS)
    frame = np.asarray(img)
    
    image_array = []
    # appending array of image in temp array
    image_array.append(frame)
    image_array1 = np.zeros(shape = (np.array(image_array).shape[0], 300, 300, 1))
    for i in range(np.array(image_array).shape[0]):
        # finally each sub matrix will be replaced with respective images array
        image_array1[i, :, :, 0] = image_array[i]
    image_array1 /= 255.0
    loaded = keras.models.load_model("ResNet_Model")
    pred = loaded.predict(image_array1)
    # ok is 0, def is 1
    res = float(pred[0][0])
    file = File()
    return {"Probability of Defective: ": res}

# if __name__ == "__main__":
#     cwd = pathlib.Path(__file__).parent.resolve()
#     uvicorn.run(app, host="127.0.0.1", port=4000, log_config=f"{cwd}/logging.conf")
