from .serializers import ProofSerializer, ProofLineSerializer, DefinitionSerializer, GenericSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Proof, ProofLine, Definition, Generic
from expression_tree.ERProofEngine import TwoSidedProof, ERProof
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.decorators import api_view

@api_view(["DELETE"])
def delete_proof(request, id):
    try:
        proof = Proof.objects.get(id=id)
        proof.delete()
        return Response(
                { "message": "Proof successfully deleted"}, status=status.HTTP_200_OK
            )
    except Proof.DoesNotExist:
        return Response(
                { "message": "Proof does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

@api_view(["PUT"])
def edit_proof(request, id):
    try:
        proof = Proof.objects.get(id=id)
        serializer = ProofSerializer(proof, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                    { "message": "Proof successfully updated" }, status=status.HTTP_200_OK
                )
        else:
            return Response(
                    { "message": "New name or tag is invalid" }, status=status.HTTP_400_BAD_REQUEST
                )
    except Proof.DoesNotExist:
        return Response(
                { "message": "Proof does not exist" }, status=status.HTTP_404_NOT_FOUND
            )

def get_or_create_proof(data, user, definitions, generics):
    proof_data = {
        "name": data["name"],
        "tag": data["tag"],
        "lhs": data["lHSGoal"],
        "rhs": data["rHSGoal"],
    }

    proof = Proof.objects.filter(
        name=data["name"], tag=data["tag"], created_by=user
    ).first()

    if proof:
        add_data_to_proof(data, proof, definitions, generics, user)
        return proof

    proof = ProofSerializer(data=proof_data)

    if not proof.is_valid():
        return proof.errors
    proof.save(created_by=user)
    add_data_to_proof(data, proof.instance, definitions, generics, user)

    return proof.instance


def create_proof_lines(lines, left_side, proof):
    for line in lines:
        # Skip empty lines that are just placeholders
        if not line.get("racket") or not line.get("rule"):
            continue
            
        racket = line["racket"]
        rule = line["rule"]
        start_position = line.get("startPosition", 0)
        errors = line.get("errors", [])
        deleted = line.get("deleted", False)

        proof_line_data = {
            "left_side": left_side,
            "racket": racket,
            "rule": rule,
            "start_position": start_position,
            "deleted": deleted,
            "errors": str(errors),
        }

        proof_line = ProofLineSerializer(data=proof_line_data)

        if not proof_line.is_valid():
            return Response(proof_line.errors, status=status.HTTP_400_BAD_REQUEST)

        proof_line.save(proof=proof)


def add_data_to_proof(json_data, proof, definitions, generics, user):
    try:
        # Clear existing proof lines when updating
        proof.proof_lines.all().delete()
        
        left_premise_data = json_data["leftPremise"]
        if left_premise_data["checked"]:
            left_premise_data = {
                "left_side": True,
                "racket": left_premise_data["racket"],
                "rule": left_premise_data["rule"],
                "start_position": left_premise_data["startPosition"],
            }
            left_premise = ProofLineSerializer(data=left_premise_data)
            if not left_premise.is_valid():
                return Response(left_premise.errors, status=status.HTTP_400_BAD_REQUEST)
            left_premise.save(proof=proof)
            
        right_premise_data = json_data["rightPremise"]
        if right_premise_data["checked"]:
            right_premise_data = {
                "left_side": False,
                "racket": right_premise_data["racket"],
                "rule": right_premise_data["rule"],
                "start_position": right_premise_data["startPosition"],
            }
            right_premise = ProofLineSerializer(data=right_premise_data)
            if not right_premise.is_valid():
                return Response(right_premise.errors, status=status.HTTP_400_BAD_REQUEST)
            right_premise.save(proof=proof)

        left_rackets_and_rules = json_data["leftRacketsAndRules"]
        right_rackets_and_rules = json_data["rightRacketsAndRules"]
        create_proof_lines(left_rackets_and_rules, True, proof)
        create_proof_lines(right_rackets_and_rules, False, proof)
        add_definitions(definitions, proof, user)
        add_generics(generics, proof, user)
    except Exception as e:
        proof.delete()
        raise Exception(f"Error adding data to proof: {str(e)}")


def add_definitions(definitions, proof: Proof, user):
    proof.definitions.clear()
    for definition in definitions:
        proof.definitions.add(definition["id"])

def add_generics(generics, proof: Proof, user):
    for label in generics.keys():
        generic = Generic.objects.filter(created_by=user, label=label).first()
        proof.generics.add(generic)

# Return all incomplete proofs for a user. Can be change to return all but if a use click on a proof marked as complete the backend crashes because the proof is already complete.
# This can be fixed by adding a checker to see if the proof is complete, if the proof is complete don't call load_proof method.
def user_proofs(user, page=1, query="", proofs_per_page=12):
    proofs = Proof.objects.filter(created_by=user, name__contains=query).order_by(
        "-created_at"
    )
    paginator = Paginator(proofs, proofs_per_page)

    try:
        paginated_proofs = paginator.page(int(page))
    except PageNotAnInteger:
        paginated_proofs = paginator.page(1)
    except EmptyPage:
        paginated_proofs = paginator.page(paginator.num_pages)

    proof_data = []

    for proof in paginated_proofs:
        proof_lines = ProofLine.objects.filter(proof=proof)
        definitions = proof.definitions.all()
        proof_lines_data = []
        definitions_data = []

        for proof_line in proof_lines:
            proof_lines_data.append(
                {
                    "leftSide": proof_line.left_side,
                    "racket": proof_line.racket,
                    "rule": proof_line.rule,
                    "startPosition": proof_line.start_position,
                    "errors": proof_line.errors,
                }
            )

        for definition in definitions:
            definitions_data.append(
                {
                    "id": definition.id,
                    "label": definition.label,
                    "type": definition.def_type,
                    "expression": definition.expression,
                    "notes": definition.notes,
                    "applied": True,
                }
            )

        proof_data.append(
            {
                "id": proof.id,
                "name": proof.name,
                "tag": proof.tag,
                "lhs": proof.lhs,
                "rhs": proof.rhs,
                "isComplete": proof.isComplete,
                "proofLines": proof_lines_data,
                "definitions": definitions_data,
            }
        )

    return {
        "proofs": proof_data,
        "totalPages": paginator.num_pages,
        "currentPage": paginated_proofs.number,
        "hasNext": paginated_proofs.has_next(),
        "hasPrevious": paginated_proofs.has_previous(),
    }


def user_proof(user, proof_id):
    proof = Proof.objects.filter(created_by=user, id=proof_id).first()
    proof_lines = ProofLine.objects.filter(proof=proof).order_by("id")
    definitions = proof.definitions.all()
    generics = proof.generics.all()
    proof_lines_data = []
    definitions_data = []

    for proof_line in proof_lines:
        proof_lines_data.append(
            {
                "leftSide": proof_line.left_side,
                "racket": proof_line.racket,
                "rule": proof_line.rule,
                "startPosition": proof_line.start_position,
                "errors": proof_line.errors,
                "deleted": proof_line.deleted,
            }
        )

    for definition in definitions:
        definitions_data.append(
            {
                "id": definition.id,
                "label": definition.label,
                "type": definition.def_type,
                "expression": definition.expression,
                "notes": definition.notes,
                "applied": True,
            }
        )
    
    generics_data = GenericSerializer(generics, many=True).data
    for generic_dict in generics_data:
        generic_dict["enabled"] = True

    proof_data = {
        "id": proof.id,
        "name": proof.name,
        "tag": proof.tag,
        "lhs": proof.lhs,
        "rhs": proof.rhs,
        "isComplete": proof.isComplete,
        "proofLines": proof_lines_data,
        "definitions": definitions_data,
        "generics": generics_data
    }

    return proof_data


def load_proof(proof_data):
    # print(proof_data)
    proof = TwoSidedProof()

    definitions = proof_data["definitions"]

    proof_lines = proof_data["proofLines"]
    left_proof_lines = [line for line in proof_lines if line["leftSide"]]
    right_proof_lines = [line for line in proof_lines if not line["leftSide"]]

    for definition in definitions:
        label = definition["label"]
        def_type = definition["type"]
        expression = definition["expression"]
        definition["applied"] = True

        proof.addUDF(label, def_type, expression)
        proof.definitions.append(definition)
    
    for generic in proof_data["generics"]:
        proof.addGeneric(generic["label"], generic["type"], generic["restrictions"])

    for index, line in enumerate(left_proof_lines, start=0):
        if index == 0:
            proof.LHS.addProofLine(line["racket"])
        else:
            proof.LHS.addProofLine(
                left_proof_lines[index - 1]["racket"],
                line["rule"],
                left_proof_lines[index - 1]["startPosition"],
            )

    for index, line in enumerate(right_proof_lines, start=0):
        if index == 0:
            proof.RHS.addProofLine(line["racket"])
        else:
            proof.RHS.addProofLine(
                right_proof_lines[index - 1]["racket"],
                line["rule"],
                right_proof_lines[index - 1]["startPosition"],
            )

    return proof


def get_user_definitions(user):
    definitions = Definition.objects.filter(created_by=user)
    definitions_data = []

    for definition in definitions:
        definitions_data.append(
            {
                "id": definition.id,
                "label": definition.label,
                "type": definition.def_type,
                "expression": definition.expression,
                "notes": definition.notes,
                "applied": False,
            }
        )

    return definitions_data


def create_user_definition(user, data):
    definition_data = {
        "label": data["label"],
        "def_type": data["type"],
        "expression": data["expression"],
        "notes": data["notes"],
    }

    definition_serializer = DefinitionSerializer(data=definition_data)

    if not definition_serializer.is_valid():
        return False

    definition_serializer.save(created_by=user)

    return definition_serializer.data

def create_or_override_definition(user, data):
    definition = Definition.objects.filter(label=data["label"], created_by=user).first()

    if not definition:
        return create_user_definition(user, data)
    else:
        definition.def_type = data["type"]
        definition.expression = data["expression"]
        definition.notes = data["notes"]
        definition.save()
        return DefinitionSerializer(definition).data


# def get_definition(id):
def get_definition(label):
    # definition = Definition.objects.filter(id=id).first()
    definition = Definition.objects.filter(label=label).first()
    definition_data = {
        "id": definition.id,
        "label": definition.label,
        "type": definition.def_type,
        "expression": definition.expression,
    }

    return definition_data


# def edit_definition(user, id, data):
def edit_definition(user, label, data):
    definition = Definition.objects.filter(label=label, created_by=user).first()

    if not definition:
        return False

    definition.label = data["label"]
    definition.def_type = data["type"]
    definition.expression = data["expression"]
    definition.notes = data["notes"]
    definition.save()

    definition_data = DefinitionSerializer(definition).data

    return definition_data


# def delete_definition(user, id):
def delete_definition(user, label):
    # definition = Definition.objects.filter(id=id, created_by=user).first()
    definition = Definition.objects.filter(label=label, created_by=user).first()

    if not definition:
        return False

    definition.delete()

    return True

def get_user_generics(user):
    generics = Generic.objects.filter(created_by=user)
    serializer = GenericSerializer(generics, many=True)
    return serializer.data

def create_user_generic(user, data):
    model_data = {
        **data, 
        "restrictions": str(data.get("restrictions"))
        }
    serializer = GenericSerializer(data=model_data)
    if serializer.is_valid(raise_exception=True):
        serializer.save(created_by=user)
    return serializer.data

def use_generic(proof: TwoSidedProof, id):
    generic = Generic.objects.get(id=id)
    generic_data = GenericSerializer(generic).data
    proof.addGeneric(generic_data["label"], generic_data["type"], generic_data["restrictions"])

def remove_generic(proof: TwoSidedProof, id):
    generic = Generic.objects.get(id=id)
    label = generic.label
    del proof.generics[label]

def delete_generic(proof: TwoSidedProof, id):
    try:
        remove_generic(proof, id)
    except KeyError:
        pass
    generic = Generic.objects.get(id=id)
    generic.delete()

def use_uploaded_generic(user, proof: TwoSidedProof, generic_data):
    model_data = {
        **generic_data, 
        "restrictions": str(generic_data.get("restrictions"))
        }
    generic_object = Generic.objects.filter(created_by=user, label=generic_data["label"]).first()
    serializer = (GenericSerializer(data=model_data) 
                  if generic_object is None 
                  else GenericSerializer(instance=generic_object, data=model_data))
    if serializer.is_valid():
        serializer.save(created_by=user)
    proof.addGeneric(generic_data["label"], generic_data["type"], generic_data["restrictions"])