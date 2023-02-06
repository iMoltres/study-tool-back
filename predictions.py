import os
import openai
import hashlib
from user import saveQuestionToRedis, getQuestionFromRedis

questionsCache = {
}

def getQuestion(prompt: str):
    prompt = hashlib.sha256(prompt.strip().lower().encode()).hexdigest();
    if (prompt in questionsCache):
        return questionsCache[prompt]

    if (getQuestionFromRedis(prompt) != None):
        questionsCache[prompt] = getQuestionFromRedis(prompt)
        return questionsCache[prompt]
    
    return None

def saveQuestion(prompt: str, history: list = []):
    prompt = hashlib.sha256(prompt.strip().lower().encode()).hexdigest();
    questionsCache[prompt] = history


def setup(api_key):
    openai.api_key = api_key

async def predictETA(email: str, assignments: list):
    a = "".join(assignments)
    print(a)
    return await ask(
        """
        IGNORE: """ + email + """
        Predict how long it will take to complete the following assignments by their name (in EXACT MINUTES):
        """ + a + """
        
        Respond by replacing the following text in all caps:
        ASSIGNMENT_NAME: TIME minutes
        """, 
        0.3, 
        ignore
    )

def ignore(historyList):
    pass

async def predictGrade(assignment: str) -> str:
    return await ask(
        """
        Predict what grade the following assignment would receive based on correctness and why (0% \- 100%):
        Respond by replacing the following text in all caps:
        Results: PERCENTAGE
        Reason: REASON
        """ + assignment, 
        0, 
        processHistoryForAnswer
    )

async def askStudyTips(count: int) -> str:
    text = await ask(
        """
        Give me """ + str(count) + """ study tips:
        Respond by replacing the following text in all caps:
        1. STUDY TIP
        2. STUDY TIP
        3. STUDY TIP
        ... (and so on)
        """, 
        0.3, 
        ignore
    )

    lines = text.splitlines()
    #remove 1. and 2. and 3. etc
    lines = [x.split(".")[1].strip().capitalize() for x in lines]
    return lines

async def hint(email: str, prompt: str):
    res = await ask(
        """
        IGNORE: """ + email + """
        Can you give me a HINT (NOT THE SOLUTION) for the following question?
        
        """ + prompt,
        0, 
        processHistoryForHint
    )
    return res

def processHistoryForHint(historyList):
    if (historyList[-1].startswith("Solution:")):
        return historyList[-1]

    historyList.append("Prompt: Give me the step-by-step solution with explanations for each step.\n")

def processHistoryForAnswer(historyList):
    if (historyList[-1].startswith("Results:")):
        print("Found " + historyList[-1])
        return historyList[-1]

async def ask(prompt: str, temperature: float, historyFound) -> str:
    #add history to prompt to give the ai context
    historyList = getQuestion(prompt)

    ogPrompt = prompt   
    if (historyList != None and len(historyList) > 0):
        his = historyFound(historyList)
        if (his != None):
            return his

        prompt = "".join(historyList)
    else:
        historyList = [prompt]


    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt + "\n",
        temperature=temperature,
        max_tokens=1024,
        top_p=1,
        best_of=2,
    )

    res: str = response.choices[0].text

    historyList.append(res.strip())
    saveQuestion(ogPrompt, historyList)

    return res