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

# ER Engine imports for induction proof wiring
from expression_tree.IndProofs import IndProof
from expression_tree.ERProofEngine import TwoSidedProof, ERProof, ERProofLine
from expression_tree.ERCommon import makeJson
from expression_tree.ERRuleset import recursiveReplaceNodes, IH


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
    """Archive (soft delete) the current active proof for the user"""
    from .models import InductionProof
    user = request.user
    
    try:
        # Find the active proof
        proof = InductionProof.objects.filter(user=user, is_active=True).order_by('-created_at').first()
        
        if proof:
            # Archive it (soft delete)
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
def start_induction_proof(request):
    user = request.user
    json_data = request.data
    
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
        
        # Validate required fields
        if not all([proof_name, induction_variable, anchor_value is not None, leap_variable]):
            return Response(
                {"error": "Missing required fields: proof_name, induction_variable, anchor_value, and leap_variable are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 1. Validate that iVar, aVal, and Lvar are all integers
        try:
            anchor_value_int = int(anchor_value)
        except (ValueError, TypeError):
            return Response(
                {"error": "Anchor value (aVal) must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        # 4. Automatically create a generic variable definition for Lvar
        generic_definition = {
            'name': leap_variable,
            'type': 'int',
            'body': '<generic>',
            'description': f'Generic variable for leap case in induction on {induction_variable}'
        }
        
        # Create complete proof data
        proof_data = {
            'user': user.id,
            'name': proof_name,
            'tag': proof_tag,
            'proof_type': 'induction_int',
            'induction_type': induction_type,
            'induction_variable': induction_variable,
            'anchor_value': anchor_value_int,
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
            'definition': [generic_definition],
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
                    "generic_definition_created": generic_definition,
                    "data": serializer.data
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

@api_view(["POST"])
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


def reload_proof_lines_from_db(proof, proof_id):
    """Reload all proof lines from database into the IndProof object"""
    from .models import InductionProofLine
    
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
        
        print(f"[RELOAD PROOF LINES] Loading {lines.count()} proof lines from database")
        print("[DB LOAD] Result node values from database:")
        for line in lines:
            print(f"  Line {line.line_number} ({line.case} {line.side}): result_node={line.result_node}, selected_node={line.selected_node}")
        
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
            
            print(f"[RELOAD] Restored {line.case} {line.side} line {line.line_number}: selectedNode={line.selected_node}")
    except Exception as e:
        print(f"[RELOAD ERROR] {str(e)}")
        pass


def save_proof_line_to_db(proof_id, case, side, racket, rule, start_position, line_number, substitution='', selected_node=None, result_node=None, json_tree=None):
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
        # LOG: Verify result_node is being saved
        print(f"[DB SAVE] Line {line_number} ({case} {side}): result_node={result_node_id}, selected_node={node_id}")
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
            }
        )
        print(f"[DB SAVE] Successfully saved line {line_number}")
    except InductionProof.DoesNotExist:
        print(f"[DB SAVE ERROR] Proof {proof_id} doesn't exist")
    except Exception as e:
        print(f"[DB SAVE ERROR] Failed to save line {line_number}: {e}")
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
        definitions = data.get("definitions", [])

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

        # Prepare leap step: add generic for lvar, build premises ivar -> (+ lvar 1) for int structure
        try:
            ind.leapStep.addGeneric(lvar, struct)
        except Exception:
            # ignore if invalid; frontend can still proceed applying IH/rules
            pass

        leap_succ_expr = f"(+ {lvar} 1)" if struct == "int" else None
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
                    selected_node=0
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
                    selected_node=0
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
                    selected_node=0
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
                    selected_node=0
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


def _apply_line(target: ERProof, currentRacket: str, rule: str | None, startPosition: int | None, substitution: str | None):
    if rule:
        # Apply rule directly - don't duplicate first
        # The rule application will create a new line based on currentRacket
        if substitution is not None and substitution != "":
            target.addProofLine(currentRacket, rule, int(startPosition or 0), substitution)
        else:
            target.addProofLine(currentRacket, rule, int(startPosition or 0))
    else:
        # goal/premise line only
        target.addProofLine(currentRacket)


@api_view(["POST"]) 
def apply_rule(request):
    """
    Apply a rule/substitution to the current case+side of the IndProof.
    Expected JSON: { case, side, currentRacket, rule, startPosition, selectedNode?, substitution? }
    """
    from .models import InductionProofLine
    user = request.user
    data = request.data
    proof, proof_id = get_or_set_induction_obj(user)

    try:
        side = data.get("side", "LHS")
        case = data.get("case", "base")
        currentRacket = data.get("currentRacket", "")
        rule = data.get("rule")
        startPosition = data.get("startPosition", 0)
        selectedNode = data.get("selectedNode")
        substitution = data.get("substitution")

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
        _apply_line(target, currentRacket, rule, startPosition, substitution)

        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        jsonTree = makeJson(target.proofLines[-1].exprTree) if len(target.proofLines) else {}
        
        # Extract resultNodeId from the last proof line if available
        result_node_id = None
        if is_valid and len(target.proofLines) > 0:
            result_node_id = target.proofLines[-1].resultNodeId
            print(f"[APPLY_RULE] selectedNode from request: {selectedNode}, startPosition from request: {startPosition}, result_node_id from ERProof: {result_node_id}")

        # Save to cache
        save_induction_obj_to_cache(user, proof, proof_id)
        
        # Save to database if we have a valid proof line
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_sub = last_line.appliedRule or ''
            if substitution:
                rule_with_sub = f"{rule_with_sub} {substitution}".strip()
            
            calculated_line_number = len(target.proofLines) - 1
            
            print(f"[APPLY_RULE] About to save line {calculated_line_number}: proof_id={proof_id}, case={case}, side={side}")
            
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
                        print(f"[APPLY_RULE] Updating line {calculated_line_number - 1} selected_node to {startPosition}")
                        InductionProofLine.objects.filter(
                            proof_id=proof_id,
                            case=case.lower(),
                            side=side.upper(),
                            line_number=calculated_line_number - 1
                        ).update(selected_node=startPosition)
                    else:
                        print(f"[APPLY_RULE] Line {calculated_line_number - 1} doesn't exist in DB (probably premise), skipping update")
                except Exception as e:
                    print(f"[APPLY_RULE ERROR] Failed to update previous line: {e}")
                    # Continue anyway - this shouldn't block saving the new line
            
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
                json_tree=jsonTree
            )

        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "errors": target.errLog,
            "jsonTree": jsonTree,
            "lineNum": max(0, len(target.proofLines) - 1),
            "resultNodeId": result_node_id
        }, status=status.HTTP_200_OK)
    except Exception as e:
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
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case,
                    side=side,
                    line_number=line_number
                ).update(
                    racket='',
                    rule='',
                    start_position=0,
                    selected_node=0,
                    result_node=0
                )
                
                # Also clear the rule on the next line (if it exists)
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case,
                    side=side,
                    line_number=line_number + 1
                ).update(rule='')
                
                # Clear selected_node (target highlight) on the previous line (if it exists)
                if line_number > 0:
                    InductionProofLine.objects.filter(
                        proof_id=proof_id,
                        case=case,
                        side=side,
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
    proof, proof_id = get_or_set_induction_obj(user)
    try:
        side = data.get("side", "LHS")
        case = data.get("case", "base")
        goal = data.get("goal")
        target = _get_case_side(proof, case, side)
        
        # Mark proof incomplete when resetting premise
        if case == 'base':
            proof.baseCase.markIncomplete()
        else:
            proof.leapStep.markIncomplete()
        
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
        target.addProofLine(goal)
        jsonTree = makeJson(target.proofLines[-1].exprTree)
        save_induction_obj_to_cache(user, proof, proof_id)
        
        # Save premise line to database
        if proof_id and len(target.proofLines) > 0:
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
        return Response({"isValid": True, "errors": [], "jsonTree": jsonTree}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"]) 
def substitution(request):
    from .models import InductionProofLine
    user = request.user
    data = request.data
    proof, proof_id = get_or_set_induction_obj(user)
    try:
        side = data.get("side", "LHS")
        case = data.get("case", "base")
        rule = data.get("rule")
        if rule and rule.lower() == "math":
            rule = "rewrite math"
        currentRacket = data.get("currentRacket", "")
        startPosition = data.get("startPosition", 0)
        selectedNode = data.get("selectedNode")
        substitution = data.get("substitution")

        target = _get_case_side(proof, case, side)
        # Clear previous errors before attempting new substitution
        target.errLog = []
        # Mark proof incomplete when user edits
        if case == 'base':
            proof.baseCase.markIncomplete()
        else:
            proof.leapStep.markIncomplete()
        _apply_line(target, currentRacket, rule, startPosition, substitution)

        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        jsonTree = makeJson(target.proofLines[-1].exprTree)
        
        # Get the rule from the engine - it formats it correctly with "with" keyword
        rule_with_sub = ''
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_sub = last_line.appliedRule or rule or ''
            # Append substitution value to show "rewrite math with (* 0 2) as 0"
            if substitution:
                rule_with_sub = f"{rule_with_sub} as {substitution}"

        save_induction_obj_to_cache(user, proof, proof_id)
        
        # Extract resultNodeId from the last proof line
        result_node_id = 0
        if is_valid and len(target.proofLines) > 0:
            result_node_id = target.proofLines[-1].resultNodeId
            print(f"[SUBSTITUTION] selectedNode from request: {selectedNode}, startPosition from request: {startPosition}, result_node_id from ERProof: {result_node_id}")
        
        # Save to database if we have a valid proof line
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            calculated_line_number = len(target.proofLines) - 1
            
            # Update the PREVIOUS line's selected_node (where user clicked to generate this line)
            if calculated_line_number > 0:
                prev_line_exists = InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case.lower(),
                    side=side.upper(),
                    line_number=calculated_line_number - 1
                ).exists()
                
                if prev_line_exists:
                    print(f"[SUBSTITUTION] Updating line {calculated_line_number - 1} selected_node to {startPosition}")
                    InductionProofLine.objects.filter(
                        proof_id=proof_id,
                        case=case.lower(),
                        side=side.upper(),
                        line_number=calculated_line_number - 1
                    ).update(selected_node=startPosition)
                else:
                    print(f"[SUBSTITUTION] Line {calculated_line_number - 1} doesn't exist in DB (probably premise), skipping update")
            
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
                result_node=result_node_id
            )
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
        
        if case == 'base':
            is_complete = proof.baseCase.checkComplete()
            label = "BASE CASE"
        elif case == 'leap':
            is_complete = proof.leapStep.checkComplete()
            label = "LEAP STEP"
        else:
            return Response({"error": "Invalid case. Use 'base' or 'leap'."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check overall completion and update indProof.isComplete
        overall_complete = proof.checkComplete()
        
        # Save updated completion status to cache
        save_induction_obj_to_cache(user, proof, proof_id)
        
        return Response({
            "isComplete": is_complete,
            "label": label,
            "overallComplete": overall_complete
        }, status=status.HTTP_200_OK)
    except Exception as e:
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
                        print(f"[get_proof_lines] Parsed and saved jsonTree for line {line.line_number}")
                    else:
                        json_tree = {}
                except Exception as parse_error:
                    print(f"[get_proof_lines] Failed to parse line {line.line_number}: {parse_error}")
                    json_tree = {}
            
            line_data = {
                'racket': line.racket,
                'rule': line.rule,
                'startPosition': line.start_position,
                'selectedNode': line.selected_node,
                'resultNode': line.result_node,
                'lineNumber': line.line_number,
                'substitution': line.substitution,
                'jsonTree': json_tree
            }
            print(f"[get_proof_lines] Line {line.line_number} ({line.case} {line.side}): selectedNode={line.selected_node}, resultNode={line.result_node}")
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
            "tag": proof.tag or ""
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

