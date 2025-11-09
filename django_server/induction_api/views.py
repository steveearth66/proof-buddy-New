from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from dill import dumps, loads
from django.core.cache import cache
from .models import InductionProof
from .serializers import InductionProofSerializer, InductionProofCreateSerializer
import re


User = get_user_model()


@api_view(["POST"])
def create_induction_proof(request):
    user = request.user
    
    create_serializer = InductionProofCreateSerializer(data=request.data)
    
    if not create_serializer.is_valid():
        return Response(
            {
                "error": "Validation failed",
                "details": create_serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = create_serializer.validated_data
    
    proof_data = {
        'user': user.id,
        'proof_type': 'induction_int',
        'induction_variable': validated_data['induction_variable'],
        'anchor_value': validated_data['anchor_value'],
        'leap_variable': validated_data['leap_variable'],
        'lhs_expression': validated_data['lhs_expression'],
        'rhs_expression': validated_data['rhs_expression'],
        'is_valid': True,
        'definition': [],
    }
    
    induction_var = validated_data['induction_variable']
    leap_var = validated_data['leap_variable']
    anchor_val = validated_data['anchor_value']
    
    lhs_anchor = validated_data['lhs_expression'].replace(
        induction_var, str(anchor_val)
    )
    rhs_anchor = validated_data['rhs_expression'].replace(
        induction_var, str(anchor_val)
    )
    
    lhs_leap = validated_data['lhs_expression'].replace(
        induction_var, leap_var
    )
    rhs_leap = validated_data['rhs_expression'].replace(
        induction_var, leap_var
    )
    
    proof_data.update({
        'lhs_anchor_goal': lhs_anchor,
        'rhs_anchor_goal': rhs_anchor,
        'lhs_leap_goal': lhs_leap,
        'rhs_leap_goal': rhs_leap,
        'current_goal': 'base_case',
    })
    
    serializer = InductionProofSerializer(data=proof_data)
    
    if serializer.is_valid():
        proof = serializer.save(user=user)
        
        save_induction_proof_to_cache(user, {
            'id': proof.id,
            'lhs_leap_goal': proof.lhs_leap_goal,
            'rhs_leap_goal': proof.rhs_leap_goal,
            'lhs_anchor_goal': proof.lhs_anchor_goal,
            'rhs_anchor_goal': proof.rhs_anchor_goal,
            'current_goal': proof.current_goal,
            'isValid': proof.is_valid,
            'definition': proof.definition,
        })
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(
        {
            "error": "Failed to create proof",
            "details": serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(["POST"])
def start_induction_proof(request):
    user = request.user
    json_data = request.data
    
    print("Received induction data:", json_data)
    
    try:
        side = json_data.get('side')
        proof_name = json_data.get('proof_name')
        proof_tag = json_data.get('proof_tag')
        lhs_leap_goal = json_data.get('lhs_leap_goal')
        rhs_leap_goal = json_data.get('rhs_leap_goal')
        lhs_anchor_goal = json_data.get('lhs_anchor_goal')
        rhs_anchor_goal = json_data.get('rhs_anchor_goal')
        induction_variable = json_data.get('induction_variable')
        anchor_value = json_data.get('anchor_value')
        leap_variable = json_data.get('leap_variable')
        induction_type = json_data.get('induction_type')
        is_anchor = json_data.get('is_anchor', False)
        
        if not all([proof_name, induction_variable, anchor_value]):
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proof_data = {
            'user': user.id,
            'proof_type': 'induction_int',
            'name': proof_name,
            'tag': proof_tag,
            'induction_variable': induction_variable,
            'anchor_value': anchor_value,
            'leap_variable': leap_variable,
            'lhs_leap_goal': lhs_leap_goal,
            'rhs_leap_goal': rhs_leap_goal,
            'lhs_anchor_goal': lhs_anchor_goal,
            'rhs_anchor_goal': rhs_anchor_goal,
            'induction_type': induction_type,
            'current_side': side,
            'is_anchor_case': is_anchor,
            'is_valid': True,
            'definition': [],
        }
        
        serializer = InductionProofSerializer(data=proof_data)
        if serializer.is_valid():
            proof = serializer.save(user=user)
            
            save_induction_proof_to_cache(user, {
                'id': proof.id,
                'name': proof.name,
                'tag': proof.tag,
                'lhs_leap_goal': proof.lhs_leap_goal,
                'rhs_leap_goal': proof.rhs_leap_goal,
                'lhs_anchor_goal': proof.lhs_anchor_goal,
                'rhs_anchor_goal': proof.rhs_anchor_goal,
                'induction_variable': proof.induction_variable,
                'anchor_value': proof.anchor_value,
                'leap_variable': proof.leap_variable,
                'current_side': proof.current_side,
                'is_anchor_case': proof.is_anchor_case,
                'current_goal': proof.current_goal,
                'isValid': proof.is_valid,
                'definition': proof.definition,
            })
            
            return Response(
                {
                    "message": "Induction proof started successfully",
                    "proof_id": proof.id,
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    "error": "Failed to save proof",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        print(f"Error processing induction proof: {str(e)}")
        return Response(
            {"error": f"Internal server error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def clear_induction(request):
    user = request.user
    clear_induction_proof(user)
    
    delete_all = request.data.get('delete_all', False)
    if delete_all:
        InductionProof.objects.filter(user=user).delete()
    
    return Response(
        {"message": "Induction proof cleared successfully"},
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
def get_induction_proofs(request):
    user = request.user
    proofs = InductionProof.objects.filter(user=user)
    serializer = InductionProofSerializer(proofs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_induction_proof(request, proof_id):
    user = request.user
    
    try:
        proof = InductionProof.objects.get(id=proof_id, user=user)
        serializer = InductionProofSerializer(proof)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except InductionProof.DoesNotExist:
        return Response(
            {"error": "Proof not found"},
            status=status.HTTP_404_NOT_FOUND
        )

def clear_induction_proof(user):
    cache.delete(f"induction_proof_{user.username}")


def save_induction_proof_to_cache(user, proof):
    cache_proof = dumps(proof)
    cache.set(f"induction_proof_{user.username}", cache_proof)


def get_or_set_induction_proof(user):
    proof = {
        "lhs_leap_goal": None,
        "rhs_leap_goal": None,
        "lhs_anchor_goal": None,
        "rhs_anchor_goal": None,
        "current_goal": None,
        "isValid": True,
        "definition": [],
    }
    cache_proof = dumps(proof)
    user_proof = cache.get_or_set(f"induction_proof_{user.username}", cache_proof)
    return loads(user_proof)