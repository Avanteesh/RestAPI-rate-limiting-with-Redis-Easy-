from fastapi import FastAPI,Response,Request
from fastapi import Form,Depends,HTTPException,status
from sqlmodel import SQLModel, Field,create_engine
from sqlmodel import String, Session, select
from passlib.context import CryptContext
from dotenv import load_dotenv
from redis import Redis
from os import getenv
from uuid import uuid4
from json import loads,dumps
from jose import jwt, JWTError
from datetime import datetime, timedelta
from requests import get

load_dotenv()
app = FastAPI()
redis_ins = Redis(host=getenv('HOST'))
pwd_context = CryptContext(schemes=["bcrypt"],deprecated='auto')
credential_exception = HTTPException(
  detail="Unauthorized user!",status_code=status.HTTP_401_UNAUTHORIZED,
  headers={"WWW-Authenticate":"Bearer"}
)

class User(SQLModel, table=True):
    id: str = Field(default=str(uuid4()),primary_key=True)
    username: str = Field(String)
    email: str = Field(String,unique=True)
    password: str = Field(String)

class UserMetaData(SQLModel):
    id: str
    username: str
    email: str

db_engine = create_engine("sqlite:///users.db")
SQLModel.metadata.create_all(db_engine)

def getUser(email: str):
    query = None
    with Session(db_engine) as session:
        query = session.exec(
          select(User).where(User.email == email)
        ).first()
        return query

def authenticate(email: str, password: str):
    query = getUser(email)
    if not query:
        return False
    elif not pwd_context.verify(password, query.password):
        return False
    return UserMetaData(id=query.id,username=query.username,email=query.email)

def createAccessToken(data: dict):
    copied = data.copy()
    expiry_time = datetime.now() + timedelta(minutes=int(getenv('TOKEN_EXPIRY_TIME')))
    copied.update({"exp": expiry_time})
    return jwt.encode(copied,getenv("SECRET_KEY"),algorithm=getenv("ALGORITHM"))

def verifyJWT(request: Request):
    cookie = request.cookies.get("_session")
    if cookie is None:
        raise credential_exception
    return cookie

async def getActiveUser(token: str=Depends(verifyJWT)):
    userdata = None
    try:
        payload = jwt.decode(token, getenv("SECRET_KEY"),algorithms=[getenv("ALGORITHM")])
        userdata = payload.get("sup")
        if userdata is None:
            raise credential_exception
        userdata = loads(userdata)
    except JWTError:
        raise credential_exception
    result = getUser(userdata["email"])
    if result is None:
        raise credential_exception
    return result

def getWeatherData(city_name: str):
    data = get(f"http://api.weatherapi.com/v1/current.json?key={getenv("WEATHER_API_KEY")}&q={city_name}&aqi=no")
    parsed = data.json()
    return {
      "location": parsed["location"]["name"],
      "lat-long": [parsed['location']['lat'], parsed['location']['lon']],
      "temperature": f"{parsed['current']['temp_c']} celsius",
      "wind speed": f"{parsed['current']['wind_kph']} km/h",
      "cloud cover": f"{parsed['current']['cloud']} %"
    }

@app.post("/signIn")
async def signIn(username: str=Form(...),email:str=Form(...),password:str=Form(...)):
    if getUser(email) is not None:
        return {
          "status": "failed!", 
          "message": "Invalid email! might probably exist!"
        }
    with Session(db_engine) as session:
        session.add(User(
          username=username,email=email,password=pwd_context.hash(password)                
        ))
        session.commit()
    return {
      "status": "Success",
      "message": "Your signed in successfully!"
    }
    
@app.post("/login")
async def login(response: Response, email: str=Form(...),password: str=Form(...)):
    user_metadata = authenticate(email, password)
    if user_metadata is False:
        return {
          "status": "failed!",
          "message": "Oops your email of password might be incorrect!"
        }
    token = createAccessToken({"sup": dumps({"email": user_metadata.email,"username": user_metadata.username})})
    response.set_cookie(key="_session", value=token)
    return {
      "status": "success",
      "message": "Your active!"
    }

@app.get("/tell-me-weather/{city_name}")
async def tellMeWeather(city_name: str, user: UserMetaData=Depends(getActiveUser)):
    encoded_data = redis_ins.hgetall(user.id)
    calls = {} if encoded_data == {} else {key.decode():value.decode() for key, value in encoded_data.items()}
    if calls == {}:
        redis_ins.hset(name=user.id,key='requests',value=1)
        redis_ins.expire(user.id, 180) # key expires in 3 minute! 
        data = getWeatherData(city_name)
        return {
          "status": "success","report": data
        }
    elif int(calls['requests']) == 3:
        return {
          "status": "Error",
          "message": "You have exceeded the rate limit, 1 request per minute"
        } 
    redis_ins.hset(name=user.id,key='requests',value=int(calls['requests'])+1)
    data = getWeatherData(city_name)
    return data
    
        
