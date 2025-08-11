from expression_tree.ERProofEngine import ERProof, ERProofLine, ERProofLine
from expression_tree.ERCommon import makeJson
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from proofs.models import Proof
from proofs.views import (
    get_or_create_proof,
    user_proofs,
    user_proof,
    load_proof,
    get_user_definitions,
    create_user_definition,
    create_or_override_definition,
    get_definition,
    edit_definition,
    delete_definition,
    get_user_generics,
    create_user_generic,
    use_generic,
    remove_generic,
    delete_generic
)
from dill import dumps, loads
from django.core.cache import cache
import copy

User = get_user_model()

@api_view(["POST"])
def apply_rule(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    errors, proof = add_proof_line(json_data, proof, json_data["side"])

    current_proof: ERProof = proof["currentProof"]
    is_valid = proof["isValid"]

    racket_str = (
        current_proof.getPrevRacket() if is_valid else "Error generating racket"
    )

    # this jsonTree is of the last proofline after the rule is applied
    jsonTree = makeJson(current_proof.proofLines[-1].exprTree)
    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "errors": errors, "jsonTree": jsonTree, "lineNum": max(0, len(current_proof.proofLines) - 1)},
        status=status.HTTP_200_OK,
    )

@api_view(["DELETE"])
def delete_line(request, side):
    user = request.user
    proof = get_or_set_proof(user)

    is_p_one_active = side == "LHS"
    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]

    # if LHS active, delete from LHS
    if is_p_one_active:
        proof_one.deleteProofLine()
    # else delete from RHS
    else:
        proof_two.deleteProofLine()

    save_proof_to_cache(user, proof)
    # next steps is to verify if I need to use update_current_proof
    # and update_is_valid
    # assume no... deletions should have less checks than additions
    # then use racket string and return response
    # use HTTP code that Javaughn recommeneded

    # not sure if this is neccessary
    # ----------------------------------------------------------------------------
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def check_goal(request):
    user = request.user
    json_data = request.data
    jsonTree = makeJson(ERProofLine(json_data["goal"]).exprTree)
    proof = get_or_set_proof(user)
    user_proof = Proof.objects.filter(
        created_by=user, name=json_data["name"], tag=json_data["tag"]
    ).first()

    if user_proof and user_proof.id != json_data["loadedProofId"]:
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

    if len(current_proof.proofLines) != 0:
        current_proof.proofLines.clear()
    
    current_proof.addProofLine(json_data["goal"])

    errors, proof = update_and_validate(proof, json_data["side"])
    is_valid = proof["isValid"]

    save_proof_to_cache(user, proof)

    return Response({"isValid": is_valid, "errors": errors, "jsonTree": jsonTree}, status=status.HTTP_200_OK)

# Set the current definition based on the UI's import file. 
# Any errors will result in the server proof state being unchanged EXCEPT for definitions
@api_view(["POST"])
def set_current_proof(request):
    user = request.user
    json_data = request.data

    # create a new proof!
    proof = {
        "proofOne": ERProof(),
        "proofTwo": ERProof(),
        "isValid": True,
        "currentProof": None,
        "definitions": [],
    }

    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]

    # set definitions. 
    # NOTE- This will override definitions with the same labels created by the user even if there is an error at any point in the validation
    errors = []
    for definition in json_data["definitions"]:
        saved_definition = create_or_override_definition(user, definition)
        if not saved_definition:
            errors.append("Unable to add definition with label " + definition["label"])
        else:
            label = saved_definition["label"]
            def_type = saved_definition["def_type"]
            expression = saved_definition["expression"]
            saved_definition["applied"] = True

            proof_one.addUDF(label, def_type, expression)
            proof_two.addUDF(label, def_type, expression)
            proof["definitions"].append(saved_definition)

    if len(errors) > 0:
        return get_error_response(errors)


    # Set LHS and RHS goals
    if json_data["leftGoalChecked"]:
        proof_one.addProofLine(json_data["lHSGoal"])
        errors, proof = update_and_validate(proof, "LHS")
        if not proof["isValid"]:
            return get_error_response(errors)

    if json_data["rightGoalChecked"]:
        proof_two.addProofLine(json_data["rHSGoal"])
        errors, proof = update_and_validate(proof, "RHS")
        if not proof["isValid"]:
            return get_error_response(errors)
    
    # Add all LHS and RHS and validate
    for side in {"LHS", "RHS"}:
        for line in json_data[side]:
            errors, proof = add_proof_line(line, proof, side)
            save_proof_to_cache(user, proof)
            if not proof["isValid"]:
                return get_error_response(errors)
            
    # Import Successful! Let's officiall overrite the cache
    # clear working cache for the user
    cache.delete(f"proofs_{user.username}")
    set_proof(user, proof)

    return Response(
        {"isValid": "True", "errors": []},
        status=status.HTTP_201_CREATED,
    )

def get_error_response(errors):
    return Response(
        {
            "isValid": False,
            "errors": errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )

def add_proof_line(line, proof, side):
    current = ("proofOne" if side == "LHS" else "proofTwo")
    other = ("proofTwo" if side == "LHS" else "proofOne")

    current_proof: ERProof = proof[current]

    if current_proof.getPrevRacket() != line["currentRacket"]:
        current_proof = proof[other]
    
    current_proof.addProofLine(
        line["currentRacket"],
        line["rule"],
        line["startPosition"],
    )
    
    return update_and_validate(proof, side)


def update_and_validate(proof, side):
    proof = update_current_proof(proof, side)
    proof = update_is_valid(proof)
    return get_errors_and_clear(proof)

@api_view(["POST"])
def add_definitions(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    proof_one: ERProof = proof["proofOne"]
    proof_two: ERProof = proof["proofTwo"]
    definitions = proof["definitions"]

    try:
        if json_data["expression"]:
            proof_one.addUDF(json_data["label"], json_data["type"], json_data["expression"])
            proof_two.addUDF(json_data["label"], json_data["type"], json_data["expression"])
        else:
            proof_one.addGeneric(json_data["label"], json_data["type"])
            proof_two.addGeneric(json_data["label"], json_data["type"])

    except:
        return Response(
            {"message": "Error adding definition"}, status=status.HTTP_400_BAD_REQUEST
        )

    if proof_one.errLog or proof_two.errLog:
        if proof["currentProof"] == proof_one or not proof["currentProof"]:
            errors = copy.deepcopy(proof_one.errLog)
        else:
            errors = copy.deepcopy(proof_two.errLog)
        proof_one.errLog.clear()
        proof_two.errLog.clear()
        return Response(
            {"message": errors}, status=status.HTTP_400_BAD_REQUEST)

    definition = create_user_definition(user, json_data)
    definition["applied"] = True
    definitions.append(definition)
    save_proof_to_cache(user, proof)
    return Response(definition, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
# def remove_definition(request, id):
def remove_definition(request, label):
    user = request.user
    proof = get_or_set_proof(user)

    definitions = proof["definitions"]
    proof["definitions"] = [
        # definition for definition in definitions if definition["id"] != id
        definition for definition in definitions if definition["label"] != label
    ]
    proof["proofOne"].removeUDF(label)
    proof["proofTwo"].removeUDF(label)

    save_proof_to_cache(user, proof)
    return Response(status=status.HTTP_200_OK)


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

    rule = json_data["rule"]

    if rule.lower() == "math":
        print("math", json_data["substitution"])
        rule = "advMath"

    if is_p_one_active:
        if proof_one.getPrevRacket() != json_data["currentRacket"]:
            proof_two.addProofLine(
                json_data["currentRacket"],
                rule,
                json_data["startPosition"],
                json_data["substitution"],
            )
        else:
            proof_one.addProofLine(
                json_data["currentRacket"],
                rule,
                json_data["startPosition"],
                json_data["substitution"],
            )
    elif proof_two.getPrevRacket() != json_data["currentRacket"]:
        proof_one.addProofLine(
            json_data["currentRacket"],
            rule,
            json_data["startPosition"],
            json_data["substitution"],
        )
    else:
        proof_two.addProofLine(
            json_data["currentRacket"],
            rule,
            json_data["startPosition"],
            json_data["substitution"],
        )

    proof = update_current_proof(proof, json_data["side"])
    proof = update_is_valid(proof)

    current_proof: ERProof = proof["currentProof"]
    is_valid = proof["isValid"]

    racket_str = (
        current_proof.getPrevRacket() if is_valid else "Error generating racket"
    )
    jsonTree = makeJson(current_proof.proofLines[-1].exprTree)
    errors, proof = get_errors_and_clear(proof)

    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "jsonTree": jsonTree, "errors": errors},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def save_proof(request):
    try:
        data = request.data
        user = request.user
        user_proof = get_or_set_proof(user)
        definitions = user_proof["definitions"]
        generics = user_proof["currentProof"].generics
        proof = get_or_create_proof(data, user, definitions, generics)

        if not proof:
            return Response(
                {"message": "Error saving proof"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Proof saved successfully"}, status=status.HTTP_201_CREATED
        )
    except:
        return Response(
            {"message": "Error saving proof"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
def get_user_proofs(request):
    user = request.user
    page = request.GET.get("page", 1)
    query = request.GET.get("query", "")
    proof_data = user_proofs(user, page, query)

    return Response(proof_data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_proof(request, proof_id):
    user = request.user
    proof_data = user_proof(user, proof_id)
    proof = load_proof(proof_data)

    frontend_json = {
        "name": proof_data["name"],
        "tag": proof_data["tag"],
        "lHSGoal": proof_data["lhs"],
        "rHSGoal": proof_data["rhs"],
        "leftRacketsAndRules": [],
        "rightRacketsAndRules": [],
        "definitions": proof_data["definitions"],
        "generics": proof_data["generics"],
        "loadedInServer": True
    }

    leftIndex = rightIndex = 0
    for line in proof_data["proofLines"]:
        if line.pop("leftSide"):
            line["jsonTree"] = makeJson(proof["proofOne"].proofLines[leftIndex].exprTree)
            if line["rule"] == "Premise":
                frontend_json["leftPremise"] = line
                frontend_json["lHSGoal"] = line["racket"]
            else:
                frontend_json["leftRacketsAndRules"].append(line)
            leftIndex += 1
        else:
            line["jsonTree"] = makeJson(proof["proofTwo"].proofLines[rightIndex].exprTree)
            if line["rule"] == "Premise":
                frontend_json["rightPremise"] = line
                frontend_json["rHSGoal"] = line["racket"]
            else:
                frontend_json["rightRacketsAndRules"].append(line)
            rightIndex += 1
    
    for side in ("left", "right"):
        if frontend_json.get(side + "Premise") is not None:
            frontend_json[side + "RacketsAndRules"].append(
                {
                    "racket": "",
                    "jsonTree": {},
                    "rule": "",
                    "deleted": False,
                    "errors": []
                }
            )
        else:
            frontend_json[side + "Premise"] = {
                "racket": proof_data["lhs"] if side == "left" else proof_data["rhs"],
                "rule": "Premise",
                "startPosition": 0
            }
            

    save_proof_to_cache(user, proof)

    return Response(frontend_json, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_definitions(request):
    user = request.user
    definitions = get_user_definitions(user)

    return Response(definitions, status=status.HTTP_200_OK)


@api_view(["GET"])
# def use_definition(request, id):
def use_definition(request, label):
    user = request.user
    # definition = get_definition(id)
    definition = get_definition(label)
    proof = get_or_set_proof(user)

    try:
        proof_one: ERProof = proof["proofOne"]
        proof_two: ERProof = proof["proofTwo"]
        definitions = proof["definitions"]

        for proof_definition in definitions:
            if proof_definition["label"] == definition["label"]:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        proof_one.addUDF(
            definition["label"], definition["type"], definition["expression"]
        )
        proof_two.addUDF(
            definition["label"], definition["type"], definition["expression"]
        )
        definition["applied"] = True
        definitions.append(definition)
        save_proof_to_cache(user, proof)

        return Response(status=status.HTTP_200_OK)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def update_definition(request):
    user = request.user
    json_data = request.data
    definition = edit_definition(user, json_data["label"], json_data)

    if not definition:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(definition, status=status.HTTP_200_OK)


@api_view(["DELETE"])
# def delete_definition_api(request, id):
def delete_definition_api(request, label):
    user = request.user
    # delete_definition(user, id)
    delete_definition(user, label)

    if not delete_definition:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_200_OK)

@api_view(["GET"])
def get_generics(request):
    user = request.user
    userProof = get_or_set_proof(user)
    enabledGenerics = userProof["proofOne"].generics
    generics = get_user_generics(user)
    for generic in generics:
        if generic["label"] in enabledGenerics.keys():
            generic["enabled"] = True
        else:
            generic["enabled"] = False
    return Response(generics, status=status.HTTP_200_OK)

@api_view(["POST"])
def add_generic(request):
    user = request.user
    data = request.data
    proof = get_or_set_proof(user)
    try:
        generic = create_user_generic(user, data)
        generic["enabled"] = True
    except Exception as e:
        return Response({ 'message': str(e) }, status=status.HTTP_400_BAD_REQUEST)
    for proofSide in (proof["proofOne"], proof["proofTwo"]):
        proofSide.addGeneric(data["label"], data["type"], data.get("restrictions"))
        if len(proofSide.errLog) != 0:
            error = proofSide.errLog[-1]
            proofSide.errLog.clear()
            return Response({ 'message': error }, status=status.HTTP_400_BAD_REQUEST)
    save_proof_to_cache(user, proof)
    return Response(generic, status=status.HTTP_201_CREATED)

@api_view(["GET"])
def enable_generic(request, id):
    user = request.user
    proof = get_or_set_proof(user)
    use_generic(proof, id)
    errors, proof = get_errors_and_clear(proof)
    if len(errors) != 0:
        return Response({'message': errors[-1]}, status=status.HTTP_400_BAD_REQUEST)
    save_proof_to_cache(user, proof)
    return Response(status=status.HTTP_200_OK)

@api_view(["DELETE"])
def disable_generic(request, id):
    user = request.user
    proof = get_or_set_proof(user)
    remove_generic(proof, id)
    save_proof_to_cache(user, proof)
    return Response(status=status.HTTP_200_OK)

@api_view(["DELETE"])
def delete_generic_api(request, id):
    user = request.user
    proof = get_or_set_proof(user)
    try:
        delete_generic(proof, id)
        save_proof_to_cache(user, proof)
        return Response(status=status.HTTP_200_OK)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)

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
        errors = proof['proofOne'].errLog + proof['proofTwo'].errLog
        proof['proofOne'].errLog.clear()
        proof['proofTwo'].errLog.clear()
        return errors, proof

    prev_errors = copy.deepcopy(current_proof.errLog)
    current_proof.errLog = []

    return prev_errors, proof


def clear_user_proofs(user):
    cache.delete(f"proofs_{user.username}")


def save_proof_to_cache(user, proof):
    cache_proofs = dumps(proof)
    cache.set(f"proofs_{user.username}", cache_proofs)


def get_or_set_proof(user):
    # NOTE: 'proofOne' and 'proofTwo' should have the same Ruleset and generics.
    # May be favorable to find a way to link these attributes
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

def set_proof(user, proof):
    cache_proofs = dumps(proof)
    cache.set(f"proofs_{user.username}", cache_proofs)
