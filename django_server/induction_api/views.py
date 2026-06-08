from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from dill import dumps, loads
from django.core.cache import cache
from .models import InductionProof, InductionProofLineComment
from .serializers import InductionProofSerializer, InductionProofCreateSerializer
import re
import traceback
import json
from django.db import models

# ER Engine imports for induction proof wiring
from expression_tree.IndProofs import IndProof
from expression_tree.ERProofEngine import TwoSidedProof, ERProof, ERProofLine
from expression_tree.ERCommon import makeJson
from expression_tree.ERRuleset import recursiveReplaceNodes, IH
from expression_tree.LemmaApplicator import build_lemma_rule
from expression_tree.default_udfs import DEFAULT_UDFS
from proofs.views import use_uploaded_generic
from .models import InductionProofLine

from assignments.models import StudentProofMapping
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.shortcuts import get_object_or_404

User = get_user_model()


# ========================
# Lemma Lookup Helper
# ========================

def _lookup_lemma(name: str, user):
    """
    Look up a completed proof by *name* for *user*.
    Returns ``(premise_str, conclusion_str, error_msg)``.
    Checks EquationalProof first; falls back to InductionProof.
    *error_msg* is ``None`` on success.
    """
    from equational_reasoning_api.models import EquationalProof as _EqProof
    from .models import InductionProof as _IndProof

    # Check i: does an equational proof with this name exist?
    eq = _EqProof.objects.filter(name=name, user=user, is_active=True).order_by('-created_at').first()
    if eq is not None:
        # Check ii: is it complete?
        if not eq.is_complete:
            return None, None, f"Proof '{name}' has not been completed yet"
        return eq.lhs_goal, eq.rhs_goal, None

    # Check i: does an induction proof with this name exist?
    ind = _IndProof.objects.filter(name=name, user=user, is_active=True).order_by('-created_at').first()
    if ind is not None:
        # Check ii: is it complete?
        if not ind.is_complete:
            return None, None, f"Proof '{name}' has not been completed yet"
        # Reconstruct original goal by substituting leap_variable → induction_variable
        k, n = ind.leap_variable, ind.induction_variable
        premise_str = re.sub(r'\b' + re.escape(k) + r'\b', n, ind.inductive_hypothesis_lhs)
        conclusion_str = re.sub(r'\b' + re.escape(k) + r'\b', n, ind.inductive_hypothesis_rhs)
        return premise_str, conclusion_str, None

    return None, None, f"No completed proof named '{name}' found"


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
        'inductive_hypothesis_lhs' : validated_data.get('inductive_hypothesis_lhs', ''),
        'inductive_hypothesis_rhs' : validated_data.get('inductive_hypothesis_rhs', ''),
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
def clear_induction(request):
    """Clear cache of the current active proof for the user"""
    from .models import InductionProof
    user = request.user
    
    try:
        # Find the active proof
        proof = InductionProof.objects.filter(user=user, is_active=True).order_by('-created_at').first()
        
        if proof:
            # Archive the proof in the database (soft delete)
            proof.is_active = False
            proof.save()
            # Clear the cache
            cache.delete(f"induction_obj_{user.username}")
            
            return Response({
                "message": "Proof archived successfully",
                "proof_name": proof.name or "Unnamed proof"
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "No active proof found"
            }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def new_proof(request):
    """Clear the session cache without archiving the proof, so the user can start a new proof
    while the current one remains visible in All Proofs."""
    user = request.user
    try:
        cache.delete(f"induction_obj_{user.username}")
        cache.delete(f"induction_proof_{user.username}")
        return Response({"message": "Session cleared successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_induction_proofs(request):
    user = request.user
    query = request.GET.get('query', '')
    
    # Filter proofs by user and optionally by query (name contains)
    proofs = InductionProof.objects.filter(user=user, is_active=True)
    if query:
        proofs = proofs.filter(name__icontains=query)
    
    proofs = proofs.order_by('-created_at')
    
    serializer = InductionProofSerializer(proofs, many=True)
    
    # Return in the same format as equational reasoning for consistency
    return Response({
        "proofs": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(["POST"])
def start_induction_proof(request):
    user = request.user
    json_data = request.data
    
    # Clear any stale cached proof object to prevent validation contamination
    # (Without this, check_goal validations use old UDFs from previous proofs)
    cache.delete(f"induction_obj_{user.username}")
    
    try:
        # Extract all data
        side = json_data.get('side', 'LHS')
        proof_name = json_data.get('proof_name', '')
        proof_tag = json_data.get('proof_tag', '')
        lhs_leap_goal = json_data.get('lhs_leap_goal', '')
        rhs_leap_goal = json_data.get('rhs_leap_goal', '')
        lhs_anchor_goal = json_data.get('lhs_anchor_goal', '')
        rhs_anchor_goal = json_data.get('rhs_anchor_goal', '')
        induction_variable = json_data.get('induction_variable', '')
        anchor_value = json_data.get('anchor_value')
        leap_variable = json_data.get('leap_variable', '')
        induction_type = json_data.get('induction_type', 'integers')
        is_anchor = json_data.get('is_anchor', False)
        inductive_hypothesis_lhs = json_data.get('inductive_hypothesis_lhs', '')
        inductive_hypothesis_rhs = json_data.get('inductive_hypothesis_rhs', '')
        definitions = json_data.get('definitions', [])
        
        # Validate required fields
        if not all([proof_name, induction_variable, anchor_value is not None, leap_variable]):
            return Response(
                {"error": "Missing required fields: proof_name, induction_variable, anchor_value, and leap_variable are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Reserved proof names cannot be used
        RESERVED_PROOF_NAMES = {"IH", "length", "append", "reverse"}
        if proof_name.strip() in RESERVED_PROOF_NAMES:
            return Response(
                {"error": f"'{proof_name.strip()}' is a reserved name and cannot be used as a proof name."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine structure type
        struct = 'list' if induction_type.lower() == 'lists' else 'int'
        
        # 1. Validate anchor value based on structure type
        if struct == 'int':
            # For integers: must be a valid integer (but keep as string for model)
            try:
                int(anchor_value)  # Validate it's an integer
            except (ValueError, TypeError):
                return Response(
                    {"error": "Anchor value (aVal) must be a valid integer for integer induction"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # For lists: anchor_value stays as string (e.g., 'null', "'()", etc.)
            pass
        
        # Check iVar is a valid identifier (single letter or valid variable name)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', induction_variable):
            return Response(
                {"error": "Induction variable (iVar) must be a valid identifier"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check Lvar is a valid identifier
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', leap_variable):
            return Response(
                {"error": "Leap variable (Lvar) must be a valid identifier"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Verify iVar appears as parameter in at least one side's goal
        def check_ivar_in_expression(expr, ivar):
            """Check if ivar appears as a parameter in a function application"""
            if not expr or not expr.strip():
                return False
            
            # Simple check: look for ivar as a word boundary
            pattern = r'\b' + re.escape(ivar) + r'\b'
            return bool(re.search(pattern, expr))
        
        ivar_in_lhs_leap = check_ivar_in_expression(lhs_leap_goal, induction_variable)
        ivar_in_rhs_leap = check_ivar_in_expression(rhs_leap_goal, induction_variable)
        ivar_in_lhs_anchor = check_ivar_in_expression(lhs_anchor_goal, induction_variable)
        ivar_in_rhs_anchor = check_ivar_in_expression(rhs_anchor_goal, induction_variable)
        
        if not (ivar_in_lhs_leap or ivar_in_rhs_leap or ivar_in_lhs_anchor or ivar_in_rhs_anchor):
            return Response(
                {"error": f"Induction variable '{induction_variable}' must appear as a parameter in at least one goal expression"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Check that Lvar has no conflict with other variables
        # Check if Lvar appears in any of the goal expressions
        lvar_in_lhs_leap = check_ivar_in_expression(lhs_leap_goal, leap_variable)
        lvar_in_rhs_leap = check_ivar_in_expression(rhs_leap_goal, leap_variable)
        lvar_in_lhs_anchor = check_ivar_in_expression(lhs_anchor_goal, leap_variable)
        lvar_in_rhs_anchor = check_ivar_in_expression(rhs_anchor_goal, leap_variable)
        
        if lvar_in_lhs_leap or lvar_in_rhs_leap or lvar_in_lhs_anchor or lvar_in_rhs_anchor:
            return Response(
                {"error": f"Leap variable '{leap_variable}' conflicts with variables in the goal. It must not appear in the original goal expressions."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if Lvar equals iVar
        if leap_variable == induction_variable:
            return Response(
                {"error": f"Leap variable '{leap_variable}' cannot be the same as induction variable '{induction_variable}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Validate that IH expressions are correct transformations of goals (ivar -> lvar)
        # Frontend already validates syntax/arity via checkGoal endpoint
        # Here we just check the transformation is correct
        from expression_tree.ERProofEngine import ERProofLine
        from expression_tree.ERRuleset import recursiveReplaceNodes
        import copy
        
        try:
            # Detect whether frontend is using high support mode
            high_support_mode = (
                not inductive_hypothesis_lhs.strip() and
                not inductive_hypothesis_rhs.strip()
            )

            # Parse the goals and IH expressions (frontend already validated these)
            lhs_goal_line = ERProofLine(lhs_leap_goal, False, None, generics=None)
            rhs_goal_line = ERProofLine(rhs_leap_goal, False, None, generics=None)
            
            # Create expected IH by replacing ivar with lvar in the parsed goals
            lvar_node = ERProofLine(leap_variable, False, None, generics=None).exprTree
            
            expected_lhs_ih_tree = copy.deepcopy(lhs_goal_line.exprTree)
            expected_rhs_ih_tree = copy.deepcopy(rhs_goal_line.exprTree)
            
            recursiveReplaceNodes(expected_lhs_ih_tree, [induction_variable], [lvar_node])
            recursiveReplaceNodes(expected_rhs_ih_tree, [induction_variable], [lvar_node])

            # Convert generated trees to strings
            expected_lhs_ih = str(expected_lhs_ih_tree)
            expected_rhs_ih = str(expected_rhs_ih_tree)

            if high_support_mode:
                # Autofill IH values
                inductive_hypothesis_lhs = expected_lhs_ih
                inductive_hypothesis_rhs = expected_rhs_ih

            else:
                # Get the already-parsed IH lines from the validation above
                lhs_ih_line = ERProofLine(inductive_hypothesis_lhs, False, None, generics=None)
                rhs_ih_line = ERProofLine(inductive_hypothesis_rhs, False, None, generics=None)
                
                # Compare the trees
                if str(lhs_ih_line.exprTree) != str(expected_lhs_ih_tree):
                    print(f"LHS IH mismatch!")
                    return Response(
                        {"error": f"LHS Inductive Hypothesis must be the LHS goal with {induction_variable} replaced by {leap_variable}.\nExpected: {expected_lhs_ih_tree}\nGot: {inductive_hypothesis_lhs}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if str(rhs_ih_line.exprTree) != str(expected_rhs_ih_tree):
                    return Response(
                        {"error": f"RHS Inductive Hypothesis must be the RHS goal with {induction_variable} replaced by {leap_variable}.\nExpected: {expected_rhs_ih_tree}\nGot: {inductive_hypothesis_rhs}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        except Exception as e:
            return Response(
                {"error": f"Error validating Inductive Hypothesis: {type(e).__name__}: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 5. Automatically create generic variable definitions
        # For leap variable (type based on structure)
        final_definitions_for_db = []
        generic_lvar = {
            'name': leap_variable,
            'type': 'list' if struct == 'list' else 'int',
            'body': '<generic>',
            'description': f'Generic variable for leap case in induction on {induction_variable}',
            'is_generic': True,
            'restrictions': {}
        }
        final_definitions_for_db.append(generic_lvar)
        
        generics_to_create = [generic_lvar]
        
        # For list induction with UP direction, also create generic 'a' of type 'Any'
        if struct == 'list':
            # Note: For now we default to UP direction. Later we'll add UI to select UP/DOWN
            generic_a = {
                'name': 'a',
                'type': 'Any',
                'body': '<generic>',
                'description': 'Generic element for cons in list induction',
                'is_generic': True,
                'restrictions': {}
            }
            final_definitions_for_db.append(generic_a)
            generics_to_create.append(generic_a)

        # C. Add User Definitions (UDFs) from Request
        # Normalize fields to ensure consistency
        for d in definitions:
            final_definitions_for_db.append({
                'label': d.get('label') or d.get('name'),
                'name': d.get('name') or d.get('label'),
                'type': d.get('type'),
                'body': d.get('expression') or d.get('body'),
                'expression': d.get('expression') or d.get('body'),
                'description': d.get('description', 'User Defined Function'),
                'is_generic': False
            })
        
        # Archive any existing active proof (Induction or ER) with the same name
        # Name alone is now sufficient to trigger archiving (cross-table)
        InductionProof.objects.filter(
            name=proof_name,
            user=user,
            is_active=True
        ).update(is_active=False)
        from equational_reasoning_api.models import EquationalProof as _ERProof
        _ERProof.objects.filter(
            name=proof_name,
            user=user,
            is_active=True
        ).update(is_active=False)

        # Create complete proof data
        proof_data = {
            'user': user.id,
            'name': proof_name,
            'tag': proof_tag,
            'proof_type': 'induction_int',
            'induction_type': induction_type,
            'induction_variable': induction_variable,
            'anchor_value': str(anchor_value),  # Store as string in database
            'leap_variable': leap_variable,
            'lhs_leap_goal': lhs_leap_goal,
            'rhs_leap_goal': rhs_leap_goal,
            'lhs_anchor_goal': lhs_anchor_goal,
            'rhs_anchor_goal': rhs_anchor_goal,
            'current_side': side,
            'is_anchor_case': is_anchor,
            'inductive_hypothesis_lhs' : inductive_hypothesis_lhs,
            'inductive_hypothesis_rhs' : inductive_hypothesis_rhs,
            'current_goal': 'base_case',
            'is_valid': True,
            'definition': final_definitions_for_db,
        }
        
        serializer = InductionProofSerializer(data=proof_data)
        
        if serializer.is_valid():
            proof = serializer.save(user=user)
            
            # Save to cache
            save_induction_proof_to_cache(user, {
                'id': proof.id,
                'name': proof.name,
                'tag': proof.tag,
                'lhs_leap_goal': proof.lhs_leap_goal,
                'rhs_leap_goal': proof.rhs_leap_goal,
                'lhs_anchor_goal': proof.lhs_anchor_goal,
                'rhs_anchor_goal': proof.rhs_anchor_goal,
                'current_goal': proof.current_goal,
                'current_side': side,
                'is_anchor_case': is_anchor,
                'isValid': proof.is_valid,
                'definition': proof.definition,
                'inductive_hypothesis_lhs' : proof.inductive_hypothesis_lhs,
                'inductive_hypothesis_rhs' : proof.inductive_hypothesis_rhs,
            })
            
            # Also update the IndProof object cache with the proof_id
            ind_proof, _ = get_or_set_induction_obj(user)
            save_induction_obj_to_cache(user, ind_proof, proof.id)
            
            # Note: Premises will be saved to database when set_current_proof is called
            # with the properly substituted values (ivar->aval for base, ivar->(+lvar 1) for leap)
            
            return Response(
                {
                    "message": "Induction proof started successfully",
                    "proof_id": proof.id,
                    "proof_name": proof.name,
                    "proof_tag": proof.tag,
                    "generic_definition_created": generic_lvar,  # For backwards compatibility
                    "generics_created": generics_to_create,  # All generics created
                    "data": serializer.data,
                    "inductive_hypothesis_lhs": inductive_hypothesis_lhs,
                    "inductive_hypothesis_rhs": inductive_hypothesis_rhs
                },
                status=status.HTTP_201_CREATED
            )
        else:
            print("=== SERIALIZER ERRORS ===")
            print(serializer.errors)
            print("=== END SERIALIZER ERRORS ===")
            
            return Response(
                {
                    "error": "Failed to save proof",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        print(f"Error processing induction proof: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response(
            {"error": f"Internal server error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
def get_induction_proofs(request):
    user = request.user
    query = request.GET.get('query', '')
    
    # Filter proofs by user and optionally by query (name contains)
    proofs = InductionProof.objects.filter(user=user, is_active=True)
    if query:
        proofs = proofs.filter(name__icontains=query)
    
    proofs = proofs.order_by('-created_at')
    
    serializer = InductionProofSerializer(proofs, many=True)
    
    # Return in the same format as equational reasoning for consistency
    return Response({
        "proofs": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_induction_proof(request, proof_id):
    user = request.user
    
    try:
        proof = get_object_or_404(InductionProof, id=proof_id)
        if (proof.user != user):
            proof_content_type = ContentType.objects.get_for_model(InductionProof)
        
            is_authorized_instructor = StudentProofMapping.objects.filter(
                object_id=proof.id,
                content_type=proof_content_type,
                assignment__course__instructor=user
            ).exists()

            if not is_authorized_instructor:
                return Response({"hasProof": False}, status=status.HTTP_403_OK)
        serializer = InductionProofSerializer(proof)
        response_data = dict(serializer.data)
        definitions = [dict(d) for d in (response_data.get("definition") or [])]
        for item in definitions:
            if item.get("expression_hidden") and not user.is_instructor:
                item["expression"] = "****"
        response_data["definition"] = definitions
        return Response(response_data, status=status.HTTP_200_OK)
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

# New: Cache helpers for full IndProof engine object
def save_induction_obj_to_cache(user, ind_proof: IndProof, proof_id=None):
    """Save IndProof object to cache along with the database proof ID"""
    cache_data = {
        'ind_proof': dumps(ind_proof),
        'proof_id': proof_id
    }
    cache.set(f"induction_obj_{user.username}", cache_data)

def get_or_set_induction_obj(user):
    """Get IndProof object and associated proof ID from cache"""
    cached = cache.get(f"induction_obj_{user.username}")
    if cached is None:
        ind = IndProof()
        save_induction_obj_to_cache(user, ind)
        return ind, None
    proof_id = cached.get('proof_id')
    return loads(cached['ind_proof']), proof_id


def _ensure_udfs_hydrated(proof, proof_id):
    """Re-register any UDFs that are missing from the proof engine ruleSet.
    This is a safety net for cache-miss scenarios (server restart, cache expiry)
    where the IndProof is rebuilt fresh and UDFs are lost. Called before every
    rule application so that eval-* and other non-apply rules can also find UDFs."""
    # baseCase and leapStep each have their own shared ruleSet (LHS+RHS share it)
    two_sided = [proof.baseCase, proof.leapStep]
    # Build the full list: DEFAULT_UDFS first, then any user defs stored in DB
    all_defs = list(DEFAULT_UDFS)
    if proof_id:
        try:
            _db_proof = InductionProof.objects.get(id=proof_id)
            all_defs = all_defs + list(_db_proof.definition or [])
        except InductionProof.DoesNotExist:
            pass
    for _d in all_defs:
        if _d.get('is_generic'):
            _glabel = _d.get('label') or _d.get('name') or ''
            _gtype = _d.get('type', 'int')
            _grestrictions = _d.get('restrictions') or {}
            if _glabel:
                for ts in two_sided:
                    if _glabel not in ts.generics:
                        try:
                            ts.addGeneric(_glabel, _gtype, _grestrictions)
                            ts.errLog = []
                        except Exception:
                            pass
            continue
        _dlabel = _d.get('label') or _d.get('name') or ''
        _dudf = _dlabel.replace('(', ' ').replace(')', ' ').split()
        if not _dudf:
            continue
        _udf_name = _dudf[0]
        _dtype = _d.get('type')
        _dbody = _d.get('expression') or _d.get('body')
        if not _dtype or not _dbody:
            continue
        for ts in two_sided:
            if _udf_name not in ts.ruleSet.get('apply', {}):
                ts.addUDF(_dlabel, _dtype, _dbody)
                ts.errLog = []  # discard hydration noise; apply_rule clears per-target errLog


def reload_proof_lines_from_db(proof, proof_id):
    """Reload all proof lines from database into the IndProof object"""    
    if proof_id is None:
        return
    
    try:
        # Clear existing proof lines
        proof.baseCase.LHS.proofLines = []
        proof.baseCase.RHS.proofLines = []
        proof.leapStep.LHS.proofLines = []
        proof.leapStep.RHS.proofLines = []
        
        # Get all proof lines for this proof, ordered by line number
        lines = InductionProofLine.objects.filter(proof_id=proof_id).order_by('case', 'side', 'line_number')

        for line in lines:
            # Determine which ERProof to add to
            if line.case == 'base':
                target = proof.baseCase.LHS if line.side == 'LHS' else proof.baseCase.RHS
            else:  # leap
                target = proof.leapStep.LHS if line.side == 'LHS' else proof.leapStep.RHS
            
            # Create ERProofLine and add to target
            proof_line = ERProofLine(line.racket, target.debug, target.ruleSet, generics=target.generics)
            proof_line.appliedRule = line.rule
            proof_line.appliedRuleNodeId = line.selected_node  # Restore highlighting position
            target.proofLines.append(proof_line)
            proof_line.errors = line.errors
            proof_line.hide_expression = line.hide_expression
            proof_line.hide_justification = line.hide_justification
    except Exception as e:
        pass


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_name_conflict(request):
    """
    Check whether any active proof (Induction or Equational Reasoning) owned by
    the current user already uses the given name.
    Query param: ?name=<proof name>
    Returns: { conflict: bool, type: "Induction" | "Equational Reasoning" | null, name: str }
    """
    from equational_reasoning_api.models import EquationalProof
    user = request.user
    name = request.GET.get('name', '').strip()
    if not name:
        return Response({'conflict': False, 'type': None, 'name': name}, status=status.HTTP_200_OK)
    # Check Induction proofs first
    ind_conflict = InductionProof.objects.filter(user=user, name=name, is_active=True).exists()
    if ind_conflict:
        return Response({'conflict': True, 'type': 'Induction', 'name': name}, status=status.HTTP_200_OK)
    # Check Equational Reasoning proofs
    er_conflict = EquationalProof.objects.filter(user=user, name=name, is_active=True).exists()
    if er_conflict:
        return Response({'conflict': True, 'type': 'Equational Reasoning', 'name': name}, status=status.HTTP_200_OK)
    return Response({'conflict': False, 'type': None, 'name': name}, status=status.HTTP_200_OK)


def _check_rewrite_math_misuse(rule):
    """Return an error message string if the user typed 'rewrite math' or 'rewrite logic'
    into the rule field instead of using the Substitution button, or None if the rule is fine."""
    rule_norm = (rule or '').strip().lower()
    if rule_norm == 'rewrite math':
        return ("The 'rewrite math' rule must be applied using the Substitution button, "
                "not the rule field.")
    if rule_norm.startswith('rewrite math'):
        return "'rewrite math' does not require additional parameters to be applied."
    if rule_norm == 'rewrite logic':
        return ("The 'rewrite logic' rule must be applied using the Substitution button, "
                "not the rule field.")
    if rule_norm.startswith('rewrite logic'):
        return "'rewrite logic' does not require additional parameters to be applied."
    return None


def save_proof_line_to_db(proof_id, case, side, racket, rule, start_position, line_number, substitution='', selected_node=None, result_node=None, json_tree=None, errors=''):
    """Save a proof line to the database"""
    from .models import InductionProofLine, InductionProof
    if proof_id is None:
        return
    try:
        proof = InductionProof.objects.get(id=proof_id)
        # Use selected_node if provided, otherwise default to start_position
        node_id = selected_node if selected_node is not None else start_position
        # Use result_node if provided, otherwise default to 0
        result_node_id = result_node if result_node is not None else 0
        # Use update_or_create to avoid duplicates
        InductionProofLine.objects.update_or_create(
            proof=proof,
            case=case,
            side=side,
            line_number=line_number,
            defaults={
                'racket': racket,
                'rule': rule or '',
                'substitution': substitution or '',
                'start_position': start_position,
                'selected_node': node_id,
                'result_node': result_node_id,
                'json_tree': json_tree or {},
                'errors': errors
            }
        )
    except InductionProof.DoesNotExist:
        pass
    except Exception as e:
        raise  # Re-raise to see full error


# ---- Induction Engine Endpoints (frontend -> ER engine) ----

@api_view(["POST"]) 
def set_current_proof(request):
    """
    Initialize a full IndProof engine instance using frontend inputs.
    Expected JSON:
    {
      "struct": "int" | "list",
      "ivar": "n",
      "aval": "0",            # anchor value expression
      "lvar": "k",            # leap variable
      "lhsPremise": "(sum n)",
      "rhsPremise": "(* n (+ n 1) (/ 1 2))",
      "definitions": [ { "label": "(f n)", "type": "int -> int", "expression": "..." }, ... ]
    }
    Returns 201 with initial state (json trees for base case LHS/RHS and leap step premises).
    """
    user = request.user
    data = request.data
    try:
        struct = str(data.get("struct", "int")).lower()
        ivar = data.get("ivar")
        aval = data.get("aval")
        lvar = data.get("lvar")
        lhsPremise = data.get("lhsPremise")
        rhsPremise = data.get("rhsPremise")
        definitions_and_generics = data.get("definitions", [])
        definitions = []
        generics = data.get("generics", [])
        
        for item in definitions_and_generics:
            if item.get('is_generic'):
                generics.append(item)
            else:
                item['applied'] = True
                definitions.append(item)

        # Basic validation
        missing = [k for k in ("ivar","aval","lvar","lhsPremise","rhsPremise") if not data.get(k)]
        if missing:
            return Response({"isValid": False, "errors": [f"Missing fields: {', '.join(missing)}"]}, status=status.HTTP_400_BAD_REQUEST)

        # Create a fresh IndProof engine, but preserve existing proof_id if available
        _, existing_proof_id = get_or_set_induction_obj(user)
        ind = IndProof()
        ind.struct = struct
        ind.ivar = ivar
        ind.aval = aval
        ind.lvar = lvar
        ind.lhsPremise = lhsPremise
        ind.rhsPremise = rhsPremise

        # Add generics to both baseCase and leapStep
        errors = []
        for g in generics:
            try:
                use_uploaded_generic(user, ind.baseCase, g)
                use_uploaded_generic(user, ind.leapStep, g)
            except Exception as e:
                error_msg = f"Error adding generic {g.get('label')}: {str(e)}"
                errors.append(error_msg)
        
        if errors:
            return Response({
                "isValid": False,
                "errors": errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Add user definitions (UDF) to both baseCase and leapStep rule sets
        for d in definitions:
            label = d.get("label")
            type_str = d.get("type")
            body = d.get("expression")
            if not label or not type_str or body is None:
                continue
            ind.baseCase.addUDF(label, type_str, body)
            ind.leapStep.addUDF(label, type_str, body)
            # track definition list similar to racket_api
            if getattr(ind, "definitions", None) is None:
                ind.definitions = []
            ind.definitions.append({
                "label": label,
                "type": type_str,
                "expression": body,
                "applied": True
            })

        # Build base case premises (ivar -> aval) and add as first proof lines
        # LHS
        lhs_line = ERProofLine(lhsPremise, ind.baseCase.LHS.debug, ind.baseCase.LHS.ruleSet, generics=ind.baseCase.LHS.generics)
        aval_line = ERProofLine(aval, ind.baseCase.LHS.debug, ind.baseCase.LHS.ruleSet, generics=ind.baseCase.LHS.generics)
        if lhs_line.errLog:
            return Response({"isValid": False, "errors": lhs_line.errLog}, status=status.HTTP_400_BAD_REQUEST)
        if aval_line.errLog:
            return Response({"isValid": False, "errors": aval_line.errLog}, status=status.HTTP_400_BAD_REQUEST)
        recursiveReplaceNodes(lhs_line.exprTree, [ivar], [aval_line.exprTree])
        ind.baseCase.LHS.addProofLine(str(lhs_line.exprTree))

        # RHS
        rhs_line = ERProofLine(rhsPremise, ind.baseCase.RHS.debug, ind.baseCase.RHS.ruleSet, generics=ind.baseCase.RHS.generics)
        aval_line_rhs = ERProofLine(aval, ind.baseCase.RHS.debug, ind.baseCase.RHS.ruleSet, generics=ind.baseCase.RHS.generics)
        if rhs_line.errLog:
            return Response({"isValid": False, "errors": rhs_line.errLog}, status=status.HTTP_400_BAD_REQUEST)
        if aval_line_rhs.errLog:
            return Response({"isValid": False, "errors": aval_line_rhs.errLog}, status=status.HTTP_400_BAD_REQUEST)
        recursiveReplaceNodes(rhs_line.exprTree, [ivar], [aval_line_rhs.exprTree])
        ind.baseCase.RHS.addProofLine(str(rhs_line.exprTree))

        # Build induction hypothesis nodes (ivar -> lvar) and register IH rule
        ih_lhs_line = ERProofLine(lhsPremise, ind.baseCase.LHS.debug, ind.baseCase.LHS.ruleSet, generics=ind.baseCase.LHS.generics)
        ih_rhs_line = ERProofLine(rhsPremise, ind.baseCase.RHS.debug, ind.baseCase.RHS.ruleSet, generics=ind.baseCase.RHS.generics)
        lvar_line = ERProofLine(lvar, ind.baseCase.LHS.debug, ind.baseCase.LHS.ruleSet, generics=ind.baseCase.LHS.generics)
        lvar_line_rhs = ERProofLine(lvar, ind.baseCase.RHS.debug, ind.baseCase.RHS.ruleSet, generics=ind.baseCase.RHS.generics)
        if ih_lhs_line.errLog or ih_rhs_line.errLog or lvar_line.errLog or lvar_line_rhs.errLog:
            errors = []
            errors.extend(ih_lhs_line.errLog or [])
            errors.extend(ih_rhs_line.errLog or [])
            errors.extend(lvar_line.errLog or [])
            errors.extend(lvar_line_rhs.errLog or [])
            return Response({"isValid": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        recursiveReplaceNodes(ih_lhs_line.exprTree, [ivar], [lvar_line.exprTree])
        recursiveReplaceNodes(ih_rhs_line.exprTree, [ivar], [lvar_line_rhs.exprTree])
        ind.indHypLHS = ih_lhs_line.exprTree
        ind.indHypRHS = ih_rhs_line.exprTree
        ih_rule = IH(ind.indHypLHS, ind.indHypRHS)
        ind.baseCase.ruleSet['apply']['IH'] = ih_rule
        ind.leapStep.ruleSet['apply']['IH'] = ih_rule

        # Prepare leap step: add generic for lvar, build premises with proper successor
        try:
            ind.leapStep.addGeneric(lvar, struct)
        except Exception:
            # ignore if invalid; frontend can still proceed applying IH/rules
            pass

        # Build leap successor expression based on structure
        if struct == "int":
            leap_succ_expr = f"(+ {lvar} 1)"
        elif struct == "list":
            # For list UP induction: (cons a K) where a is generic Any, K is lvar
            # Note: We created generic 'a' in start_induction_proof
            leap_succ_expr = f"(cons a {lvar})"
        else:
            leap_succ_expr = None
            
        if leap_succ_expr:
            leap_succ_line_L = ERProofLine(leap_succ_expr, ind.leapStep.LHS.debug, ind.leapStep.LHS.ruleSet, generics=ind.leapStep.LHS.generics)
            leap_succ_line_R = ERProofLine(leap_succ_expr, ind.leapStep.RHS.debug, ind.leapStep.RHS.ruleSet, generics=ind.leapStep.RHS.generics)
            lhs_leap_line = ERProofLine(lhsPremise, ind.leapStep.LHS.debug, ind.leapStep.LHS.ruleSet, generics=ind.leapStep.LHS.generics)
            rhs_leap_line = ERProofLine(rhsPremise, ind.leapStep.RHS.debug, ind.leapStep.RHS.ruleSet, generics=ind.leapStep.RHS.generics)
            if not (lhs_leap_line.errLog or rhs_leap_line.errLog or leap_succ_line_L.errLog or leap_succ_line_R.errLog):
                recursiveReplaceNodes(lhs_leap_line.exprTree, [ivar], [leap_succ_line_L.exprTree])
                recursiveReplaceNodes(rhs_leap_line.exprTree, [ivar], [leap_succ_line_R.exprTree])
                ind.leapStep.LHS.addProofLine(str(lhs_leap_line.exprTree))
                ind.leapStep.RHS.addProofLine(str(rhs_leap_line.exprTree))

        # Save engine to cache, preserving proof_id that was set by start_induction_proof
        save_induction_obj_to_cache(user, ind, existing_proof_id)

        # Persist user-supplied generics to proof.definition so session restore finds them
        if existing_proof_id and generics:
            try:
                db_proof = InductionProof.objects.get(id=existing_proof_id)
                existing_defs = list(db_proof.definition or [])
                existing_labels = {d.get('label') or d.get('name') for d in existing_defs}
                for g in generics:
                    glabel = g.get('label') or g.get('name')
                    if glabel and glabel not in existing_labels:
                        existing_defs.append({
                            'name': glabel,
                            'label': glabel,
                            'type': g.get('type', 'Any'),
                            'body': '<generic>',
                            'is_generic': True,
                            'description': f'User generic {glabel}',
                            'restrictions': g.get('restrictions') or {}
                        })
                db_proof.definition = existing_defs
                db_proof.save()
            except InductionProof.DoesNotExist:
                pass

        # Now save the properly initialized premises to database
        if existing_proof_id:
            # Save base case premises (these have ivar substituted with aval)
            if ind.baseCase.LHS.proofLines:
                save_proof_line_to_db(
                    proof_id=existing_proof_id,
                    case='base',
                    side='LHS',
                    racket=str(ind.baseCase.LHS.proofLines[0].exprTree),
                    rule='Premise',
                    start_position=0,
                    line_number=0,
                    selected_node=0,
                    json_tree=makeJson(ind.baseCase.LHS.proofLines[0].exprTree),
                    errors=ind.baseCase.LHS.proofLines[0].errors
                )
            if ind.baseCase.RHS.proofLines:
                save_proof_line_to_db(
                    proof_id=existing_proof_id,
                    case='base',
                    side='RHS',
                    racket=str(ind.baseCase.RHS.proofLines[0].exprTree),
                    rule='Premise',
                    start_position=0,
                    line_number=0,
                    selected_node=0,
                    json_tree=makeJson(ind.baseCase.RHS.proofLines[0].exprTree),
                    errors=ind.baseCase.RHS.proofLines[0].errors
                )
            # Save leap step premises (these have ivar substituted with (+ lvar 1))
            if ind.leapStep.LHS.proofLines:
                save_proof_line_to_db(
                    proof_id=existing_proof_id,
                    case='leap',
                    side='LHS',
                    racket=str(ind.leapStep.LHS.proofLines[0].exprTree),
                    rule='Premise',
                    start_position=0,
                    line_number=0,
                    selected_node=0,
                    json_tree=makeJson(ind.leapStep.LHS.proofLines[0].exprTree),
                    errors=ind.leapStep.LHS.proofLines[0].errors
                )
            if ind.leapStep.RHS.proofLines:
                save_proof_line_to_db(
                    proof_id=existing_proof_id,
                    case='leap',
                    side='RHS',
                    racket=str(ind.leapStep.RHS.proofLines[0].exprTree),
                    rule='Premise',
                    start_position=0,
                    line_number=0,
                    selected_node=0,
                    json_tree=makeJson(ind.leapStep.RHS.proofLines[0].exprTree),
                    errors=ind.leapStep.RHS.proofLines[0].errors
                )

        # Build frontend payload with jsonTrees for latest lines
        payload = {
            "isValid": True,
            "errors": [],
            "base": {
                "LHS": {
                    "racket": ind.baseCase.LHS.getPrevRacket(),
                    "jsonTree": makeJson(ind.baseCase.LHS.proofLines[-1].exprTree),
                },
                "RHS": {
                    "racket": ind.baseCase.RHS.getPrevRacket(),
                    "jsonTree": makeJson(ind.baseCase.RHS.proofLines[-1].exprTree),
                },
            },
            "leap": {
                "LHS": {
                    "racket": ind.leapStep.LHS.getPrevRacket() if len(ind.leapStep.LHS.proofLines) else "",
                    "jsonTree": makeJson(ind.leapStep.LHS.proofLines[-1].exprTree) if len(ind.leapStep.LHS.proofLines) else {},
                },
                "RHS": {
                    "racket": ind.leapStep.RHS.getPrevRacket() if len(ind.leapStep.RHS.proofLines) else "",
                    "jsonTree": makeJson(ind.leapStep.RHS.proofLines[-1].exprTree) if len(ind.leapStep.RHS.proofLines) else {},
                },
            }
        }
        return Response(payload, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        print("Error in set_current_induction_proof:", str(e))
        print(traceback.format_exc())
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


def _get_case_side(proof: IndProof, case: str, side: str) -> ERProof:
    case_key = (case or "base").lower()
    side_key = (side or "LHS").upper()
    if case_key in ("base", "anchor", "base_case"):
        ts = proof.baseCase
    elif case_key in ("leap", "step", "leap_step"):
        ts = proof.leapStep
    else:
        raise ValueError("Invalid case. Use 'base' or 'leap'.")
    if side_key not in ("LHS", "RHS"):
        raise ValueError("Invalid side. Use 'LHS' or 'RHS'.")
    return ts.LHS if side_key == "LHS" else ts.RHS


def _apply_line(target: ERProof, currentRacket: str, rule: str | None, startPosition: int | None, substitution: str | None, auto_infer: bool = False, support_rewrite_complexity = True):
    if rule:
        # Apply rule directly - don't duplicate first
        # The rule application will create a new line based on currentRacket
        if substitution is not None and substitution != "":
            target.addProofLine(currentRacket, rule, int(startPosition or 0), substitution, support_rewrite_complexity=support_rewrite_complexity)
        else:
            target.addProofLine(currentRacket, rule, int(startPosition or 0), auto_infer=auto_infer)
    else:
        # goal/premise line only
        target.addProofLine(currentRacket)


@api_view(["POST"]) 
@permission_classes([IsAuthenticated])
def apply_rule(request):
    """
    Apply a rule/substitution to the current case+side of the IndProof.
    Expected JSON: { case, side, currentRacket, rule, startPosition, selectedNode?, substitution?, lineNumber? }
    """
    from .models import InductionProofLine
    user = request.user
    data = request.data
    proof, proof_id = get_or_set_induction_obj(user)

    try:
        reload_proof_lines_from_db(proof, proof_id)
        _ensure_udfs_hydrated(proof, proof_id)
        side = data.get("side", "LHS")
        case = data.get("case", "base")
        currentRacket = data.get("currentRacket", "")
        rule = data.get("rule")
        startPosition = data.get("startPosition", 0)
        selectedNode = data.get("selectedNode")
        substitution = data.get("substitution")
        lineNumber = data.get("lineNumber")
        support_rewrite_complexity = data.get("supportRewriteComplexity", True)

        # Guard: "rewrite math" must use the Substitution button, not the rule field
        rewrite_math_error = _check_rewrite_math_misuse(rule)
        if rewrite_math_error:
            # Write the error to the previous DB line if we can identify it
            if proof_id and lineNumber is not None and lineNumber > 0:
                from .models import InductionProofLine
                prev = InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case.lower(),
                    side=side.upper(),
                    line_number=lineNumber - 1
                ).first()
                if prev:
                    sep = ", " if prev.errors else ""
                    prev.errors += f"{sep}{rewrite_math_error}"
                    prev.save()
            return Response({"isValid": False, "errors": [rewrite_math_error]}, status=status.HTTP_200_OK)

        # Check if proof engine is initialized
        if not hasattr(proof, 'baseCase') or not hasattr(proof, 'leapStep'):
            return Response({
                "isValid": False, 
                "errors": ["Proof engine not initialized. Please click 'Start Induction Proof' first."]
            }, status=status.HTTP_400_BAD_REQUEST)

        target = _get_case_side(proof, case, side)
        # Clear previous errors before attempting new rule application
        target.errLog = []
        # Mark proof incomplete when user edits
        if case == 'base':
            proof.baseCase.markIncomplete()
        else:
            proof.leapStep.markIncomplete()

        # ── Lemma injection (checks i & ii at view layer) ──────────────────
        # If the rule is "apply <name> ..." and <name> is not already in the
        # ruleset, look it up as a completed proof and inject it temporarily.
        _lemma_injected = False
        _lemma_name = None
        if rule:
            _parts = rule.split()
            if len(_parts) >= 2 and _parts[0] == "apply":
                _lemma_name = _parts[1]
                if _lemma_name not in target.ruleSet.get('apply', {}):
                    if _lemma_name == "IH":
                        # "IH" is the built-in Inductive Hypothesis rule, not a user proof.
                        # When the cache misses (server restart, cache clear) the IH rule is
                        # lost from the ruleSet. Re-register it from the stored DB strings.
                        _ih_recovered = False
                        if proof_id:
                            try:
                                _db_proof = InductionProof.objects.get(id=proof_id)
                                _ih_lhs_str = _db_proof.inductive_hypothesis_lhs
                                _ih_rhs_str = _db_proof.inductive_hypothesis_rhs
                                if _ih_lhs_str and _ih_rhs_str:
                                    _ih_lhs_line = ERProofLine(_ih_lhs_str, target.debug, target.ruleSet, generics=target.generics)
                                    _ih_rhs_line = ERProofLine(_ih_rhs_str, target.debug, target.ruleSet, generics=target.generics)
                                    if not _ih_lhs_line.errLog and not _ih_rhs_line.errLog:
                                        _ih_rule = IH(_ih_lhs_line.exprTree, _ih_rhs_line.exprTree)
                                        proof.baseCase.ruleSet['apply']['IH'] = _ih_rule
                                        proof.leapStep.ruleSet['apply']['IH'] = _ih_rule
                                        # Re-save the repaired proof to cache so future
                                        # requests don't repeat this recovery.
                                        save_induction_obj_to_cache(user, proof, proof_id)
                                        _ih_recovered = True
                            except InductionProof.DoesNotExist:
                                pass
                        if not _ih_recovered:
                            target.errLog.append("Inductive Hypothesis not available. Please restart the proof.")
                    else:
                        # Before trying a proof lookup, check if this name matches a
                        # UDF stored in the proof's definition list (handles cache-miss
                        # where the engine was rebuilt without re-hydrating UDFs).
                        _udf_recovered = False
                        if proof_id:
                            try:
                                _db_proof = InductionProof.objects.get(id=proof_id)
                                for _d in (_db_proof.definition or []):
                                    if _d.get('is_generic'):
                                        continue
                                    _dlabel = _d.get('label') or _d.get('name') or ''
                                    _dudf = _dlabel.replace('(', ' ').replace(')', ' ').split()
                                    if _dudf and _dudf[0] == _lemma_name:
                                        _dtype = _d.get('type')
                                        _dbody = _d.get('expression') or _d.get('body')
                                        if _dtype and _dbody:
                                            target.addUDF(_dlabel, _dtype, _dbody)
                                            _udf_recovered = True
                                        break
                            except InductionProof.DoesNotExist:
                                pass
                        # Also check default UDFs (e.g. reverse, append built-ins)
                        if not _udf_recovered:
                            for _d in DEFAULT_UDFS:
                                _dlabel = _d.get('label') or ''
                                _dudf = _dlabel.replace('(', ' ').replace(')', ' ').split()
                                if _dudf and _dudf[0] == _lemma_name:
                                    _dtype = _d.get('type')
                                    _dbody = _d.get('expression') or _d.get('body')
                                    if _dtype and _dbody:
                                        target.addUDF(_dlabel, _dtype, _dbody)
                                        _udf_recovered = True
                                    break
                        if not _udf_recovered:
                            _premise, _conclusion, _err = _lookup_lemma(_lemma_name, user)
                            if _err:
                                target.errLog.append(_err)
                            else:
                                _lemma_rule, _parse_err = build_lemma_rule(
                                    _lemma_name, _premise, _conclusion,
                                    target.ruleSet, target.generics
                                )
                                if _parse_err:
                                    target.errLog.append(_parse_err)
                                else:
                                    target.ruleSet['apply'][_lemma_name] = _lemma_rule
                                    _lemma_injected = True

        # Read support_value_mapping from DB (HIGH support = auto-infer params)
        _auto_infer = False
        if proof_id:
            try:
                _db_ind_proof = InductionProof.objects.get(id=proof_id)
                _auto_infer = bool(_db_ind_proof.support_value_mapping)
            except InductionProof.DoesNotExist:
                pass

        if not target.errLog:
            _apply_line(target, currentRacket, rule, startPosition, substitution, auto_infer=_auto_infer, support_rewrite_complexity=support_rewrite_complexity)

        # Remove temporarily injected lemma rule
        if _lemma_injected and _lemma_name and _lemma_name in target.ruleSet.get('apply', {}):
            del target.ruleSet['apply'][_lemma_name]

        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        jsonTree = makeJson(target.proofLines[-1].exprTree) if len(target.proofLines) else {}
        
        if not is_valid and len(target.proofLines) > 0:
            # append current line errors (lineNumber may be None if frontend didn't send it)
            current_line = target.proofLines[lineNumber - 1] if lineNumber is not None else target.proofLines[-1]
            separator = ", " if current_line.errors else ""
            current_line.errors += f'{separator}{target.errLog}'

        # Extract resultNodeId from the last proof line if available
        result_node_id = None
        if is_valid and len(target.proofLines) > 0:
            result_node_id = target.proofLines[-1].resultNodeId

        # Save to cache
        save_induction_obj_to_cache(user, proof, proof_id)
        
        rule_with_sub = None  # will hold appliedRule (with ↦ annotations) if a line was generated
        # Save to database if we have a valid proof line
        if len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_sub = last_line.appliedRule or ''
            if substitution:
                rule_with_sub = f"{rule_with_sub} {substitution}".strip()
            
            # Use lineNumber from frontend if provided (editing specific line), otherwise calculate from array length (appending)
            calculated_line_number = lineNumber if lineNumber is not None else (len(target.proofLines) - 1)
            if is_valid:
                # Update the PREVIOUS line's selected_node (where user clicked to generate this line)
                if calculated_line_number > 0:
                    try:
                        prev_line_exists = InductionProofLine.objects.filter(
                            proof_id=proof_id,
                            case=case.lower(),
                            side=side.upper(),
                            line_number=calculated_line_number - 1
                        ).exists()
                        
                        if prev_line_exists:
                            InductionProofLine.objects.filter(
                                proof_id=proof_id,
                                case=case.lower(),
                                side=side.upper(),
                                line_number=calculated_line_number - 1
                            ).update(selected_node=selectedNode)
                        else:
                            pass
                    except Exception as e:
                        # Continue anyway - this shouldn't block saving the new line
                        pass
                    
                error_value = ''
                if calculated_line_number < len(target.proofLines):
                    error_value = target.proofLines[calculated_line_number].errors

                # Save the NEW line with selected_node=None (unknown until next line generated)
                save_proof_line_to_db(
                    proof_id=proof_id,
                    case=case,
                    side=side,
                    racket=racket_str,
                    rule=rule_with_sub,
                    start_position=startPosition,
                    line_number=calculated_line_number,
                    substitution=substitution or '',
                    selected_node=None,  # Unknown until user generates next line
                    result_node=result_node_id,
                    json_tree=jsonTree,
                    errors=error_value
                )
            else:
                line_index = calculated_line_number - 1
                last_line_obj = target.proofLines[line_index]
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case.lower(),
                    side=side.upper(),
                    line_number=line_index
                ).update(errors=last_line_obj.errors)

        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "errors": target.errLog,
            "jsonTree": jsonTree,
            "lineNum": max(0, len(target.proofLines) - 1),
            "resultNodeId": result_node_id,
            "rule": rule_with_sub
        }, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"]) 
def delete_line(request, case, side, line_number):
    """Clear a proof line (blank out racket expression and rule) instead of deleting it"""
    user = request.user
    proof, proof_id = get_or_set_induction_obj(user)
    
    print(f"[DELETE_LINE] Called with case={case}, side={side}, line_number={line_number}")
    
    try:
        # Mark proof incomplete when clearing
        if case == 'base':
            proof.baseCase.markIncomplete()
        else:
            proof.leapStep.markIncomplete()
        proof.isComplete = False
        
        target = _get_case_side(proof, case, side)
        print(f"[DELETE_LINE] Target has {len(target.proofLines)} proof lines")
        
        if line_number > 0 and len(target.proofLines) > line_number:
            # Clear the line in memory by replacing it with an empty line
            # Empty string is now allowed thanks to special case in ERProofLine.__init__
            empty_line = ERProofLine("", target.debug, target.ruleSet, generics=target.generics)
            target.proofLines[line_number] = empty_line
            
            # Clear in database - update the line to have empty racket and rule
            if proof_id:
                from .models import InductionProofLine
                # Clear the current line (racket, rule, and all position markers)
                # Normalize case to lowercase and side to uppercase to match database storage
                
                # Check if line exists before update
                exists = InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case.lower(),
                    side=side.upper(),
                    line_number=line_number
                ).exists()
                
                if exists:
                    updated_count = InductionProofLine.objects.filter(
                        proof_id=proof_id,
                        case=case.lower(),
                        side=side.upper(),
                        line_number=line_number
                    ).update(
                        racket='',
                        rule='',
                        start_position=0,
                        selected_node=0,
                        result_node=0
                    )
                else:
                    # Line not found, cannot clear
                    pass
                
                # Also clear the rule on the next line (if it exists)
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case.lower(),
                    side=side.upper(),
                    line_number=line_number + 1
                ).update(rule='')
                
                # Clear selected_node (target highlight) on the previous line (if it exists)
                if line_number > 0:
                    InductionProofLine.objects.filter(
                        proof_id=proof_id,
                        case=case.lower(),
                        side=side.upper(),
                        line_number=line_number - 1
                    ).update(selected_node=0)
        
        save_induction_obj_to_cache(user, proof, proof_id)
        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in delete_line: {e}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"]) 
def check_goal(request):
    """
    Set or reset a goal/premise for a given case+side.
    JSON: { case, side, goal }
    """
    user = request.user
    data = request.data
    
    # ALWAYS create a fresh IndProof for validation during proof setup
    # This prevents contamination from stale cached proofs from previous sessions.
    # During an active proof session, the proof will be properly initialized via
    # set_current_proof and proof lines will be in the database, not cache.
    proof = IndProof()
    proof_id = None
    
    try:
        # reload_proof_lines_from_db will do nothing since proof_id is None
        reload_proof_lines_from_db(proof, proof_id)

        side = data.get("side", "LHS")
        case = data.get("case", "base")
        goal = data.get("goal")
        
        # Get the appropriate TwoSidedProof (baseCase or leapStep)
        if case == 'base':
            two_sided_proof = proof.baseCase
        else:
            two_sided_proof = proof.leapStep
        
        # Set current side for validation
        two_sided_proof.setCurrentSide(side)
        target = two_sided_proof.currentSide
        
        # Mark proof incomplete when resetting premise
        two_sided_proof.markIncomplete()
        
        # Clear and set goal
        if len(target.proofLines) != 0:
            target.proofLines.clear()
            # Clear from database too
            if proof_id:
                from .models import InductionProofLine
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case,
                    side=side
                ).delete()
        
        # Add proof line and validate
        target.addProofLine(goal)
        two_sided_proof.updateErrorsAndValidate()
        errors = two_sided_proof.getErrorsAndClear()
        
        # Get jsonTree if valid
        jsonTree = None
        if two_sided_proof.isValid and len(target.proofLines) > 0:
            jsonTree = makeJson(target.proofLines[-1].exprTree)
        
        save_induction_obj_to_cache(user, proof, proof_id)
        
        # Save premise line to database only if valid
        if proof_id and two_sided_proof.isValid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            save_proof_line_to_db(
                proof_id=proof_id,
                case=case,
                side=side,
                racket=goal,
                rule=last_line.appliedRule or 'Premise',
                start_position=0,
                line_number=0,
                selected_node=0
            )
        
        return Response({"isValid": two_sided_proof.isValid, "errors": errors, "jsonTree": jsonTree}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"]) 
def substitution(request):
    from .models import InductionProofLine
    user = request.user
    data = request.data
    proof, proof_id = get_or_set_induction_obj(user)
    try:
        reload_proof_lines_from_db(proof, proof_id)
        _ensure_udfs_hydrated(proof, proof_id)

        case = data.get("case", "base")
        side = data.get("side", "LHS")
        rule = data.get("rule")
        if rule and rule.lower() == "math":
            rule = "rewrite math"
        elif rule and rule.lower() == "logic":
            rule = "rewrite logic"
        currentRacket = data.get("currentRacket", "")
        startPosition = data.get("startPosition", 0)
        selectedNode = data.get("selectedNode")
        substitution = data.get("substitution")
        lineNumber = data.get("lineNumber")
        support_rewrite_complexity = data.get("supportRewriteComplexity")

        target = _get_case_side(proof, case, side)
        # Clear previous errors before attempting new substitution
        target.errLog = []
        # Mark proof incomplete when user edits
        if case == 'base':
            proof.baseCase.markIncomplete()
        else:
            proof.leapStep.markIncomplete()
        _apply_line(target, currentRacket, rule, startPosition, substitution, support_rewrite_complexity)

        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        jsonTree = makeJson(target.proofLines[-1].exprTree) if is_valid and len(target.proofLines) > 0 else {}
        
        # Get the rule from the engine - it formats it correctly with "with" keyword
        rule_with_sub = ''
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_sub = last_line.appliedRule or rule or ''
            # Append substitution value to show "rewrite math with (* 0 2) as 0"
            if substitution:
                rule_with_sub = f"{rule_with_sub} as {substitution}"

        if not is_valid and len(target.proofLines) > 0 and lineNumber is not None:
            # append current line errors
            current_line = target.proofLines[lineNumber - 1]
            separator = ", " if current_line.errors else ""
            current_line.errors += f'{separator}{target.errLog}'

        save_induction_obj_to_cache(user, proof, proof_id)
        
        # Extract resultNodeId from the last proof line
        result_node_id = 0
        if is_valid and len(target.proofLines) > 0:
            result_node_id = target.proofLines[-1].resultNodeId
        
        # Save to database if we have a valid proof line
        if len(target.proofLines) > 0:            
            last_line = target.proofLines[-1]                
            # Use lineNumber from frontend if provided (editing specific line), otherwise calculate from array length (appending)
            calculated_line_number = lineNumber if lineNumber is not None else (len(target.proofLines) - 1)
            
            if is_valid:
                # Update the PREVIOUS line's selected_node (where user clicked to generate this line)
                if calculated_line_number > 0:
                    prev_line_exists = InductionProofLine.objects.filter(
                        proof_id=proof_id,
                        case=case.lower(),
                        side=side.upper(),
                        line_number=calculated_line_number - 1
                    ).exists()
                    
                    if prev_line_exists:
                        InductionProofLine.objects.filter(
                            proof_id=proof_id,
                            case=case.lower(),
                            side=side.upper(),
                            line_number=calculated_line_number - 1
                        ).update(selected_node=startPosition)
                    else:
                        pass

                error_value = ''
                if calculated_line_number < len(target.proofLines):
                    error_value = target.proofLines[calculated_line_number].errors

                # Save the NEW line with selected_node=None (unknown until next line generated)
                save_proof_line_to_db(
                    proof_id=proof_id,
                    case=case,
                    side=side,
                    racket=racket_str,
                    rule=rule_with_sub,
                    start_position=startPosition,
                    line_number=calculated_line_number,
                    substitution=substitution or '',
                    selected_node=None,  # Unknown until user generates next line
                    result_node=result_node_id,
                    json_tree=jsonTree,
                    errors=error_value
                )
            else:
                line_index = calculated_line_number - 1
                last_line_obj = target.proofLines[line_index]
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case.lower(),
                    side=side.upper(),
                    line_number=line_index
                ).update(errors=last_line_obj.errors)

        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "jsonTree": jsonTree,
            "rule": rule_with_sub,
            "resultNodeId": result_node_id,
            "errors": target.errLog
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def check_completion(request):
    """
    Check if a specific case (base or leap) is complete.
    Expected JSON: { case: 'base' | 'leap' }
    Returns: { isComplete: bool, label: str, overallComplete: bool }
    """
    user = request.user
    data = request.data
    proof, proof_id = get_or_set_induction_obj(user)
    
    try:
        # Reload proof lines from database before checking completion
        reload_proof_lines_from_db(proof, proof_id)
        
        case = data.get("case", "base")
        is_student = not user.is_instructor
        
        if case == 'base':
            is_complete = proof.baseCase.checkComplete(is_student)
            label = "BASE CASE"
        elif case == 'leap':
            is_complete = proof.leapStep.checkComplete(is_student)
            label = "LEAP STEP"
        else:
            return Response({"error": "Invalid case. Use 'base' or 'leap'."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check overall completion and update indProof.isComplete
        is_mathematically_complete = proof.checkComplete(user.is_instructor)

        # Check if there are any hidden fields remaining
        has_hidden_fields = False
        if not user.is_instructor and proof_id:
            has_hidden_fields = InductionProofLine.objects.filter(
                proof_id=proof_id, case=case
            ).filter(
                models.Q(hide_expression=True) | models.Q(hide_justification=True)
            ).exists()
        
        # Proof is only complete if mathematically correct AND no hidden fields
        overall_complete = is_mathematically_complete and not has_hidden_fields
        # Persist overall completion status to database
        if proof_id:
            InductionProof.objects.filter(id=proof_id).update(is_complete=overall_complete)

            # update assignment if it exists and is completed for the first time
            if overall_complete:
                content_type = ContentType.objects.get(app_label="induction_api", model="inductionproof")
                mapping = StudentProofMapping.objects.filter(
                    content_type=content_type,
                    object_id=proof_id
                ).first()

                # If it belongs to an assignment, lock in the completion timestamp
                if mapping:
                    # Only set it if it hasn't been completed before
                    if not mapping.completed_at:
                        mapping.completed_at = timezone.now()
                        mapping.save()

        # Save updated completion status to cache
        save_induction_obj_to_cache(user, proof, proof_id)
        
        return Response({
            "isComplete": is_complete,
            "label": label,
            "overallComplete": overall_complete
        }, status=status.HTTP_200_OK)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_proof_lines(request):
    """
    Get all proof lines from the database for the current proof.
    Returns: {
        base: {
            LHS: [{ racket, rule, startPosition, selectedNode, lineNumber }, ...],
            RHS: [{ racket, rule, startPosition, selectedNode, lineNumber }, ...]
        },
        leap: {
            LHS: [{ racket, rule, startPosition, selectedNode, lineNumber }, ...],
            RHS: [{ racket, rule, startPosition, selectedNode, lineNumber }, ...]
        }
    }
    """
    user = request.user
    _, proof_id = get_or_set_induction_obj(user)
    
    if proof_id is None:
        return Response({
            "base": {"LHS": [], "RHS": []},
            "leap": {"LHS": [], "RHS": []}
        }, status=status.HTTP_200_OK)
    
    try:
        from .models import InductionProofLine
        
        # Get all proof lines for this proof
        lines = InductionProofLine.objects.filter(proof_id=proof_id).order_by('case', 'side', 'line_number')
        
        # Organize by case and side
        result = {
            'base': {'LHS': [], 'RHS': []},
            'leap': {'LHS': [], 'RHS': []}
        }
        
        for line in lines:
            # Use stored jsonTree if available, otherwise try to parse racket string
            json_tree = line.json_tree
            
            # If json_tree is empty (old data before migration), try to parse it
            if not json_tree or not isinstance(json_tree, dict) or len(json_tree) == 0:
                try:
                    # Get the proof engine to access rulesets and generics
                    ind, _ = get_or_set_induction_obj(request.user)
                    
                    # Determine which case/side to use for parsing context
                    if line.case == 'base':
                        target = ind.baseCase.LHS if line.side == 'LHS' else ind.baseCase.RHS
                    else:
                        target = ind.leapStep.LHS if line.side == 'LHS' else ind.leapStep.RHS
                    
                    # Parse with proper context
                    from expression_tree.ERProofEngine import ERProofLine
                    temp_line = ERProofLine(
                        line.racket, 
                        target.debug, 
                        target.ruleSet, 
                        generics=target.generics
                    )
                    if temp_line.exprTree and not temp_line.errLog:
                        json_tree = makeJson(temp_line.exprTree)
                        # Update the database with the parsed tree
                        line.json_tree = json_tree
                        line.save()
                    else:
                        json_tree = {}
                except Exception as parse_error:
                    json_tree = {}
            
            line_data = {
                'racket': line.racket,
                'rule': line.rule,
                'startPosition': line.start_position,
                'selectedNode': line.selected_node,
                'resultNode': line.result_node,
                'lineNumber': line.line_number,
                'substitution': line.substitution,
                'jsonTree': json_tree,
                'errors': line.errors,
                'hide_expression': line.hide_expression,
                'hide_justification': line.hide_justification
            }
            result[line.case][line.side].append(line_data)
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in get_proof_lines: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_current_proof(request):
    """
    Get the current proof metadata from the database.
    Returns proof parameters like induction_variable, anchor_value, goals, etc.
    """
    user = request.user
    _, proof_id = get_or_set_induction_obj(user)
    
    if proof_id is None:
        return Response({"hasProof": False}, status=status.HTTP_200_OK)
    
    try:
        proof = InductionProof.objects.get(id=proof_id, user=user)
        
        return Response({
            "hasProof": True,
            "inductionVariable": proof.induction_variable,
            "anchorValue": proof.anchor_value,
            "leapVariable": proof.leap_variable,
            "lhsAnchorGoal": proof.lhs_anchor_goal or "",
            "rhsAnchorGoal": proof.rhs_anchor_goal or "",
            "lhsLeapGoal": proof.lhs_leap_goal or "",
            "rhsLeapGoal": proof.rhs_leap_goal or "",
            "inductiveHypothesisLHS": proof.inductive_hypothesis_lhs or "",
            "inductiveHypothesisRHS": proof.inductive_hypothesis_rhs or "",
            "currentSide": proof.current_side,
            "isAnchorCase": proof.is_anchor_case,
            "proofName": proof.name or "",
            "tag": proof.tag or "",
            "proof_id": proof.id,
            "support_errors": proof.support_errors,
            "support_current_lhs_rhs": proof.support_current_lhs_rhs,
            "support_ih": proof.support_ih,
            "support_premise": proof.support_premise,
            "support_rule_set": proof.support_rule_set,
            "visible_rules": parse_visible_rules(proof.visible_rules),
            "support_value_mapping": proof.support_value_mapping,
            "support_rewrite_complexity": proof.support_rewrite_complexity,
        }, status=status.HTTP_200_OK)
    except InductionProof.DoesNotExist:
        return Response({"hasProof": False}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in get_current_proof: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def clear_all_proof_lines(request):
    """
    Delete all proof lines for the current proof from the database.
    Useful for starting fresh without creating a new proof.
    """
    user = request.user
    proof, proof_id = get_or_set_induction_obj(user)
    
    if proof_id is None:
        return Response({"message": "No active proof to clear"}, status=status.HTTP_200_OK)
    
    try:
        from .models import InductionProofLine
        
        # Delete all proof lines for this proof
        deleted_count = InductionProofLine.objects.filter(proof_id=proof_id).delete()[0]
        
        # Clear the in-memory proof lines too
        proof.baseCase.LHS.proofLines = []
        proof.baseCase.RHS.proofLines = []
        proof.leapStep.LHS.proofLines = []
        proof.leapStep.RHS.proofLines = []
        
        save_induction_obj_to_cache(user, proof, proof_id)
        
        print(f"[CLEAR] Deleted {deleted_count} proof lines from database")
        return Response({
            "message": f"Cleared {deleted_count} proof lines",
            "deleted_count": deleted_count
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in clear_all_proof_lines: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_induction_session_by_id(request):
    user = request.user
    proof_id = request.data.get('proof_id')
    
    try:
        proof = get_object_or_404(InductionProof, id=proof_id)
        if (proof.user != user):
            proof_content_type = ContentType.objects.get_for_model(InductionProof)
        
            is_authorized_instructor = StudentProofMapping.objects.filter(
                object_id=proof.id,
                content_type=proof_content_type,
                assignment__course__instructor=user
            ).exists()

            if not is_authorized_instructor:
                return Response({"hasProof": False}, status=status.HTTP_403_FORBIDDEN)
        
        # 1. Initialize the Engine
        ind_proof = IndProof()
        
        # 2. HYDRATE THE ENGINE
        ind_proof.struct = 'list' if proof.induction_type == 'lists' else 'int'
        ind_proof.ivar = proof.induction_variable
        ind_proof.aval = proof.anchor_value
        ind_proof.lvar = proof.leap_variable
        
        # Fallback goals if lines are empty
        ind_proof.lhsPremise = proof.lhs_leap_goal 
        ind_proof.rhsPremise = proof.rhs_leap_goal 
        
        # 3. Load Definitions & Generics
        # First, always load all default UDFs into the engine
        for d in DEFAULT_UDFS:
            label = d.get('label')
            type_str = d.get('type')
            body = d.get('expression')
            if label and type_str and body:
                ind_proof.baseCase.addUDF(label, type_str, body)
                ind_proof.leapStep.addUDF(label, type_str, body)

        db_defs = proof.definition or []
        for d in db_defs:
            if d.get('is_generic'):
                # Handle 'name' vs 'label' mismatch
                label = d.get('label') or d.get('name')
                g_type = d.get('type', 'int')
                # FIX: Ensure restrictions is a dict, never None
                restrictions = d.get('restrictions') or {} 
                
                if label:
                    # Add to Base Case (LHS & RHS)
                    try:
                        ind_proof.baseCase.LHS.addGeneric(label, g_type, restrictions)
                        ind_proof.baseCase.RHS.addGeneric(label, g_type, restrictions)
                    except Exception: 
                        pass 

                    # Add to Leap Step (LHS & RHS)
                    try:
                        ind_proof.leapStep.LHS.addGeneric(label, g_type, restrictions)
                        ind_proof.leapStep.RHS.addGeneric(label, g_type, restrictions)
                    except Exception: 
                        pass
            else:
                # Load User Defined Functions (UDFs)
                label = d.get('label') or d.get('name')
                type_str = d.get('type')
                body = d.get('expression') or d.get('body')
                if label and type_str and body:
                    ind_proof.baseCase.addUDF(label, type_str, body)
                    ind_proof.leapStep.addUDF(label, type_str, body)
        
        # 4. Load Proof Lines
        reload_proof_lines_from_db(ind_proof, proof_id)
        
        # 5. Save fully hydrated engine to Cache
        save_induction_obj_to_cache(user, ind_proof, proof_id)

        return Response({"success": True}, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_proof(request):
    """
    Endpoint to mark a proof as deleted in the database (`is_active=False`).
    """
    proof_id = request.data.get('proof_id')
    user = request.user
    try:
        if proof_id is not None:
            # 1. Update the DB
            updated_count = InductionProof.objects.filter(id=proof_id, user=user).update(is_active=False)
            
            if updated_count == 0:
                return Response({"error": "Proof not found"}, status=status.HTTP_404_NOT_FOUND)

            # 2. Clear cache if active proof_id is the same as the current cache
            cached = cache.get(f"induction_proof_{user.username}") 
            cache_cleared = False
            if cached:
                cached_proof = loads(cached)
                cached_proof_id = cached_proof.get('id')   

                if cached_proof_id == proof_id:
                    cache_cleared = True
                    cache.delete(f"induction_proof_{user.username}")

            return Response({
                "success": True,
                "message": "Proofed marked as inactive",
                "cacheCleared": cache_cleared
            }, status=status.HTTP_200_OK)    

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {"message": f"Error setting proof to inactive: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
        )

def parse_visible_rules(raw_val):
    """Safely parse the TextField string back into a dictionary for the frontend."""
    if isinstance(raw_val, str) and raw_val.strip():
        try:
            return json.loads(raw_val)
        except json.JSONDecodeError:
            return {}
    elif isinstance(raw_val, dict):
        return raw_val
    return {}

PARAM_FIELDS = [
    'support_errors',
    'support_current_lhs_rhs',
    'support_ih',
    'support_premise',
    'support_rule_set',
    'support_value_mapping',
    'visible_rules',
    'support_rewrite_complexity'
]


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def set_parameters(request):
    """Instructor-only: update the 6 support param fields on an InductionProof."""
    user = request.user
    if not user.is_instructor:
        return Response({"error": "Instructor access required"}, status=status.HTTP_403_FORBIDDEN)
    proof_id = request.data.get('proof_id')
    try:
        proof = InductionProof.objects.get(id=proof_id, user=user)
    except InductionProof.DoesNotExist:
        return Response({"error": "Proof not found"}, status=status.HTTP_404_NOT_FOUND)
    for field in PARAM_FIELDS:
        if field in request.data:
            val = request.data[field]
            if field == 'visible_rules' and isinstance(val, dict):
                val = json.dumps(val)
            setattr(proof, field, val)
    proof.save()
    return Response({f: getattr(proof, f) for f in PARAM_FIELDS}, status=status.HTTP_200_OK)


def _unique_proof_name(user, base_name):
    """Return base_name if unused for this user, else append '(copy)', '(copy 2)', etc."""
    from equational_reasoning_api.models import EquationalProof as _ERProof
    candidate = base_name
    suffix = 1
    while True:
        ind_taken = InductionProof.objects.filter(user=user, name=candidate, is_active=True).exists()
        er_taken = _ERProof.objects.filter(user=user, name=candidate, is_active=True).exists()
        if not er_taken and not ind_taken:
            return candidate
        candidate = f"{base_name} (copy)" if suffix == 1 else f"{base_name} (copy {suffix})"
        suffix += 1


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_proof(request):
    """Export the full induction proof as a JSON payload for browser download."""
    user = request.user
    proof_id = request.GET.get('proof_id')
    if not proof_id:
        return Response({"error": "proof_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        proof = InductionProof.objects.get(id=proof_id, user=user, is_active=True)
    except InductionProof.DoesNotExist:
        return Response({"error": "Proof not found"}, status=status.HTTP_404_NOT_FOUND)
    from .models import InductionProofLine
    def get_side_lines(case, side):
        lines = InductionProofLine.objects.filter(proof=proof, case=case, side=side).order_by('line_number')
        return [
            {
                'lineNumber': l.line_number,
                'racket': l.racket,
                'rule': l.rule,
                'startPosition': l.start_position,
                'selectedNode': l.selected_node,
                'resultNode': l.result_node,
                'substitution': l.substitution,
                'jsonTree': l.json_tree,
            }
            for l in lines
        ]
    data = {
        'proofType': 'induction',
        'name': proof.name or '',
        'tag': proof.tag or '',
        'proofSubtype': proof.proof_type,
        'inductionType': proof.induction_type,
        'inductionVariable': proof.induction_variable,
        'anchorValue': proof.anchor_value,
        'leapVariable': proof.leap_variable,
        'lhsAnchorGoal': proof.lhs_anchor_goal or '',
        'rhsAnchorGoal': proof.rhs_anchor_goal or '',
        'lhsLeapGoal': proof.lhs_leap_goal or '',
        'rhsLeapGoal': proof.rhs_leap_goal or '',
        'inductiveHypothesisLHS': proof.inductive_hypothesis_lhs or '',
        'inductiveHypothesisRHS': proof.inductive_hypothesis_rhs or '',
        'definition': proof.definition if proof.definition is not None else [],
        'support_errors': proof.support_errors,
        'support_current_lhs_rhs': proof.support_current_lhs_rhs,
        'support_ih': proof.support_ih,
        'support_premise': proof.support_premise,
        'support_rule_set': proof.support_rule_set,
        'visible_rules': parse_visible_rules(proof.visible_rules),
        'support_value_mapping': proof.support_value_mapping,
        'support_rewrite_complexity': proof.support_rewrite_complexity,
        'lines': {
            'base': {
                'LHS': get_side_lines('base', 'LHS'),
                'RHS': get_side_lines('base', 'RHS'),
            },
            'leap': {
                'LHS': get_side_lines('leap', 'LHS'),
                'RHS': get_side_lines('leap', 'RHS'),
            },
        },
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_proof(request):
    """Import an induction proof from a JSON payload and create a new proof record."""
    user = request.user
    data = request.data
    if data.get('proofType') != 'induction':
        return Response({"error": "This file is not an induction proof."}, status=status.HTTP_400_BAD_REQUEST)
    base_name = (data.get('name') or 'Untitled').strip() or 'Untitled'
    name = _unique_proof_name(user, base_name)
    try:
        from .models import InductionProofLine
        proof = InductionProof.objects.create(
            user=user,
            name=name,
            tag=data.get('tag') or '',
            proof_type=data.get('proofSubtype', 'induction_int'),
            induction_type=data.get('inductionType', 'integers'),
            induction_variable=data.get('inductionVariable', ''),
            anchor_value=data.get('anchorValue', ''),
            leap_variable=data.get('leapVariable', ''),
            lhs_anchor_goal=data.get('lhsAnchorGoal', ''),
            rhs_anchor_goal=data.get('rhsAnchorGoal', ''),
            lhs_leap_goal=data.get('lhsLeapGoal', ''),
            rhs_leap_goal=data.get('rhsLeapGoal', ''),
            inductive_hypothesis_lhs=data.get('inductiveHypothesisLHS', ''),
            inductive_hypothesis_rhs=data.get('inductiveHypothesisRHS', ''),
            definition=data.get('definition', []),
            support_errors=data.get('support_errors', True),
            support_current_lhs_rhs=data.get('support_current_lhs_rhs', True),
            support_ih=data.get('support_ih', True),
            support_premise=data.get('support_premise', True),
            support_rule_set=data.get('support_rule_set', True),
            visible_rules=data.get('visible_rules', {}),
            support_value_mapping=data.get('support_value_mapping', True),
            support_rewrite_complexity=data.get('support_rewrite_complexity', True)
        )
        lines_data = data.get('lines', {})
        for case in ('base', 'leap'):
            case_lines = lines_data.get(case, {})
            for side in ('LHS', 'RHS'):
                for line in case_lines.get(side, []):
                    InductionProofLine.objects.create(
                        proof=proof,
                        case=case,
                        side=side,
                        line_number=int(line.get('lineNumber') or 0),
                        racket=line.get('racket') or '',
                        rule=line.get('rule') or '',
                        start_position=int(line.get('startPosition') or 0),
                        selected_node=int(line.get('selectedNode') or 0),
                        result_node=int(line.get('resultNode') or 0),
                        substitution=line.get('substitution') or '',
                        json_tree=line.get('jsonTree') or {},
                    )
        return Response({'proofId': proof.id, 'proofName': name}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def normalize_whitespace(text):
    """Remove all whitespace for comparison"""
    return re.sub(r'\s+', ' ', text.strip())

def compare_exact(student_input, actual_value):
    """
    Compare two racket expressions for exact match (whitespace-agnostic).
    Order matters: (+ 2 1) != (+ 1 2)
    """
    return normalize_whitespace(student_input) == normalize_whitespace(actual_value)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def validate_hidden_field(request):
    """
    Validate student input against hidden field value.
    Validates Rule + Selection OR Expression via AST JSON tree comparison.
    """    
    user = request.user
    
    # 1. Grab the fully populated engine from the cache instead of manually reading it
    proof_obj, proof_id = get_or_set_induction_obj(user)
    
    if not proof_id:
        return Response({"error": "No active proof session found. Please reload."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 2. Extract Data
        side = request.data.get('side')
        case = request.data.get('case')
        line_number = request.data.get('lineNumber')
        student_expression = request.data.get('studentExpression')
        student_rule = request.data.get('studentRule')
        student_selected = request.data.get('studentSelectedNode') 
        
        if not side or line_number is None:
            return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine target side to get the correct rules and generics
        currentCase = proof_obj.baseCase if case == 'base' else proof_obj.leapStep
        target = currentCase.LHS if side.upper() == 'LHS' else currentCase.RHS
        
        # 3. Get Database Line
        try:
            line = InductionProofLine.objects.get(
                proof_id=proof_id, side=side.upper(), line_number=line_number, case=case.lower()
            )
        except InductionProofLine.DoesNotExist:
            return Response({"error": "Line not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            prev_line = InductionProofLine.objects.get(
                proof_id=proof_id, 
                side=side.upper(), 
                line_number=(line_number - 1)
            )
        except InductionProofLine.DoesNotExist:
            prev_line = None

        errors = []
        changed = False
        
        # 4. Logic: Master Key Validation (Rule + Selection)
        if student_rule is not None:
            rule_text_match = compare_exact(student_rule, line.rule)
            
            selection_match = True
            if prev_line.selected_node is not None and student_selected is not None:
                 if int(student_selected) != int(prev_line.selected_node):
                     selection_match = False
                     errors.append("Incorrect selection.")

            if rule_text_match and selection_match:
                if line.hide_justification:
                    line.hide_justification = False
                    changed = True
            elif not rule_text_match:
                errors.append("Rule does not match.")
        else:
            errors.append("You must provide a rule.")
        
        # 5. Logic: Expression Tree Match (JSON Dictionary Comparison)
        if student_expression is not None and student_expression.strip() != "":
            try:
                # Use the target's actual ruleSet and generics so UDFs are parsed correctly
                temp_line = ERProofLine(
                    student_expression, 
                    target.debug, 
                    target.ruleSet, 
                    generics=target.generics
                )
                
                if not temp_line.errLog:
                    raw_student_tree = makeJson(temp_line.exprTree)
                    
                    student_tree = json.loads(json.dumps(raw_student_tree))
                    
                    # 3. Deep compare
                    if student_tree == line.json_tree:
                        line.hide_expression = False
                        changed = True
                    else:
                        errors.append("Expression does not match.")
                else:
                    errors.append("Syntax error in expression.")
            except Exception as e:
                errors.append(f"Error parsing expression: {str(e)}")
        else:
            errors.append("You must provide an expression.")

        if not errors and changed:
            line.save()
        
        message = "Correct!" if not errors else None
        
        return Response({
            "isValid": not errors,
            "errors": errors,
            "hide_expression": line.hide_expression,
            "hide_justification": line.hide_justification,
            "message": message
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def validate_hidden_definition(request):
    """
    Validate a student's expression against a hidden definition.
    Case A: definition has a stored expression — student must match the tree exactly.
    Case B: definition has no expression (student-entry mode) — any valid parse is accepted,
            stored in the DB proof record and registered in the engine cache.
    """
    user = request.user
    label = request.data.get("label")
    student_expression = request.data.get("student_expression", "").strip()
    if not label or not student_expression:
        return Response({"error": "Missing label or student_expression."}, status=status.HTTP_400_BAD_REQUEST)
    ind, proof_id = get_or_set_induction_obj(user)
    if not proof_id:
        return Response({"error": "No active proof session found."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        db_proof = InductionProof.objects.get(id=proof_id)
    except InductionProof.DoesNotExist:
        return Response({"error": "Proof not found."}, status=status.HTTP_400_BAD_REQUEST)
    definitions = list(db_proof.definition or [])
    target_idx = None
    target_def = None
    for idx, d in enumerate(definitions):
        if d.get("label") == label and not d.get("is_generic"):
            target_idx = idx
            target_def = d
            break
    if target_def is None:
        return Response({"error": "Definition not found."}, status=status.HTTP_400_BAD_REQUEST)
    if not target_def.get("expression_hidden"):
        return Response({"error": "Definition is not hidden."}, status=status.HTTP_400_BAD_REQUEST)
    # Parse the student input using the ER engine
    temp_proof = ERProof()
    temp_proof.addProofLine(student_expression)
    if temp_proof.errLog:
        return Response({"isValid": False, "message": "Syntax error in expression."}, status=status.HTTP_200_OK)
    student_tree = makeJson(temp_proof.proofLines[-1].exprTree)
    stored_expression = target_def.get("expression", "")
    if stored_expression:
        # Case A: compare trees
        stored_proof = ERProof()
        stored_proof.addProofLine(stored_expression)
        if stored_proof.errLog:
            return Response({"error": "Stored expression is unparseable."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        stored_tree = makeJson(stored_proof.proofLines[-1].exprTree)
        if student_tree == stored_tree:
            return Response({"isValid": True, "expression": stored_expression}, status=status.HTTP_200_OK)
        else:
            return Response({"isValid": False, "message": "the input expression does not match the hidden definition"}, status=status.HTTP_200_OK)
    else:
        # Case B: student-entry mode — accept any valid expression
        def_type = target_def.get("type") or target_def.get("def_type", "")
        definitions[target_idx] = dict(target_def)
        definitions[target_idx]["expression"] = student_expression
        InductionProof.objects.filter(id=proof_id).update(definition=definitions)
        ind.baseCase.addUDF(label, def_type, student_expression)
        ind.leapStep.addUDF(label, def_type, student_expression)
        save_induction_obj_to_cache(user, ind, proof_id)
        return Response({"isValid": True, "expression": student_expression}, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_visibility(request):
    user = request.user
    
    # 1. Get the session object
    proof_obj, proof_id = get_or_set_induction_obj(user)
    
    if not proof_id:
        return Response({"error": "Session expired or invalid proof ID"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reload_proof_lines_from_db(proof_obj, proof_id)

        side = request.data.get('side')
        line_number = request.data.get('lineNumber')
        field = request.data.get('field') 
        case = request.data.get('case')
        
        if not side or line_number is None or field not in ['expression', 'justification'] or not case:
            return Response({"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        side = side.upper()
        target_case = proof_obj.baseCase if case == 'base' else proof_obj.leapStep
        target_proof = target_case.LHS if side == 'LHS' else target_case.RHS
        
        # Now this check will pass because proofLines is fully populated
        if line_number < 0 or line_number >= len(target_proof.proofLines):
            return Response({
                "error": f"Line number {line_number} out of bounds. Total lines: {len(target_proof.proofLines)}"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        line_obj = target_proof.proofLines[line_number]
        
        # Toggle attribute in Memory
        attr_name = 'hide_expression' if field == 'expression' else 'hide_justification'
        current_val = getattr(line_obj, attr_name, False)
        new_val = not current_val
        setattr(line_obj, attr_name, new_val)

        # Save updated object to Cache
        save_induction_obj_to_cache(user, proof_obj, proof_id)
        
        # Update Database
        try:
            db_line = InductionProofLine.objects.get(
                proof_id=proof_id, side=side, line_number=line_number, case=case
            )
            if field == 'expression':
                db_line.hide_expression = new_val
            else:
                db_line.hide_justification = new_val
            db_line.save()
        except InductionProofLine.DoesNotExist:
            pass 

        return Response({
            "success": True,
            "line_number": line_number,
            "side": side,
            "field": field,
            "new_value": new_val
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_visibility_premise(request):
    user = request.user
    
    # 1. Get the session object
    proof_obj, proof_id = get_or_set_induction_obj(user)
    
    if not proof_id:
        return Response({"error": "Session expired or invalid proof ID"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reload_proof_lines_from_db(proof_obj, proof_id)

        side = request.data.get('side')
        line_number = request.data.get('lineNumber')
        field = request.data.get('field') 
        case = request.data.get('case')
        setting_visibility = request.data.get('setting_visibility')
        
        if not side or line_number is None or field not in ['expression', 'justification'] or not case:
            return Response({"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        side = side.upper()
        target_case = proof_obj.baseCase if case == 'base' else proof_obj.leapStep
        target_proof = target_case.LHS if side == 'LHS' else target_case.RHS
        
        # Now this check will pass because proofLines is fully populated
        if line_number < 0 or line_number >= len(target_proof.proofLines):
            return Response({
                "error": f"Line number {line_number} out of bounds. Total lines: {len(target_proof.proofLines)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        line_obj = target_proof.proofLines[line_number]
        
        # Toggle attribute in Memory
        attr_name = 'hide_expression' if field == 'expression' else 'hide_justification'
        current_val = getattr(line_obj, attr_name, False)
        new_val = setting_visibility if setting_visibility is not None else not current_val
        setattr(line_obj, attr_name, new_val)

        # Save updated object to Cache
        save_induction_obj_to_cache(user, proof_obj, proof_id)
        
        # Update Database
        try:
            db_line = InductionProofLine.objects.get(
                proof_id=proof_id, side=side, line_number=line_number, case=case
            )
            if field == 'expression':
                db_line.hide_expression = new_val
            else:
                db_line.hide_justification = new_val
            db_line.save()
        except InductionProofLine.DoesNotExist:
            pass 

        return Response({
            "success": True,
            "line_number": line_number,
            "side": side,
            "field": field,
            "new_value": new_val
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def save_comment(request):
    if request.method != "POST":
        return Response(
            {"error": "POST required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = request.user
        _, proof_id = get_or_set_induction_obj(user)

        data = request.data

        side = data.get("side")
        line_number = data.get("line_number")
        role = data.get("role")
        comment_text = data.get("comment")

        if not all([side, line_number is not None, role]):
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment_obj, created = InductionProofLineComment.objects.update_or_create(
            proof_id=proof_id,
            side=side,
            line_number=line_number,
            role=role,
            defaults={
                "comment": comment_text
            }
        )

        return Response({
            "success": True,
            "created": created
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
@api_view(["GET"])
def get_comments(request):

    try:
        user = request.user
        _, proof_id = get_or_set_induction_obj(user)

        side = request.GET.get("side")
        line_number = int(request.GET.get("line_number"))

        comments = InductionProofLineComment.objects.filter(
            proof_id=proof_id,
            side=side,
            line_number=line_number
        )

        result = {
            "student": "",
            "instructor": ""
        }

        for c in comments:

            if c.role == "student":
                result["student"] = c.comment

            elif c.role == "instructor":
                result["instructor"] = c.comment

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:

        print("GET COMMENTS ERROR:", e)

        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
@api_view(["GET"])
def get_comment_status(request):

    try:

        user = request.user
        _, proof_id = get_or_set_induction_obj(user)

        if proof_id is None:
            return Response({}, status=status.HTTP_200_OK)

        comments = InductionProofLineComment.objects.filter(
            proof_id=proof_id
        )

        result = {}

        for comment in comments:

            # Ignore blank comments
            if not comment.comment or comment.comment.strip() == "":
                continue

            key = f"{comment.side}-{comment.line_number}"

            result[key] = True

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:

        print(f"GET COMMENT STATUS ERROR: {str(e)}")

        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )