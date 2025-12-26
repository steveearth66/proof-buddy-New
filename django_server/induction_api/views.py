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
        'inductive_hypothesis_lhs' : validated_data['inductive_hypothesis_lhs'],
        'inductive_hypothesis_rhs' : validated_data['inductive_hypothesis_rhs'],
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
    
    print(f"User: {user.username}")
    print("Received induction data:", json_data)
    
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
        
        print(f"Processing induction proof for user: {user.username}")
        
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
        
        print("Proof data for serializer:", proof_data)
        
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
    return loads(cached['ind_proof']), cached.get('proof_id')

def save_proof_line_to_db(proof_id, case, side, racket, rule, start_position, line_number, substitution=''):
    """Save a proof line to the database"""
    from .models import InductionProofLine, InductionProof
    if proof_id is None:
        return
    try:
        proof = InductionProof.objects.get(id=proof_id)
        InductionProofLine.objects.create(
            proof=proof,
            case=case,
            side=side,
            racket=racket,
            rule=rule or '',
            substitution=substitution or '',
            start_position=start_position,
            line_number=line_number
        )
    except InductionProof.DoesNotExist:
        pass  # Proof doesn't exist in DB yet


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

        # Create engine object and assign core params (follow tests pattern)
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

        # Save engine to cache (without proof_id for now, as this is just engine setup)
        save_induction_obj_to_cache(user, ind)

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
    Expected JSON: { case, side, currentRacket, rule, startPosition, substitution? }
    """
    user = request.user
    data = request.data
    proof, proof_id = get_or_set_induction_obj(user)

    try:
        side = data.get("side", "LHS")
        case = data.get("case", "base")
        currentRacket = data.get("currentRacket", "")
        rule = data.get("rule")
        startPosition = data.get("startPosition", 0)
        substitution = data.get("substitution")

        target = _get_case_side(proof, case, side)
        # Clear previous errors before attempting new rule application
        target.errLog = []
        _apply_line(target, currentRacket, rule, startPosition, substitution)

        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        jsonTree = makeJson(target.proofLines[-1].exprTree) if len(target.proofLines) else {}

        # Save to cache
        save_induction_obj_to_cache(user, proof, proof_id)
        
        # Save to database if we have a valid proof line
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_sub = last_line.appliedRule or ''
            if substitution:
                rule_with_sub = f"{rule_with_sub} {substitution}".strip()
            save_proof_line_to_db(
                proof_id=proof_id,
                case=case,
                side=side,
                racket=racket_str,
                rule=rule_with_sub,
                start_position=startPosition,
                line_number=len(target.proofLines) - 1,
                substitution=substitution or ''
            )

        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "errors": target.errLog,
            "jsonTree": jsonTree,
            "lineNum": max(0, len(target.proofLines) - 1)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"]) 
def delete_line(request, case, side):
    user = request.user
    proof, proof_id = get_or_set_induction_obj(user)
    try:
        target = _get_case_side(proof, case, side)
        line_number = len(target.proofLines) - 1
        if len(target.proofLines) > 0:
            target.deleteProofLine()
            # Delete from database if we have proof_id
            if proof_id:
                from .models import InductionProofLine
                InductionProofLine.objects.filter(
                    proof_id=proof_id,
                    case=case,
                    side=side,
                    line_number=line_number
                ).delete()
        save_induction_obj_to_cache(user, proof, proof_id)
        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        # Log error but still return 200 if deletion completed
        print(f"Warning in delete_line: {e}")
        return Response(status=status.HTTP_200_OK)


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
                line_number=0
            )
        return Response({"isValid": True, "errors": [], "jsonTree": jsonTree}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"]) 
def substitution(request):
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
        substitution = data.get("substitution")

        target = _get_case_side(proof, case, side)
        # Clear previous errors before attempting new substitution
        target.errLog = []
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
        
        # Save to database if we have a valid proof line
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            save_proof_line_to_db(
                proof_id=proof_id,
                case=case,
                side=side,
                racket=racket_str,
                rule=rule_with_sub,
                start_position=startPosition,
                line_number=len(target.proofLines) - 1,
                substitution=substitution or ''
            )
        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "jsonTree": jsonTree,
            "rule": rule_with_sub,
            "errors": target.errLog
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"isValid": False, "errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)