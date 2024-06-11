from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
import copy
from proofs.serializers import ProofSerializer, ProofLineSerializer, DefinitionSerializer
from proofs.views import create_proof, create_proof_lines, create_proof_definitions
from dill import dumps, loads
from django.core.cache import cache

User = get_user_model()


@api_view(["POST"])
def apply_rule(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    is_p_one_active = json_data["side"] == "LHS"
    p = proof["proofOne"] if is_p_one_active else proof['proofTwo']

    p.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"]
        )
    
    proof['currentProof'] = p
    proof = update_is_valid(proof)
    is_valid = proof["isValid"]

    racket_str = (
        p.getPrevRacket() if is_valid else "Error generating racket"
    )
    errors, proof = get_errors_and_clear(proof)

    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "errors": errors},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def check_goal(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    is_p_one_active = json_data["side"] == "LHS"

    p = proof["proofOne"] if is_p_one_active else proof['proofTwo']

    p.addProofLine(json_data["goal"])

    proof['currentProof'] = p
    proof = update_is_valid(proof)

    is_valid = proof["isValid"]
    errors, proof = get_errors_and_clear(proof)

    save_proof_to_cache(user, proof)

    return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)


@api_view(["POST"])
def add_definitions(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    try:
        if json_data["label"] not in proof["proofOne"].ruleSet.keys():
            proof["proofOne"].addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )

        if json_data["label"] not in proof["proofTwo"].ruleSet.keys():
            proof["proofTwo"].addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )
    except:
        return Response(
            {"message": "Error adding definition"}, status=status.HTTP_400_BAD_REQUEST
        )

    proof["definitions"].append(json_data)
    
    proof = update_is_valid(proof)
    errors, proof = get_errors_and_clear(proof)
    is_valid = proof["isValid"]

    save_proof_to_cache(user, proof)

    return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)


@api_view(["POST"])
def complete_proof(request):
    user = request.user
    json_data = request.data
    user_proof = get_or_set_proof(user)
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

    definitions = user_proof["definitions"]
    create_proof_definitions(definitions, proof, user)

    clear_user_proofs(user)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def clear_proof(request):
    user = request.user

    clear_user_proofs(user)

    return Response(status=status.HTTP_200_OK)


# called from the substitution window (generate and check), not from the main proof window
@api_view(["POST"])
def substitution(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    is_p_one_active = json_data["side"] == "LHS"
    p = proof["proofOne"] if is_p_one_active else proof['proofTwo']

    p.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"], json_data["substitution"]
        )

    proof['currentProof'] = p
    proof = update_is_valid(proof)
    is_valid = proof["isValid"]

    racket_str = (
        p.getPrevRacket() if is_valid else "Error generating racket"
    )
    errors, proof = get_errors_and_clear(proof)

    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "errors": errors},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def edit_udf(request):
    pass
@api_view(["POST"])
def remove_udf(request):
    pass

def create_proof(data, user):
    proof_data = {
        "name": data["name"],
        "tag": data["tag"],
        "lhs": data["lHSGoal"],
        "rhs": data["rHSGoal"],
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


def update_current_proof(user, newProofObj, side):

    proof = get_or_set_proof(user)

    is_p_one_active = side == "LHS"

    current_proof = proof['proofOne'] if is_p_one_active else proof["proofTwo"]
    print('DEBUG: ',[str(l) for l in current_proof.proofLines])

    proof["currentProof"] = current_proof

    return proof


def update_is_valid(proof):
    current_proof: ERProof = proof["currentProof"]

    if current_proof == None:
        proof["isValid"] = True
    else:
        proof["isValid"] = current_proof.errLog == []

    return proof


def get_errors_and_clear(proof):
    current_proof: ERProof = proof["currentProof"]

    if current_proof == None:
        return [], proof

    prev_errors = copy.deepcopy(current_proof.errLog)
    current_proof.errLog = []

    return prev_errors, proof


def clear_user_proofs(user):
    cache.delete(f"proofs_{user.username}")


def save_proof_to_cache(user, proof):
    cache_proofs = dumps(proof)
    cache.set(f"proofs_{user.username}", cache_proofs)


def get_or_set_proof(user):
    proof = {
        "proofOne": ERProof(),
        "proofTwo": ERProof(),
        "isValid": True,
        "currentProof": None,
        "definitions": [],
    }
    cache_proofs = dumps(proof)
    user_proof = cache.get_or_set(f"proofs_{user.username}", cache_proofs)
    proof = loads(user_proof)
    return proof
