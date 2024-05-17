from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
import copy
from proofs.serializers import (
    ProofSerializer,
    ProofLineSerializer,
    DefinitionSerializer,
)

User = get_user_model()

users_proof = {}


@api_view(["POST"])
def apply_rule(request):
    global users_proof
    user = request.user
    json_data = request.data

    is_p_one_active = json_data["side"] == "LHS"
    proof_one: ERProof = users_proof[user]["proofOne"]
    proof_two: ERProof = users_proof[user]["proofTwo"]

    if is_p_one_active:
        if proof_one.getPrevRacket() != json_data["currentRacket"]:
            proof_two.addProofLine(
                json_data["currentRacket"],
                json_data["rule"],
                json_data["startPosition"],
            )
        else:
            proof_one.addProofLine(
                json_data["currentRacket"],
                json_data["rule"],
                json_data["startPosition"],
            )
    elif proof_two.getPrevRacket() != json_data["currentRacket"]:
        proof_one.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"]
        )
    else:
        proof_two.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"]
        )

    update_current_proof(user, json_data["side"])
    update_is_valid(user)

    current_proof: ERProof = users_proof[user]["currentProof"]
    is_valid = users_proof[user]["isValid"]

    racket_str = (
        current_proof.getPrevRacket() if is_valid else "Error generating racket"
    )
    errors = get_errors_and_clear(user)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "errors": errors},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def check_goal(request):
    global users_proof
    user = request.user
    json_data = request.data

    create_user_proof(user)

    is_p_one_active = json_data["side"] == "LHS"
    proof_one: ERProof = users_proof[user]["proofOne"]
    proof_two: ERProof = users_proof[user]["proofTwo"]
    current_proof = proof_one if is_p_one_active else proof_two

    current_proof.addProofLine(json_data["goal"])

    update_current_proof(user, json_data["side"])
    is_valid = users_proof[user]["isValid"]
    errors = get_errors_and_clear(user)

    return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)


@api_view(["POST"])
def add_definitions(request):
    global users_proof
    user = request.user
    json_data = request.data

    create_user_proof(user)

    proof_one: ERProof = users_proof[user]["proofOne"]
    proof_two: ERProof = users_proof[user]["proofTwo"]
    definitions = users_proof[user]["definitions"]

    if json_data["label"] not in proof_one.ruleSet.keys():
        proof_one.addUDF(json_data["label"], json_data["type"], json_data["expression"])

    if json_data["label"] not in proof_two.ruleSet.keys():
        proof_two.addUDF(json_data["label"], json_data["type"], json_data["expression"])

    definitions.append(json_data)

    update_is_valid(user)
    errors = get_errors_and_clear(user)
    is_valid = users_proof[user]["isValid"]

    return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)


@api_view(["POST"])
def complete_proof(request):
    global users_proof
    user = request.user
    json_data = request.data
    proof = create_proof(json_data, user)

    left_premise_data = json_data["leftPremise"]
    left_premise_data = {
        "left_side": True,
        "racket": left_premise_data["racket"],
        "rule": left_premise_data["rule"],
        "start_position": left_premise_data["startPosition"],
    }
    right_premise_data = json_data["rightPremise"]
    right_premise_data = {
        "left_side": False,
        "racket": right_premise_data["racket"],
        "rule": right_premise_data["rule"],
        "start_position": right_premise_data["startPosition"],
    }
    left_rackets_and_rules = json_data["leftRacketsAndRules"]
    right_rackets_and_rules = json_data["rightRacketsAndRules"]

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

    definitions = users_proof[user]["definitions"]
    create_proof_definitions(definitions, proof, user)

    clear_user_proofs(user)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def clear_proof(request):
    global users_proof
    user = request.user

    clear_user_proofs(user)

    return Response(status=status.HTTP_200_OK)


def create_proof(data, user):
    proof_data = {
        "name": data["name"],
        "tag": data["tag"],
        "lsh": data["lHSGoal"],
        "rsh": data["rHSGoal"],
    }

    serializer = ProofSerializer(data=proof_data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return serializer.save(created_by=user)


def create_proof_lines(lines, left_side, proof):
    for line in lines:
        racket = line["racket"]
        rule = line["rule"]
        try:
            start_position = line["startPosition"]
        except:
            start_position = 0

        proof_line_data = {
            "left_side": left_side,
            "racket": racket,
            "rule": rule,
            "start_position": start_position,
        }

        proof_line = ProofLineSerializer(data=proof_line_data)

        if not proof_line.is_valid():
            return Response(proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        proof_line.save(proof=proof)


def create_proof_definitions(definitions, proof, user):
    for definition in definitions:
        definition_data = {
            "label": definition["label"],
            "def_type": definition["type"],
            "expression": definition["expression"],
            "notes": definition["notes"],
        }

        definition_serializer = DefinitionSerializer(data=definition_data)

        if not definition_serializer.is_valid():
            return Response(
                definition_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        definition_serializer.save(proof=proof, created_by=user)


def update_current_proof(user, side):
    global users_proof

    proof_one: ERProof = users_proof[user]["proofOne"]
    proof_two: ERProof = users_proof[user]["proofTwo"]
    is_p_one_active = side == "LHS"

    current_proof = proof_one if is_p_one_active else proof_two

    users_proof[user]["currentProof"] = current_proof


def update_is_valid(user):
    global users_proof

    current_proof: ERProof = users_proof[user]["currentProof"]

    if current_proof == None:
        users_proof[user]["isValid"] = True
    else:
        users_proof[user]["isValid"] = current_proof.errLog == []


def get_errors_and_clear(user):
    global users_proof

    current_proof: ERProof = users_proof[user]["currentProof"]

    if current_proof == None:
        return []

    prev_errors = copy.deepcopy(current_proof.errLog)
    current_proof.errLog = []

    return prev_errors


def clear_user_proofs(user):
    global users_proof

    try:
        del users_proof[user]
    except:
        return None


def create_user_proof(user):
    global users_proof

    if user not in users_proof:
        users_proof[user] = {
            "proofOne": ERProof(),
            "proofTwo": ERProof(),
            "isValid": True,
            "currentProof": None,
            "definitions": [],
        }
