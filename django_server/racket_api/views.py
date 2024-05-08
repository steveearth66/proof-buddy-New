from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
import copy
from proofs.serializers import ProofSerializer, ProofLineSerializer, DefinitionSerializer
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
            'currentProof': None,
            'definitions': []
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
            'currentProof': None,
            'definitions': []
        }

    proofOne = users_proof[user]['proofOne']
    proofTwo = users_proof[user]['proofTwo']
    definitions = users_proof[user]['definitions']

    if json_data['label'] not in proofOne.ruleSet.keys():
        proofOne.addUDF(
            json_data['label'], json_data['type'], json_data['expression'])

    if proofTwo != None:
        if json_data['label'] not in proofTwo.ruleSet.keys():
            proofTwo.addUDF(
                json_data['label'], json_data['type'], json_data['expression'])

    definitions.append(json_data)

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
    proof = create_proof(json_data, user)

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

    create_proof_lines(left_rackets_and_rules, True, proof)
    create_proof_lines(right_rackets_and_rules, False, proof)

    proof.isComplete = True
    proof.save()

    definitions = users_proof[user]['definitions']
    create_proof_definitions(definitions, proof, user)

    clearProofs(user)

    return Response(status=status.HTTP_200_OK)


def create_proof(data, user):
    proof_data = {
        'name': data['name'],
        'tag': data['tag'],
        'lsh': data['lHSGoal'],
        'rsh': data['rHSGoal'],
    }

    serializer = ProofSerializer(data=proof_data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return serializer.save(created_by=user)



def create_proof_lines(lines, left_side, proof):
    for line in lines:
        racket = line['racket']
        rule = line['rule']
        try:
            start_position = line['startPosition']
        except:
            start_position = 0

        proof_line_data = {
            'left_side': left_side,
            'racket': racket,
            'rule': rule,
            'start_position': start_position
        }

        proof_line = ProofLineSerializer(data=proof_line_data)

        if not proof_line.is_valid():
            return Response(proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        proof_line.save(proof=proof)


def create_proof_definitions(definitions, proof, user):
    for definition in definitions:
        definition_data = {
            'label': definition['label'],
            'def_type': definition['type'],
            'expression': definition['expression'],
            'notes': definition['notes']
        }

        definition_serializer = DefinitionSerializer(data=definition_data)

        if not definition_serializer.is_valid():
            return Response(definition_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        definition_serializer.save(proof=proof, created_by=user)

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
