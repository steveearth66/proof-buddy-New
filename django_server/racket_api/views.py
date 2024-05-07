from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
import copy

User = get_user_model()

users_proof = {}


@api_view(['POST'])
def apply_rule(request):
    global users_proof
    user = request.user
    json_data = request.data

    pOneIsActive = users_proof[user]['pOneIsActive']
    proofOne = users_proof[user]['proofOne']
    proofTwo = users_proof[user]['proofTwo']
    currentProof = proofOne

    if pOneIsActive:
        if proofOne.getPrevRacket() != json_data['currentRacket']:
            pOneIsActive = False
            proofTwo.addProofLine(
                json_data['currentRacket'], json_data['rule'], json_data['startPosition'])
        else:
            proofOne.addProofLine(
                json_data['currentRacket'], json_data['rule'], json_data['startPosition'])
    elif proofTwo.getPrevRacket() != json_data['currentRacket']:
        pOneIsActive = True
        proofOne.addProofLine(
            json_data['currentRacket'], json_data['rule'], json_data['startPosition'])
    else:
        proofTwo.addProofLine(
            json_data['currentRacket'], json_data['rule'], json_data['startPosition'])

    updateCurrentProof(user)
    updateIsValid(user)

    isValid = users_proof[user]['isValid']

    racketStr = currentProof.getPrevRacket() if isValid else "Error generating racket"
    errors = getErrorsAndClear(user)

    return Response({'isValid': isValid, 'racket': racketStr, 'errors': errors}, status=status.HTTP_200_OK)


@api_view(['POST'])
def check_goal(request):
    global users_proof
    user = request.user
    json_data = request.data

    if user not in users_proof:
        users_proof[user] = {
            'proofOne': ERProof(),
            'proofTwo': ERProof(),
            'isValid': True,
            'pOneIsActive': True,
            'currentProof': None
        }

    pOneIsActive = users_proof[user]['pOneIsActive']
    proofOne = users_proof[user]['proofOne']
    proofTwo = users_proof[user]['proofTwo']
    currentProof = proofOne

    if currentProof.proofLines == []:
        currentProof.addProofLine(json_data['goal'])
    else:
        pOneIsActive = not pOneIsActive
        updateCurrentProof(user)
        currentProof = users_proof[user]['currentProof']
        currentProof.addProofLine(json_data['goal'])

    updateIsValid(user)
    isValid = users_proof[user]['isValid']
    errors = getErrorsAndClear(user)

    return Response({'isValid': isValid, 'errors': errors}, status=status.HTTP_200_OK)


@api_view(['POST'])
def add_definitions(request):
    global users_proof
    user = request.user
    json_data = request.data

    if user not in users_proof:
        users_proof[user] = {
            'proofOne': ERProof(),
            'proofTwo': ERProof(),
            'isValid': True,
            'pOneIsActive': True,
            'currentProof': None
        }

    proofOne = users_proof[user]['proofOne']
    proofTwo = users_proof[user]['proofTwo']

    if json_data['label'] not in proofOne.ruleSet.keys():
        proofOne.addUDF(
            json_data['label'], json_data['type'], json_data['expression'])

    if proofTwo != None:
        if json_data['label'] not in proofTwo.ruleSet.keys():
            proofTwo.addUDF(
                json_data['label'], json_data['type'], json_data['expression'])

    updateCurrentProof(user)
    updateIsValid(user)
    errors = getErrorsAndClear(user)
    isValid = users_proof[user]['isValid']

    return Response({'isValid': isValid, 'errors': errors}, status=status.HTTP_200_OK)


def updateCurrentProof(user):
    global users_proof

    proofOne = users_proof[user]['proofOne']
    proofTwo = users_proof[user]['proofTwo']
    pOneIsActive = users_proof[user]['pOneIsActive']

    currentProof = proofOne if pOneIsActive else proofTwo

    users_proof[user]['currentProof'] = currentProof


def updateIsValid(user):
    global users_proof

    currentProof = users_proof[user]['currentProof']

    if currentProof == None:
        users_proof[user]['isValid'] = True
    else:
        users_proof[user]['isValid'] = currentProof.errLog == []


def getErrorsAndClear(user):
    global users_proof

    currentProof = users_proof[user]['currentProof']

    if currentProof == None:
        return []

    prevErrors = copy.deepcopy(currentProof.errLog)
    currentProof.errLog = []

    return prevErrors
