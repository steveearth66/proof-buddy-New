from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from dill import dumps, loads
from django.core.cache import cache
from .models import EquationalProof, EquationalProofLine
from .serializers import EquationalProofSerializer
from proofs.views import use_uploaded_generic

# ER Engine imports
from expression_tree.ERProofEngine import TwoSidedProof, ERProof, ERProofLine
from expression_tree.ERCommon import makeJson
from expression_tree.ERRuleset import isMatch
from expression_tree.default_udfs import DEFAULT_UDFS

User = get_user_model()


# ========================
# Cache Management Helpers
# ========================

def save_equational_obj_to_cache(user, proof_obj, proof_id=None):
    """Save TwoSidedProof object to cache"""
    cached_data = {
        'proof_obj': dumps(proof_obj),
        'proof_id': proof_id
    }
    cache.set(f"equational_obj_{user.username}", cached_data, timeout=None)


def get_or_set_equational_obj(user):
    """Get TwoSidedProof object and associated proof ID from cache"""
    cached = cache.get(f"equational_obj_{user.username}")
    if cached is None:
        proof_obj = TwoSidedProof()
        save_equational_obj_to_cache(user, proof_obj)
        return proof_obj, None
    proof_id = cached.get('proof_id')
    return loads(cached['proof_obj']), proof_id


def reload_proof_lines_from_db(proof_obj, proof_id):
    """Reload all proof lines from database into the TwoSidedProof object"""
    if proof_id is None:
        return
    
    try:
        # Clear existing proof lines
        proof_obj.LHS.proofLines = []
        proof_obj.RHS.proofLines = []
        
        # Get all proof lines for this proof, ordered by line number
        lines = EquationalProofLine.objects.filter(proof_id=proof_id).order_by('side', 'line_number')
        
        for line in lines:
            # Determine which ERProof to add to
            target = proof_obj.LHS if line.side == 'LHS' else proof_obj.RHS
            
            # Create ERProofLine and add to target
            proof_line = ERProofLine(line.racket, target.debug, target.ruleSet, generics=target.generics)
            
            if proof_line.errLog == []:
                # Store metadata
                proof_line.appliedRule = line.rule
                proof_line.appliedRuleNodeId = line.selected_node
                proof_line.resultNodeId = line.result_node
                target.proofLines.append(proof_line)
    except Exception as e:
        print(f"Error reloading proof lines: {e}")


def save_proof_line_to_db(proof_id, side, racket, rule='', start_position=0, line_number=0, 
                         substitution='', selected_node=0, result_node=0):
    """Save or update a proof line in the database"""
    from .models import EquationalProofLine
    
    json_tree = {}
    try:
        # Create temporary ERProof to parse the racket expression
        temp_proof = ERProof()
        temp_proof.addProofLine(racket)
        if temp_proof.errLog == [] and len(temp_proof.proofLines) > 0:
            json_tree = makeJson(temp_proof.proofLines[-1].exprTree)
    except Exception as e:
        print(f"Error creating json_tree: {e}")
    
    # Use update_or_create to handle both insert and update
    EquationalProofLine.objects.update_or_create(
        proof_id=proof_id,
        side=side.upper(),
        line_number=line_number,
        defaults={
            'racket': racket,
            'json_tree': json_tree,
            'rule': rule,
            'substitution': substitution,
            'start_position': start_position,
            'selected_node': selected_node,
            'result_node': result_node
        }
    )


# ========================
# API Endpoints
# ========================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_current_proof(request):
    """
    Initialize a new equational proof with LHS and RHS goals.
    Expected JSON: { lhsPremise, rhsPremise, definitions: [] }
    """
    import sys
    print("[DEBUG] equational set_current_proof called", flush=True)  # Log to console for debugging
    sys.stdout.flush()
    user = request.user
    data = request.data
    print(f"[DEBUG] User: {user.username}, Data keys: {data.keys()}", flush=True)  # Log to console for debugging
    sys.stdout.flush()
    
    try:
        lhs_premise = data.get("lhsPremise")
        rhs_premise = data.get("rhsPremise")
        definitions = data.get("definitions", [])
        generics = data.get("generics", [])
        print(f"[DEBUG] lhs_premise: {lhs_premise}, rhs_premise: {rhs_premise}", flush=True)
        print(f"[DEBUG] Received {len(definitions)} definitions: {definitions}", flush=True)
        print(f"[DEBUG] Received {len(generics)} generics: {generics}", flush=True)  # Log to console for debugging
        
        # Basic validation
        if not lhs_premise or not rhs_premise:
            print("[DEBUG] Missing premise - returning 400", flush=True)  # Log to console for debugging
            return Response({
                "isValid": False, 
                "errors": ["Both lhsPremise and rhsPremise are required"]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a fresh TwoSidedProof engine
        _, existing_proof_id = get_or_set_equational_obj(user)
        proof_obj = TwoSidedProof()
        
        # Add user definitions (UDF) to both LHS and RHS rule sets
        for d in definitions:
            # Check if this is a default UDF (skip database operations)
            is_default = d.get("is_default", False) or d.get("deletable", True) == False
            
            label = d.get("label")
            type_str = d.get("type")
            body = d.get("expression")
            if not label or not type_str or body is None:
                continue
            proof_obj.LHS.addUDF(label, type_str, body)
            proof_obj.RHS.addUDF(label, type_str, body)
        
        # Add generics to both LHS and RHS
        errors = []
        for g in generics:
            try:
                use_uploaded_generic(user, proof_obj, g)
            except Exception as e:
                errors.append(str(e))
        
        if errors:
            return Response({
                "isValid": False,
                "errors": errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build premises and add as first proof lines
        # LHS
        print(f"[DEBUG] Creating LHS line from: {lhs_premise}", flush=True)  # Log to console for debugging
        lhs_line = ERProofLine(lhs_premise, proof_obj.LHS.debug, proof_obj.LHS.ruleSet, generics=proof_obj.LHS.generics)
        if lhs_line.errLog != []:
            print(f"[DEBUG] LHS line has errors: {lhs_line.errLog}", flush=True)  # Log to console for debugging
            return Response({
                "isValid": False,
                "errors": lhs_line.errLog
            }, status=status.HTTP_400_BAD_REQUEST)
        lhs_line.appliedRule = "Premise"
        proof_obj.LHS.proofLines.append(lhs_line)
        
        # RHS
        print(f"[DEBUG] Creating RHS line from: {rhs_premise}", flush=True)  # Log to console for debugging
        rhs_line = ERProofLine(rhs_premise, proof_obj.RHS.debug, proof_obj.RHS.ruleSet, generics=proof_obj.RHS.generics)
        if rhs_line.errLog != []:
            print(f"[DEBUG] RHS line has errors: {rhs_line.errLog}", flush=True)  # Log to console for debugging
            return Response({
                "isValid": False,
                "errors": rhs_line.errLog
            }, status=status.HTTP_400_BAD_REQUEST)
        rhs_line.appliedRule = "Premise"
        proof_obj.RHS.proofLines.append(rhs_line)
        
        # Debug: Check generics before saving
        print(f"[DEBUG] LHS generics before cache: {proof_obj.LHS.generics}", flush=True)
        print(f"[DEBUG] RHS generics before cache: {proof_obj.RHS.generics}", flush=True)
        
        # Save to cache
        save_equational_obj_to_cache(user, proof_obj, existing_proof_id)
        
        # Save to database if we have a proof_id
        if existing_proof_id:
            # Save LHS premise
            save_proof_line_to_db(
                proof_id=existing_proof_id,
                side='LHS',
                racket=lhs_premise,
                rule='Premise',
                line_number=0
            )
            # Save RHS premise
            save_proof_line_to_db(
                proof_id=existing_proof_id,
                side='RHS',
                racket=rhs_premise,
                rule='Premise',
                line_number=0
            )
        
        return Response({
            "isValid": True,
            "lhsPremise": lhs_premise,
            "rhsPremise": rhs_premise,
            "lhsJsonTree": makeJson(lhs_line.exprTree),
            "rhsJsonTree": makeJson(rhs_line.exprTree)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_msg = f"Exception in set_current_proof: {str(e)}"
        print(error_msg, flush=True)  # Log to console for debugging
        print(traceback.format_exc(), flush=True)  # Log full stack trace for debugging
        return Response({
            "isValid": False,
            "errors": [error_msg]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_rule(request):
    """
    Apply a rule to the current side of the proof.
    Expected JSON: { side, currentRacket, rule, startPosition, selectedNode?, substitution?, lineNumber? }
    """
    from .models import EquationalProofLine
    user = request.user
    data = request.data
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    # Debug: Check generics after loading from cache
    print(f"[DEBUG] apply_rule - LHS generics from cache: {proof_obj.LHS.generics}", flush=True)
    print(f"[DEBUG] apply_rule - RHS generics from cache: {proof_obj.RHS.generics}", flush=True)
    
    try:
        side = data.get("side", "LHS")
        current_racket = data.get("currentRacket", "")
        rule = data.get("rule")
        start_position = data.get("startPosition", 0)
        selected_node = data.get("selectedNode")
        substitution = data.get("substitution")
        line_number = data.get("lineNumber")
        
        target = proof_obj.LHS if side == "LHS" else proof_obj.RHS
        
        # Clear previous errors
        target.errLog = []
        
        # Mark proof incomplete when user edits
        proof_obj.isComplete = False
        
        # Apply the rule
        if substitution is not None and substitution != "":
            target.addProofLine(current_racket, rule, int(start_position or 0), substitution)
        else:
            target.addProofLine(current_racket, rule, int(start_position or 0))
        
        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        
        # Get rule and node info
        rule_with_params = ''
        result_node_id = 0
        json_tree = {}
        
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_params = last_line.appliedRule or rule or ''
            result_node_id = last_line.resultNodeId
            json_tree = makeJson(last_line.exprTree)
        
        save_equational_obj_to_cache(user, proof_obj, proof_id)
        
        # Save to database
        if is_valid and len(target.proofLines) > 0:
            calculated_line_number = line_number if line_number is not None else (len(target.proofLines) - 1)
            
            # Update previous line's selected_node
            if line_number is None and proof_id:
                prev_line_exists = EquationalProofLine.objects.filter(
                    proof_id=proof_id,
                    side=side.upper(),
                    line_number=calculated_line_number - 1
                ).exists()
                
                if prev_line_exists:
                    EquationalProofLine.objects.filter(
                        proof_id=proof_id,
                        side=side.upper(),
                        line_number=calculated_line_number - 1
                    ).update(selected_node=start_position)
            
            # Save the new line
            if proof_id:  # Only save to DB if we have a proof_id
                save_proof_line_to_db(
                    proof_id=proof_id,
                    side=side,
                    racket=racket_str,
                    rule=rule_with_params,
                    start_position=start_position,
                    line_number=calculated_line_number,
                    substitution=substitution or '',
                    selected_node=None,
                    result_node=result_node_id
                )
        
        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "jsonTree": json_tree,
            "rule": rule_with_params,
            "resultNodeId": result_node_id,
            "errors": target.errLog
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "isValid": False,
            "errors": [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def substitution(request):
    """
    Apply a substitution to the current side.
    Expected JSON: { side, currentRacket, rule, startPosition, substitution, lineNumber? }
    """
    from .models import EquationalProofLine
    user = request.user
    data = request.data
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    try:
        side = data.get("side", "LHS")
        rule = data.get("rule")
        if rule and rule.lower() == "math":
            rule = "rewrite math"
        current_racket = data.get("currentRacket", "")
        start_position = data.get("startPosition", 0)
        selected_node = data.get("selectedNode")
        substitution_expr = data.get("substitution")
        line_number = data.get("lineNumber")
        
        target = proof_obj.LHS if side == "LHS" else proof_obj.RHS
        target.errLog = []
        proof_obj.isComplete = False
        
        # Apply substitution
        if substitution_expr is not None and substitution_expr != "":
            target.addProofLine(current_racket, rule, int(start_position or 0), substitution_expr)
        else:
            target.addProofLine(current_racket, rule, int(start_position or 0))
        
        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        json_tree = makeJson(target.proofLines[-1].exprTree) if is_valid and len(target.proofLines) > 0 else {}
        
        rule_with_sub = ''
        result_node_id = 0
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_sub = last_line.appliedRule or rule or ''
            if substitution_expr:
                rule_with_sub = f"{rule_with_sub} as {substitution_expr}"
            result_node_id = last_line.resultNodeId
        
        save_equational_obj_to_cache(user, proof_obj, proof_id)
        
        # Save to database
        if is_valid and len(target.proofLines) > 0:
            calculated_line_number = line_number if line_number is not None else (len(target.proofLines) - 1)
            
            if calculated_line_number > 0 and proof_id:
                prev_line_exists = EquationalProofLine.objects.filter(
                    proof_id=proof_id,
                    side=side.upper(),
                    line_number=calculated_line_number - 1
                ).exists()
                
                if prev_line_exists:
                    EquationalProofLine.objects.filter(
                        proof_id=proof_id,
                        side=side.upper(),
                        line_number=calculated_line_number - 1
                    ).update(selected_node=start_position)
            
            if proof_id:  # Only save to DB if we have a proof_id
                save_proof_line_to_db(
                    proof_id=proof_id,
                    side=side,
                    racket=racket_str,
                    rule=rule_with_sub,
                    start_position=start_position,
                    line_number=calculated_line_number,
                    substitution=substitution_expr or '',
                    selected_node=None,
                    result_node=result_node_id
                )
        
        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "jsonTree": json_tree,
            "rule": rule_with_sub,
            "resultNodeId": result_node_id,
            "errors": target.errLog
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "isValid": False,
            "errors": [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_line(request, side, line_number):
    """Clear a proof line (blank out racket expression and rule)"""
    user = request.user
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    try:
        proof_obj.isComplete = False
        target = proof_obj.LHS if side == "LHS" else proof_obj.RHS
        
        if line_number > 0 and len(target.proofLines) > line_number:
            # Clear the line in memory
            empty_line = ERProofLine("", target.debug, target.ruleSet, generics=target.generics)
            target.proofLines[line_number] = empty_line
            
            # Clear in database
            if proof_id:
                EquationalProofLine.objects.filter(
                    proof_id=proof_id,
                    side=side.upper(),
                    line_number=line_number
                ).update(
                    racket='',
                    rule='',
                    json_tree={},
                    start_position=0,
                    selected_node=0,
                    result_node=0,
                    substitution=''
                )
        
        save_equational_obj_to_cache(user, proof_obj, proof_id)
        
        return Response({
            "success": True,
            "message": "Line cleared successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def check_completion(request):
    """
    Check if the proof is complete.
    Returns: { isComplete: bool }
    """
    user = request.user
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    try:
        # Reload proof lines from database
        reload_proof_lines_from_db(proof_obj, proof_id)
        
        # Check if proof is complete
        is_complete = proof_obj.checkComplete()
        
        # Update database
        if proof_id:
            EquationalProof.objects.filter(id=proof_id).update(is_complete=is_complete)
        
        proof_obj.isComplete = is_complete
        save_equational_obj_to_cache(user, proof_obj, proof_id)
        
        return Response({
            "isComplete": is_complete,
            "message": "Proof complete!" if is_complete else "Proof incomplete"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_proof_lines(request):
    """
    Get all proof lines for both LHS and RHS.
    Returns: { LHS: [...], RHS: [...] }
    """
    user = request.user
    _, proof_id = get_or_set_equational_obj(user)
    
    if not proof_id:
        return Response({
            "LHS": [],
            "RHS": []
        }, status=status.HTTP_200_OK)
    
    try:
        lhs_lines = EquationalProofLine.objects.filter(
            proof_id=proof_id,
            side='LHS'
        ).order_by('line_number').values(
            'line_number', 'racket', 'rule', 'json_tree',
            'selected_node', 'result_node', 'substitution'
        )
        
        rhs_lines = EquationalProofLine.objects.filter(
            proof_id=proof_id,
            side='RHS'
        ).order_by('line_number').values(
            'line_number', 'racket', 'rule', 'json_tree',
            'selected_node', 'result_node', 'substitution'
        )
        
        return Response({
            "LHS": list(lhs_lines),
            "RHS": list(rhs_lines)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

