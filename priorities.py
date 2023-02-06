from predictions import ask, processHistoryForAnswer
from user import getUser

def rateDifficulty(assignments: list) -> list:
    difficulties = []
    for assignment in assignments:
        #ask ai to rate the difficulty of the assignment and scale it a 1-5 scale (1 being easiest) and add it to the list
        answer = ask("""
        Rate how difficult it would be to complete the following questions individually on a scale of 1.0-5.0, you can be in between two if needed (1.0 being easiest).
        Answer in the following format:
        Results:
        1) 1.0
        2) 2.0
        3) 3.0
        4) 2.7
        5) 4.2
        6) 2.5
        ...
        Questions:
        """ + assignment
        , 0, processHistoryForAnswer)

        answer = answer.strip()

        avg = 0.0
        i = 0
        for line in answer.splitlines():
            if (line.startswith("Results:")):
                continue

            i += 1
            avg += float(line.split(")")[1])
        avg /= i
        difficulties.append(avg)

    return difficulties


def getSubjectPriorities(email: str) -> list:
    #get the assignments for each subject
    assignments = getUser(email).assignments

    priorities = []
    points = rateDifficulty(assignments)



    return priorities

def rateAssignmentCount(count: int):
    rating = 0
    if count > 4:
        rating = 5
    else:
        rating = count
    
    return rating

def rateGradeFactor(grades: list):

    rating = 0
    averagePercent = 0
    for i in grades:
        sum += i
    averagePercent = averagePercent/len(grades)
    if averagePercent < 70:
        rating = 5
    elif averagePercent < 80:
        rating = 4
    elif averagePercent < 90:
        rating = 3
    elif averagePercent < 95:
        rating = 2
    elif averagePercent <= 100:
        rating = 1
    
    return rating
