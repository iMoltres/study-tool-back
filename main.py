import threading
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import unquote
from user import *
from predictions import hint, ask, setup, questionsCache, predictGrade, predictETA, askStudyTips
from priorities import *

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def saveCache():
    #save user cache to redis
    for (email, user) in userCache.items():
        # save user to redis
        saveUserToRedis(email, user.dict())
    #save question cache to redis
    for (prompt, history) in questionsCache.items():
        saveQuestionToRedis(prompt, history)

def loadUsersFromRedis():
    #load user cache from redis
    for (email, user) in getAllUsersFromRedis().items():
        print("Loading user:", email)
        userCache[email] = user

setup(os.getenv("OPENAI_API_KEY"))
process = threading.Timer(300, saveCache)

@app.on_event("startup")
async def startup_event():
    process.start()
    loadUsersFromRedis()

@app.on_event("shutdown")
async def shutdown_event():
    saveCache()
    process.cancel()

@app.post("/login")
async def login(details: LoginDetails) -> dict:
    #if email doesn't exist then respond with an error
    if (details.email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    
    #if password is incorrect then respond with an error
    passwordEntered = details.password;

    user = getUser(details.email)
    if (user.password != hashlib.sha256(passwordEntered.encode()).hexdigest()):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    #if email and password are correct then respond with a token
    return {"detail": "OK"}

@app.post("/signup", response_model=User)
async def signup(user: User):
    #if email already exists then respond with an error
    if (user.email in userCache):
        raise HTTPException(status_code=400, detail="Email already exists")
    user = createUser(user.email, user.name, hashlib.sha256(user.password.encode()).hexdigest(), user.subjects)

    return user

@app.post("/questionHint")
async def getQuestionHint(a: QuestionHint):
    email = a.email
    question = a.question

    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    question = unquote(question)
    
    return {"questionHint": await hint(email, question)}

@app.post("/predictGrade")
async def getPredictedGrade(a: PredictedGrade):
    email = a.email
    assignment_name = "random"
    assignment_content = a.assignment
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    
    assignment_content = unquote(assignment_content)
    ans = (await predictGrade(assignment_content)).strip()

    # parse percentage out of prediction
    print(ans)
    reason = ans.splitlines()[1].strip().split(":")[1].strip()

    percentage = ans.splitlines()[0].strip().split(":")[1].strip()

    prediction = {
        assignment_name: {
            "percentage": percentage,
            "reason": reason
        }
    }

    user = getUser(email)
    user.predictedGrades.update(prediction)
    userCache[email] = user

    return prediction


@app.get("/user/{email}/all")
async def getAllUserProps(email: str):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    return getUser(email)

@app.get("/user/{email}/name")
async def getNameUserProps(email: str):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")

    return getUser(email).name

@app.get("/user/{email}/assignments")
async def getAssignmentsUserProps(email: str):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    return {"assignments": getUser(email).assignments}

@app.post("/user/{email}/assignments")
async def editAssignments(email: str, assignments: list):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    user = getUser(email)

    eta: str = await predictETA(email, assignments)

    eta: list = eta.splitlines()
    eta = [x.split(":")[1].strip() for x in eta]
    
    gradesDict = {}
    i = 0
    for assignment in assignments:
        print(eta[i])
        gradesDict[assignment] = {
            "eta": int(eta[i].lower().replace("minutes", ""))
        }
        i += 1


    user.assignments = assignments
    userCache[email] = user
    return {"assignments": user.assignments}

@app.get("/user/{email}/grades")
async def getGradesUserProps(email: str):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    return {"grades": getUser(email).grades}

@app.post("/user/{email}/grades")
async def editGrades(email: str, grades: dict):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    user = getUser(email)

    user.grades = grades
    userCache[email] = user

    return user

@app.get("/studytips/{count}")
async def getStudyTips(count: int):
    studyTips = await askStudyTips(count)
    return {"studyTips": studyTips}

@app.get("/user/{email}/subjects")
async def getSubjectsUserProps(email: str):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    return getUser(email).subjects

@app.post("/user/{email}/subjects")
async def editSubjects(email: str, subjects: list):
    if (email not in userCache):
        raise HTTPException(status_code=400, detail="Email doesn't exist")
    user = getUser(email)
    user.subjects = subjects
    userCache[email] = user

    return user
