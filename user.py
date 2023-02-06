import os
import json
import hashlib

from dotenv import load_dotenv
from pydantic import BaseModel
from redis import Redis

load_dotenv()

r = Redis(
    host=os.getenv("REDIS_HOST"), 
    port=os.getenv("REDIS_PORT"), 
    db=int(os.getenv("REDIS_DB")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PW")
)

usersGroup = "users/"

userCache = {}

class PredictedGrade(BaseModel):
    email: str
    assignment: str

class QuestionHint(BaseModel):
    email: str
    question: str

class User(BaseModel):
    email: str
    name: str
    password: str
    subjects: list
    grades: dict | None = None
    predictedGrades: dict | None = None
    assignments: dict | None = None
    
class LoginDetails(BaseModel):
    email: str
    password: str
      
print("Redis connected:", r.ping())

def saveQuestionToRedis(questionHash: str, answers: list) -> None:
    questionHash = "questions/" + questionHash
    r.set(questionHash, json.dumps(answers))

def getQuestionFromRedis(questionHash: str) -> list or None:
    a = "questions/" + questionHash
    if (r.exists(a)):
        return json.loads(r.get(a))
    return None

def saveUserToRedis(email: str, user: dict):
    if (not r.exists(usersGroup + email)):
        createRedisUser(email, user["name"], user["password"], user["subjects"])

    r.set(usersGroup + email, json.dumps(user))

def createRedisUser(email: str, name: str, password: str, subjects: list) -> User or None:
    if (r.exists(usersGroup + email)):
        return None

    user = User(email=email, name=name, password=password, subjects=subjects, grades={}, predictedGrades={}, assignments={})

    r.set(usersGroup + email, json.dumps(user.dict()))

    return user

def getAllUsersFromRedis() -> dict:
    users = {}
    for key in r.scan_iter(usersGroup + "*"):
        users[key.decode("utf-8").replace(usersGroup, "")] = User(**json.loads(r.get(key)))
    return users

def createUser(email: str, name: str, password: str, subjects: list) -> User:
    if (email in userCache):
        return userCache[email]
    user = User(email=email, name=name, password=password, subjects=subjects, grades={}, predictedGrades={}, assignments={})

    
    createRedisUser(email, name, password, subjects)
    userCache[email] = user

    return userCache[email]

def getRedisUser(email: str) -> User or None:
    if (not r.exists(usersGroup + email)):
        return None
    m = json.loads(r.get(usersGroup + email))
    return User(**m)

def getUser(email: str) -> User or None:
    print(email)
    if (email in userCache):
        return userCache[email]
    
    user = getRedisUser(email)
    if (user == None):
        return None
    
    userCache[email] = user

    return user