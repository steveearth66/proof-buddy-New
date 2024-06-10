from expression_tree.ERProofEngine import ERProof
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from proofs.models import Proof
from proofs.views import get_or_create_proof, user_proofs, user_proof, load_proof
from dill import dumps, loads
from django.core.cache import cache
import copy

User = get_user_model()


@api_view(["POST"])
def apply_rule(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    is_p_one_active = json_data["side"] == "LHS"
    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]

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

    proof = update_current_proof(proof, json_data["side"])
    proof = update_is_valid(proof)

    current_proof: ERProof = proof["currentProof"]
    is_valid = proof["isValid"]

    racket_str = (
        current_proof.getPrevRacket() if is_valid else "Error generating racket"
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
    user_proof = Proof.objects.filter(
        created_by=user, name=json_data["name"], tag=json_data["tag"]
    ).first()

    if user_proof:
        return Response(
            {
                "isValid": False,
                "errors": ["Proof with this name and tag already exists"],
            },
            status=status.HTTP_200_OK,
        )

    is_p_one_active = json_data["side"] == "LHS"
    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]
    current_proof = proof_one if is_p_one_active else proof_two

    current_proof.addProofLine(json_data["goal"])

    proof = update_current_proof(proof, json_data["side"])
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

    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]
    definitions = proof["definitions"]

    try:
        if json_data["label"] not in proof_one.ruleSet.keys():
            proof_one.addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )

        if json_data["label"] not in proof_two.ruleSet.keys():
            proof_two.addUDF(
                json_data["label"], json_data["type"], json_data["expression"]
            )
    except:
        return Response(
            {"message": "Error adding definition"}, status=status.HTTP_400_BAD_REQUEST
        )

    definitions.append(json_data)

    proof = update_current_proof(proof, "LHS")
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
    definitions = user_proof["definitions"]
    proof = get_or_create_proof(json_data, user, definitions)

    proof.isComplete = True
    proof.save()

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
    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]

    if is_p_one_active:
        if proof_one.getPrevRacket() != json_data["currentRacket"]:
            proof_two.addProofLine(
                json_data["currentRacket"],
                json_data["rule"],
                json_data["startPosition"],
                json_data["substitution"]
            )
        else:
            proof_one.addProofLine(
                json_data["currentRacket"],
                json_data["rule"],
                json_data["startPosition"],
                json_data["substitution"]
            )
    elif proof_two.getPrevRacket() != json_data["currentRacket"]:
        proof_one.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"], json_data["substitution"]
        )
    else:
        proof_two.addProofLine(
            json_data["currentRacket"], json_data["rule"], json_data["startPosition"], json_data["substitution"]
        )

    proof = update_current_proof(proof, json_data["side"])
    proof = update_is_valid(proof)

    current_proof: ERProof = proof["currentProof"]
    is_valid = proof["isValid"]

    racket_str = (
        current_proof.getPrevRacket() if is_valid else "Error generating racket"
    )
    errors, proof = get_errors_and_clear(proof)

    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "errors": errors},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def save_proof(request):
    data = request.data
    user = request.user
    user_proof = get_or_set_proof(user)
    definitions = user_proof["definitions"]
    proof = get_or_create_proof(data, user, definitions)

    if not proof:
        return Response(
            {"message": "Error creating proof"}, status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {"message": "Proof created successfully"}, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def get_user_proofs(request):
    user = request.user
    proof_data = user_proofs(user)

    return Response(proof_data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_proof(request, proof_id):
    user = request.user
    proof_data = user_proof(user, proof_id)

    proof = load_proof(proof_data)
    save_proof_to_cache(user, proof)

    return Response(proof_data, status=status.HTTP_200_OK)


def update_current_proof(proof, side):
    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]
    is_p_one_active = side == "LHS"

    current_proof = proof_one if is_p_one_active else proof_two

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
        return []

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
