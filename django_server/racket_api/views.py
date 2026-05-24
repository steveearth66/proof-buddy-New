from expression_tree.ERProofEngine import TwoSidedProof, ERProof, ERProofLine
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
    delete_generic,
    use_uploaded_generic
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

    errors = add_proof_line(json_data, proof, json_data["side"])
    is_valid = proof.isValid

    racket_str = (
        proof.currentSide.getPrevRacket() if is_valid else "Error generating racket"
    )

    # this jsonTree is of the last proofline after the rule is applied
    jsonTree = makeJson(proof.currentSide.proofLines[-1].exprTree)
    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": is_valid, "racket": racket_str, "errors": errors, "jsonTree": jsonTree, "lineNum": max(0, len(proof.currentSide.proofLines) - 1)},
        status=status.HTTP_200_OK,
    )

@api_view(["DELETE"])
def delete_line(request, side):
    user = request.user
    proof = get_or_set_proof(user)

    proof.setCurrentSide(side)
    proof.currentSide.deleteProofLine()

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
    proof = get_or_set_proof(user)
    user_proof = Proof.objects.filter(
        created_by=user, name=json_data["name"], tag=json_data["tag"]
    ).first()

    # Use .get() with default None to handle missing loadedProofId gracefully
    loaded_proof_id = json_data.get("loadedProofId", None)
    if user_proof and loaded_proof_id and user_proof.id != loaded_proof_id:
        return Response(
            {
                "isValid": False,
                "errors": ["Proof with this name and tag already exists"],
            },
            status=status.HTTP_200_OK,
        )
    
    proof.setCurrentSide(json_data['side'])

    if len(proof.currentSide.proofLines) != 0:
        proof.currentSide.proofLines.clear()
    
    proof.currentSide.addProofLine(json_data["goal"])
    errors = update_and_validate(proof, json_data["side"])

    jsonTree = makeJson(proof.currentSide.proofLines[-1].exprTree) if proof.isValid else None

    save_proof_to_cache(user, proof)

    return Response({"isValid": proof.isValid, "errors": errors, "jsonTree": jsonTree}, status=status.HTTP_200_OK)

# Set the current definition based on the UI's import file. 
# Any errors will result in the server proof state being unchanged EXCEPT for definitions
@api_view(["POST"])
def set_current_proof(request):
    import sys
    print("[DEBUG] set_current_proof called", flush=True)  # Log to console for debugging
    sys.stdout.flush()
    user = request.user
    json_data = request.data
    print(f"[DEBUG] User: {user.username}, Data keys: {json_data.keys()}", flush=True)  # Log to console for debugging
    sys.stdout.flush()

    try:
        # create a new proof!
        proof = TwoSidedProof()

        # set definitions. 
        # NOTE- This will override definitions with the same labels created by the user even if there is an error at any point in the validation
        errors = []
        for definition in json_data["definitions"]:
            # Check if this is a default UDF (skip database operations)
            is_default = definition.get("is_default", False) or definition.get("deletable", True) == False
            
            if is_default:
                # Default UDFs don't need database operations, just apply to proof
                label = definition["label"]
                def_type = definition["type"]
                expression = definition["expression"]
                proof.addUDF(label, def_type, expression)
                proof.definitions.append({
                    "label": label,
                    "def_type": def_type,
                    "expression": expression,
                    "applied": True
                })
            else:
                # User-created definitions need database operations
                saved_definition = create_or_override_definition(user, definition)
                if not saved_definition:
                    errors.append("Unable to add definition with label " + definition["label"])
                else:
                    label = saved_definition["label"]
                    def_type = saved_definition["def_type"]
                    expression = saved_definition["expression"]
                    saved_definition["applied"] = True

                    proof.addUDF(label, def_type, expression)
                    proof.definitions.append(saved_definition)
        
        for generic in json_data["generics"]:
            try:
                use_uploaded_generic(user, proof, generic)
            except Exception as e:
                errors.append(str(e))

        if len(errors) > 0:
            return get_error_response(errors)


        # Set LHS and RHS goals
        if json_data["leftGoalChecked"]:
            proof.LHS.addProofLine(json_data["lHSGoal"])
            errors = update_and_validate(proof, "LHS")
            if not proof.isValid:
                return get_error_response(errors)

        if json_data["rightGoalChecked"]:
            proof.RHS.addProofLine(json_data["rHSGoal"])
            errors = update_and_validate(proof, "RHS")
            if not proof.isValid:
                return get_error_response(errors)
        
        # Add all LHS and RHS and validate
        for side in ("LHS", "RHS"):
            for line in json_data[side]:
                errors = add_proof_line(line, proof, side)
                if not proof.isValid:
                    return get_error_response(errors)
                save_proof_to_cache(user, proof)
                
        # Import Successful! Let's officiall overrite the cache
        # clear working cache for the user
        cache.delete(f"proofs_{user.username}")
        save_proof_to_cache(user, proof)

        return Response(
            {"isValid": "True", "errors": []},
            status=status.HTTP_201_CREATED,
        )
    
    except Exception as e:
        import traceback
        error_msg = f"Exception in set_current_proof: {str(e)}"
        print(error_msg)  # Log to console for debugging
        print(traceback.format_exc())  # Log full stack trace for debugging
        return Response(
            {"isValid": False, "errors": [error_msg]},
            status=status.HTTP_400_BAD_REQUEST,
        )

def get_error_response(errors):
    print(f"[ERROR] Returning error response: {errors}")  # Log to console for debugging
    return Response(
        {
            "isValid": False,
            "errors": errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )

def add_proof_line(line, proof: TwoSidedProof, side: str):
    proof.setCurrentSide(side)

    if proof.currentSide.getPrevRacket() != line["currentRacket"]:
        proof.toggleSide()
    
    proof.currentSide.addProofLine(
        line["currentRacket"],
        line["rule"],
        line["startPosition"],
    )
    
    return update_and_validate(proof, side)


def update_and_validate(proof: TwoSidedProof, side):
    proof.setCurrentSide(side)
    proof.updateErrorsAndValidate()
    return proof.getErrorsAndClear()

@api_view(["POST"])
def add_definitions(request):
    user = request.user
    json_data = request.data
    proof = get_or_set_proof(user)

    try:
        if json_data["expression"]:
            proof.addUDF(json_data["label"], json_data["type"], json_data["expression"])
        elif json_data.get("expression_hidden"):
            pass  # student-entry mode: no expression to register yet, skip addUDF
        else:
            raise ValueError('Definition must have expression')

    except:
        return Response(
            {"message": "Error adding definition"}, status=status.HTTP_400_BAD_REQUEST
        )

    if (errors := proof.getErrorsAndClear()):
        return Response(
            {"message": str(errors)}, status=status.HTTP_400_BAD_REQUEST
        )

    definition = create_user_definition(user, json_data)
    definition["applied"] = True
    proof.definitions.append(definition)
    save_proof_to_cache(user, proof)
    return Response(definition, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
# def remove_definition(request, id):
def remove_definition(request, label):
    user = request.user
    proof = get_or_set_proof(user)

    definitions = proof.definitions
    proof.definitions = [
        # definition for definition in definitions if definition["id"] != id
        definition for definition in definitions if definition["label"] != label
    ]
    proof.removeUDF(label)

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

    rule = json_data["rule"]
    # Do not auto-rewrite; require explicit 'rewrite math' from client
    if rule.lower() == "math":
        print("[er-substitution] received 'math' without prefix; client should send 'rewrite math'")

    proof.setCurrentSide(json_data["side"])

    if proof.currentSide.getPrevRacket() != json_data["currentRacket"]:
        proof.toggleSide()
    
    try:
        print("[er-substitution] startPosition:", json_data.get("startPosition"))
        print("[er-substitution] currentRacket:", json_data.get("currentRacket"))
        print("[er-substitution] rule:", rule)
    except Exception:
        pass

    proof.currentSide.addProofLine(
        json_data["currentRacket"],
        rule,
        json_data["startPosition"],
        json_data["substitution"]
    )

    errors = update_and_validate(proof, json_data["side"])

    racket_str = (
        proof.currentSide.getPrevRacket() if proof.isValid else "Error generating racket"
    )
    jsonTree = makeJson(proof.currentSide.proofLines[-1].exprTree)

    save_proof_to_cache(user, proof)

    return Response(
        {"isValid": proof.isValid, "racket": racket_str, "jsonTree": jsonTree, "errors": errors},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def save_proof(request):
    try:
        data = request.data
        user = request.user
        user_proof = get_or_set_proof(user)
        definitions = user_proof.definitions
        generics = user_proof.generics
        proof = get_or_create_proof(data, user, definitions, generics)

        if not proof:
            return Response(
                {"message": "Error saving proof"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Proof saved successfully"}, status=status.HTTP_201_CREATED
        )
    except Exception as e:
        import traceback
        print(f"Error saving proof: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {"message": f"Error saving proof: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
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
    try:
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
                line["jsonTree"] = makeJson(proof.LHS.proofLines[leftIndex].exprTree)
                if line["rule"] == "Premise":
                    frontend_json["leftPremise"] = line
                    frontend_json["lHSGoal"] = line["racket"]
                else:
                    frontend_json["leftRacketsAndRules"].append(line)
                leftIndex += 1
            else:
                line["jsonTree"] = makeJson(proof.RHS.proofLines[rightIndex].exprTree)
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
    except Exception as e:
        return Response(
            {
                "error": "incompatible_version",
                "message": f"This proof was created with an incompatible version and cannot be loaded. Error: {str(e)}"
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
def get_definitions(request):
    user = request.user
    definitions = get_user_definitions(user)

    return Response(definitions, status=status.HTTP_200_OK)


@api_view(["GET"])
def use_definition(request, label):
    user = request.user
    definition = get_definition(user, label)
    proof = get_or_set_proof(user)

    try:
        if not definition:
            return Response({"message": "Definition not found"}, status=status.HTTP_404_NOT_FOUND)
        for proof_definition in proof.definitions:
            # if proof_definition["label"] == definition["label"]:
            #     return Response(status=status.HTTP_400_BAD_REQUEST) # removed to avoid failing on already applied defs
            if proof_definition["label"] == definition["label"]:
                return Response({"message": "Definition already applied"}, status=status.HTTP_200_OK)

        proof.addUDF(definition["label"], definition["type"], definition["expression"])

        definition["applied"] = True
        proof.definitions.append(definition)
        save_proof_to_cache(user, proof)

        return Response({"message": "Definition applied"}, status=status.HTTP_200_OK)
    except Exception as exc:
        # return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": str(exc) or "Failed to apply definition"}, status=status.HTTP_400_BAD_REQUEST)


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
    deleted = delete_definition(user, label)

    if not deleted:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # Also remove from the engine cache so the label can be reused immediately
    proof = get_or_set_proof(user)
    proof.definitions = [d for d in proof.definitions if d["label"] != label]
    proof.removeUDF(label)
    save_proof_to_cache(user, proof)

    return Response(status=status.HTTP_200_OK)

@api_view(["GET"])
def get_generics(request):
    user = request.user
    userProof = get_or_set_proof(user)
    enabledGenerics = userProof.generics
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
    proof.addGeneric(data["label"], data["type"], data.get("restrictions"))
    if (errors := proof.getErrorsAndClear()):
        return Response({ 'message': str(errors) }, status=status.HTTP_400_BAD_REQUEST)
    save_proof_to_cache(user, proof)
    return Response(generic, status=status.HTTP_201_CREATED)

@api_view(["GET"])
def enable_generic(request, id):
    user = request.user
    proof = get_or_set_proof(user)
    use_generic(proof, id)
    errors = proof.getErrorsAndClear()
    if len(errors) != 0:
        return Response({'message': str(errors)}, status=status.HTTP_400_BAD_REQUEST)
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

def clear_user_proofs(user):
    cache.delete(f"proofs_{user.username}")

def save_proof_to_cache(user, proof):
    cache_proofs = dumps(proof)
    cache.set(f"proofs_{user.username}", cache_proofs)

def get_or_set_proof(user) -> TwoSidedProof:
    proof = TwoSidedProof()
    cache_proofs = dumps(proof)
    user_proof = cache.get_or_set(f"proofs_{user.username}", cache_proofs)
    proof = loads(user_proof)
    return proof