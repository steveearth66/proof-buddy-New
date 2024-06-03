from .serializers import ProofSerializer, ProofLineSerializer, DefinitionSerializer
from rest_framework.response import Response
from rest_framework import status


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
