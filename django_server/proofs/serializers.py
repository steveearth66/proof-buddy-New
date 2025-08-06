from .models import Proof, ProofLine, Definition, Generic
from rest_framework import serializers


class ProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = ["name", "tag", "lhs", "rhs", "created_at", "isComplete"]

    def create(self, validated_data):
        proof = Proof.objects.create(**validated_data)
        return proof


class ProofLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProofLine
        fields = ['left_side', 'racket', 'rule',
                  'start_position', 'created_at', 'errors', 'deleted']

    def create(self, validated_data):
        proof = validated_data.pop("proof")
        left_side = validated_data.pop("left_side")
        racket = validated_data.pop("racket")
        proof_line, created = ProofLine.objects.update_or_create(
            proof=proof, left_side=left_side, racket=racket, defaults=validated_data
        )
        return proof_line


class DefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Definition
        fields = ["id", "label", "def_type", "expression", "notes", "created_at"]

    def create(self, validated_data):
        label = validated_data.pop("label")
        def_type = validated_data.pop("def_type")
        user = validated_data.pop("created_by")
        definition, created = Definition.objects.update_or_create(
            label=label, created_by=user, def_type=def_type, defaults=validated_data
        )
        return definition

class GenericSerializer(serializers.ModelSerializer):
    class Meta:
        model = Generic
        fields = ["id", "label", "type", "notes", "assumption", "never_null"]
        extra_kwargs = {
            "assumption": {"write_only": True},
            "neverNull": {"write_only": True}
        }
    
    restrictions = serializers.SerializerMethodField()

    def get_restrictions(self, obj):
        if obj.type == 'int':
            return { 'assumption': obj.assumption }
        if obj.type == 'list':
            return { 'neverNull': obj.never_null }
        return None
    
    def create(self, validated_data):
        user = validated_data.pop("created_by")
        generic, _ = Generic.objects.update_or_create(created_by=user, defaults=validated_data)
        return generic