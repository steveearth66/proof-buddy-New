from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from dill import dumps, loads
from django.core.cache import cache
import copy

User = get_user_model()


@api_view(["POST"])
def start_induction_proof(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_induction_proof(user)

    anchor_or_leap = 'anchor' if json_data['isAnchor'] else 'leap'
    pSide = 'lhs_' if json_data['side'] == 'LHS' else 'rhs_'
    currentProof = proof[pSide+anchor_or_leap]

    proof['current_proof'] = currentProof

    if not (json_data['inductionVariable'] in json_data['lhsGoal'] or json_data['rhsGoal']):
        errors = ["could not find IVar in either Induction goals"]
        proof['isValid'] = False
        return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)
    
    if (json_data['leapVariable'] in proof["lhs_leap"].ruleSet.keys()) or \
       (json_data['leapVariable'] in proof["rhs_leap"].ruleSet.keys()) or \
       (json_data['leapVariable'] in proof["lhs_anchor"].ruleSet.keys()) or \
       (json_data['leapVariable'] in proof["rhs_anchor"].ruleSet.keys()):
        errors = ["LVar found in the Ruleset, please choose another variable"]
        proof['isValid'] = False
        return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)
        
    anchorLHS = json_data['lhsGoal'].replace(json_data['inductionVariable'], json_data['inductionValue'])
    anchorRHS = json_data['rhsGoal'].replace(json_data['inductionVariable'], json_data['inductionValue'])
    leapLHS = json_data['lhsGoal'].replace(json_data['inductionVariable'], f"(+ 1 {json_data['inductionVariable']})")
    leapRHS = json_data['rhsGoal'].replace(json_data['inductionVariable'], f"(+ 1 {json_data['inductionVariable']})")

    proof['lhs_anchor'].addProofLine(anchorLHS)
    proof['rhs_anchor'].addProofLine(anchorRHS)
    proof['lhs_leap'].addProofLine(leapLHS)
    proof['rhs_leap'].addProofLine(leapRHS)

    proof = update_is_valid(proof)

    is_valid = proof["isValid"]
    errors, proof = get_errors_and_clear(proof)

    save_induction_proof_to_cache(user, proof)

    return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)


@api_view(["POST"])
def clear_induction(request):
    user = request.user
    clear_induction_proof(user)
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def add_definitions(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_induction_proof(user)

    try:
        if json_data["label"] not in proof["lhs_anchor"].ruleSet.keys():
            proof["lhs_anchor"].addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )

        if json_data["label"] not in proof["rhs_anchor"].ruleSet.keys():
            proof["rhs_anchor"].addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )
        
        if json_data["label"] not in proof["lhs_leap"].ruleSet.keys():
            proof["lhs_leap"].addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )
        if json_data["label"] not in proof["rhs_leap"].ruleSet.keys():
            proof["rhs_leap"].addUDF(
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

    save_induction_proof_to_cache(user, proof)

    return Response({"isValid": is_valid, "errors": errors}, status=status.HTTP_200_OK)

@api_view(["POST"])
def substitution(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_induction_proof(user)

    anchor_or_leap = 'anchor' if json_data['isAnchor'] else 'leap'
    pSide = 'lhs_' if json_data['side'] == 'LHS' else 'rhs_'
    currentProof = proof[pSide+anchor_or_leap]

    

    currentProof.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"], json_data["substitution"]
        )

    proof['current_proof'] = currentProof
    proof = update_is_valid(proof)
    is_valid = proof["isValid"]

    racket_str = (
        currentProof.getPrevRacket() if is_valid else "Error generating racket"
    )
    errors, proof = get_errors_and_clear(proof)

    save_induction_proof_to_cache(user, proof)

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

def clear_induction_proof(user):
    cache.delete(f"induction_proof_{user.username}")


def save_induction_proof_to_cache(user, proof):
    cache_proof = dumps(proof)
    cache.set(f"induction_proof_{user.username}", cache_proof)


def get_or_set_induction_proof(user):
    proof = {
        "lhs_leap": ERProof(),
        "rhs_leap": ERProof(),
        "lhs_anchor": ERProof(),
        "rhs_anchor": ERProof(),
        "current_proof": None,
        "isValid": True,
        "definitions": [],
    }
    cache_proof = dumps(proof)
    user_proof = cache.get_or_set(f"induction_proof_{user.username}", cache_proof)
    return loads(user_proof)

def get_errors_and_clear(proof):
    current_proof: ERProof = proof["current_proof"]

    if current_proof == None:
        return [], proof

    prev_errors = copy.deepcopy(current_proof.errLog)
    current_proof.errLog = []

    return prev_errors, proof

def update_is_valid(proof):
    current_proof: ERProof = proof["current_proof"]
    if current_proof == None:
        proof["isValid"] = True
    else:
        proof["isValid"] = current_proof.errLog == []

    return proof
