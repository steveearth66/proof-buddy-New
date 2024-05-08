from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
import copy
from proofs.serializers import ProofSerializer, ProofLineSerializer
from proofs.models import Proof

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


@api_view(['POST'])
def complete_proof(request):
    global users_proof
    user = request.user
    json_data = request.data

    proof_data = {
        'name': json_data['name'],
        'tag': json_data['tag'],
        'lsh': json_data['lHSGoal'],
        'rsh': json_data['rHSGoal'],
    }

    serializer = ProofSerializer(data=proof_data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    proof = serializer.save(created_by=user)

    left_premise_data = json_data['leftPremise']
    left_premise_data = {
        'left_side': True,
        'racket': left_premise_data['racket'],
        'rule': left_premise_data['rule'],
        'start_position': left_premise_data['startPosition']
    }
    right_premise_data = json_data['rightPremise']
    right_premise_data = {
        'left_side': False,
        'racket': right_premise_data['racket'],
        'rule': right_premise_data['rule'],
        'start_position': right_premise_data['startPosition']
    }
    left_rackets_and_rules = json_data['leftRacketsAndRules']
    right_rackets_and_rules = json_data['rightRacketsAndRules']

    left_premise = ProofLineSerializer(data=left_premise_data)
    right_premise = ProofLineSerializer(data=right_premise_data)

    if not left_premise.is_valid():
        return Response(left_premise.errors, status=status.HTTP_400_BAD_REQUEST)

    if not right_premise.is_valid():
        return Response(right_premise.errors, status=status.HTTP_400_BAD_REQUEST)

    left_premise.save(proof=proof)
    right_premise.save(proof=proof)

    for i in range(len(left_rackets_and_rules)):
        left_racket = left_rackets_and_rules[i - 1]['racket']
        left_rule = left_rackets_and_rules[i]['rule']
        try:
            start_position = left_rackets_and_rules[i]['startPosition']
        except:
            start_position = 0

        left_proof_line_data = {
            'left_side': True,
            'racket': left_racket,
            'rule': left_rule,
            'start_position': start_position
        }

        left_proof_line = ProofLineSerializer(data=left_proof_line_data)

        if not left_proof_line.is_valid():
            return Response(left_proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        left_proof_line.save(proof=proof)

    for i in range(len(right_rackets_and_rules)):
        right_racket = right_rackets_and_rules[i]['racket']
        right_rule = right_rackets_and_rules[i]['rule']
        try:
            start_position = right_rackets_and_rules[i]['startPosition']
        except:
            start_position = 0

        right_proof_line_data = {
            'left_side': False,
            'racket': right_racket,
            'rule': right_rule,
            'start_position': start_position
        }

        right_proof_line = ProofLineSerializer(data=right_proof_line_data)

        if not right_proof_line.is_valid():
            return Response(right_proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        right_proof_line.save(proof=proof)



    proof.isComplete = True
    proof.save()
    clearProofs(user)

    return Response(status=status.HTTP_200_OK)


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


def clearProofs(user):
    global users_proof
    del users_proof[user]
