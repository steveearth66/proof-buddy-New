from .models import Proof, ProofLine, Definition
from rest_framework import serializers


class ProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = ['name', 'tag', 'lsh', 'rsh',
                  'created_at', 'isComplete']

    def create(self, validated_data):
        proof = Proof.objects.create(**validated_data)
        proof.save()
        return proof


class ProofLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProofLine
        fields = ['left_side', 'racket', 'rule',
                  'start_position', 'created_at', 'errors', 'deleted']

    def create(self, validated_data):
        proof_line = ProofLine.objects.create(**validated_data)
        proof_line.save()
        return proof_line


class DefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Definition
        fields = ['label', 'def_type', 'expression',
                  'notes', 'created_at']

    def create(self, validated_data):
        definition = Definition.objects.create(**validated_data)
        definition.save()
        return definition
