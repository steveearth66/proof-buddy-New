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
    proof = Proof.objects.get(
        name=json_data['name'], tag=json_data['tag'], created_by=user)

    pOneIsActive = users_proof[user]['pOneIsActive']
    proofOne = users_proof[user]['proofOne']
    proofTwo = users_proof[user]['proofTwo']
    currentProof = proofOne

    proof_line_data = {
        'left_side': json_data['side'] == 'LHS',
        'racket': json_data['currentRacket'],
        'rule': json_data['rule'],
        'start_position': json_data['startPosition']
    }

    proof_line = ProofLineSerializer(data=proof_line_data)

    if not proof_line.is_valid():
        return Response(proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

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
    proof_line.save(proof=proof)

    isValid = users_proof[user]['isValid']

    racketStr = currentProof.getPrevRacket() if isValid else "Error generating racket"
    errors = getErrorsAndClear(user)

    return Response({'isValid': isValid, 'racket': racketStr, 'errors': errors}, status=status.HTTP_200_OK)


@api_view(['POST'])
def check_goal(request):
    global users_proof
    user = request.user
    json_data = request.data

    try:
        proof = Proof.objects.get(
            name=json_data['name'], tag=json_data['tag'], created_by=user)
    except Proof.DoesNotExist:
        proof_data = {
            'name': json_data['name'],
            'tag': json_data['tag']
        }
        serializer = ProofSerializer(data=proof_data)
        if serializer.is_valid():
            proof = serializer.save(created_by=user)


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
        proof_line_data = {
            'left_side': True,
            'racket': json_data['goal'],
            'rule': 'Premise',
        }

        proof_line = ProofLineSerializer(data=proof_line_data)

        if not proof_line.is_valid():
            return Response(proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        currentProof.addProofLine(json_data['goal'])
        proof.lsh = json_data['goal']
        proof.save()
        proof_line.save(proof=proof)
    else:
        proof_line_data = {
            'left_side': False,
            'racket': json_data['goal'],
            'rule': 'Premise',
        }

        proof_line = ProofLineSerializer(data=proof_line_data)

        if not proof_line.is_valid():
            return Response(proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        pOneIsActive = not pOneIsActive
        updateCurrentProof(user)
        currentProof = users_proof[user]['currentProof']
        currentProof.addProofLine(json_data['goal'])
        proof.rsh = json_data['goal']
        proof.save()
        proof_line.save(proof=proof)

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

    proof = Proof.objects.get(
        name=json_data['name'], tag=json_data['tag'], created_by=user)

    left_racket = json_data['leftRacketsAndRules'][-1]['racket']
    right_racket = json_data['rightRacketsAndRules'][-1]['racket']
    left_rule = json_data['leftRacketsAndRules'][-1]['rule']
    right_rule = json_data['rightRacketsAndRules'][-1]['rule']

    left_proof_line_data = {
        'left_side': True,
        'racket': left_racket,
        'rule': left_rule,
    }

    right_proof_line_data = {
        'left_side': False,
        'racket': right_racket,
        'rule': right_rule,
    }

    left_proof_line = ProofLineSerializer(data=left_proof_line_data)
    right_proof_line = ProofLineSerializer(data=right_proof_line_data)

    if not left_proof_line.is_valid():
        return Response(left_proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

    if not right_proof_line.is_valid():
        return Response(right_proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

    left_proof_line.save(proof=proof)
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
