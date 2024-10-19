from .serializers import ProofSerializer, ProofLineSerializer, DefinitionSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Proof, ProofLine, Definition
from expression_tree.ERProofEngine import ERProof


def get_or_create_proof(data, user, definitions):
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
        add_data_to_proof(data, proof, definitions, user)
        return proof

    proof = ProofSerializer(data=proof_data)

    if not proof.is_valid():
        return proof.errors
    proof.save(created_by=user)
    add_data_to_proof(data, proof.instance, definitions, user)

    return proof.instance


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


def add_data_to_proof(json_data, proof, definitions, user):
    try:
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
        add_definitions(definitions, proof, user)
    except:
        proof.delete()
        raise Exception("Error adding data to proof")


def add_definitions(definitions, proof: Proof, user):
    for definition in definitions:
        proof.definitions.add(definition["id"])


# Return all incomplete proofs for a user. Can be change to return all but if a use click on a proof marked as complete the backend crashes because the proof is already complete.
# This can be fixed by adding a checker to see if the proof is complete, if the proof is complete don't call load_proof method.
def user_proofs(user):
    proofs = Proof.objects.filter(
        created_by=user
    )  # Proof.objects.filter(created_by=user) to return all proofs by user
    proof_data = []

    for proof in proofs:
        proof_lines = ProofLine.objects.filter(proof=proof)
        definitions = Definition.objects.filter(created_by=user)
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

    return proof_data


def user_proof(user, proof_id):
    proof = Proof.objects.filter(created_by=user, id=proof_id).first()
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
            }
        )

    proof_data = {
        "id": proof.id,
        "name": proof.name,
        "tag": proof.tag,
        "lhs": proof.lhs,
        "rhs": proof.rhs,
        "isComplete": proof.isComplete,
        "proofLines": proof_lines_data,
        "definitions": definitions_data,
    }

    return proof_data


def load_proof(proof_data):
    # print(proof_data)
    proof = {
        "proofOne": ERProof(),
        "proofTwo": ERProof(),
        "isValid": True,
        "currentProof": None,
        "definitions": [],
    }

    left_proof: ERProof = proof["proofOne"]
    right_proof: ERProof = proof["proofTwo"]
    definitions = proof_data["definitions"]

    proof_lines = proof_data["proofLines"]
    left_proof_lines = [line for line in proof_lines if line["leftSide"]]
    right_proof_lines = [line for line in proof_lines if not line["leftSide"]]

    for definition in definitions:
        label = definition["label"]
        def_type = definition["type"]
        expression = definition["expression"]

        left_proof.addUDF(label, def_type, expression)
        right_proof.addUDF(label, def_type, expression)
        proof["definitions"].append(definition)

    for index, line in enumerate(left_proof_lines, start=0):
        if index == 0:
            left_proof.addProofLine(line["racket"])
        else:
            left_proof.addProofLine(
                left_proof_lines[index - 1]["racket"],
                line["rule"],
                left_proof_lines[index - 1]["startPosition"],
            )

    for index, line in enumerate(right_proof_lines, start=0):
        if index == 0:
            right_proof.addProofLine(line["racket"])
        else:
            right_proof.addProofLine(
                right_proof_lines[index - 1]["racket"],
                line["rule"],
                right_proof_lines[index - 1]["startPosition"],
            )

    proof["currentProof"] = left_proof

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


def get_definition(id):
    definition = Definition.objects.filter(id=id).first()
    definition_data = {
        "id": definition.id,
        "label": definition.label,
        "type": definition.def_type,
        "expression": definition.expression,
    }

    return definition_data


def edit_definition(user, id, data):
    definition = Definition.objects.filter(id=id, created_by=user).first()

    if not definition:
        return False

    definition.label = data["label"]
    definition.def_type = data["type"]
    definition.expression = data["expression"]
    definition.notes = data["notes"]
    definition.save()

    definition_data = DefinitionSerializer(definition).data

    return definition_data


def delete_definition(user, id):
    definition = Definition.objects.filter(id=id, created_by=user).first()

    if not definition:
        return False

    definition.delete()

    return True
