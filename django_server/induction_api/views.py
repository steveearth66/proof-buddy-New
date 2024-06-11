from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from dill import dumps, loads
from django.core.cache import cache


User = get_user_model()


@api_view(["POST"])
def start_induction_proof(request):
    user = request.user
    json_data = request.data
    print(json_data)
    return Response(json_data, status=status.HTTP_200_OK)


@api_view(["POST"])
def clear_induction(request):
    user = request.user
    clear_induction_proof(user)
    return Response(status=status.HTTP_200_OK)


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
