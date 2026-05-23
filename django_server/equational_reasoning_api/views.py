import json
import re
import traceback
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from dill import dumps, loads
from django.core.cache import cache
from django.db import models

from .models import EquationalProof, EquationalProofLine, EquationalProofLineComment
from proofs.views import use_uploaded_generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# ER Engine imports
from expression_tree.ERProofEngine import TwoSidedProof, ERProof, ERProofLine
from expression_tree.ERCommon import makeJson
from expression_tree.ERRuleset import isMatch
from expression_tree.default_udfs import DEFAULT_UDFS
from expression_tree.LemmaApplicator import build_lemma_rule

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
    from .models import EquationalProof as _EqProof
    from induction_api.models import InductionProof as _IndProof

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


def _ensure_er_hydrated(proof_obj, proof_id):
    """Re-register any UDFs and generics missing from the TwoSidedProof engine.
    Safety net for cache-miss / server-restart scenarios where the proof object is
    rebuilt fresh (no UDFs, no generics). Reads the stored definitions from the DB
    EquationalProof.definition field and replays addUDF / addGeneric for anything
    that isn't already present in the ruleSet."""
    if not proof_id:
        return
    try:
        _db_proof = EquationalProof.objects.get(id=proof_id)
        all_defs = list(_db_proof.definition or [])
    except EquationalProof.DoesNotExist:
        return

    sides = [proof_obj.LHS, proof_obj.RHS]
    for _d in all_defs:
        if _d.get('is_generic'):
            _glabel = _d.get('label') or _d.get('name') or ''
            _gtype = (_d.get('type') or 'int').lower()
            _grestrictions = _d.get('restrictions') or {}
            if not _glabel:
                continue
            for side in sides:
                if _glabel not in side.generics:
                    try:
                        side.addGeneric(_glabel, _gtype, _grestrictions)
                        side.errLog = []
                    except Exception:
                        pass
        else:
            _dlabel = _d.get('label') or _d.get('name') or ''
            _udf_name = _dlabel.replace('(', ' ').replace(')', ' ').split()
            if not _udf_name:
                continue
            _udf_name = _udf_name[0]
            _dtype = _d.get('type') or _d.get('def_type')
            _dbody = _d.get('expression') or _d.get('body')
            if not _dtype or not _dbody:
                continue
            for side in sides:
                if _udf_name not in side.ruleSet.get('apply', {}):
                    side.addUDF(_dlabel, _dtype, _dbody)
                    side.errLog = []


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
            proof_line.errors = line.errors

            if proof_line.errLog == []:
                # Store metadata
                proof_line.appliedRule = line.rule
                proof_line.appliedRuleNodeId = line.selected_node
                proof_line.resultNodeId = line.result_node
                target.proofLines.append(proof_line)
                proof_line.hide_expression = line.hide_expression
                proof_line.hide_justification = line.hide_justification
    except Exception as e:
        print(f"Error reloading proof lines: {e}")


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


def save_proof_line_to_db(proof_id, side, racket, rule='', start_position=0, line_number=0,
                         substitution='', selected_node=0, result_node=0,
                         hide_expression=False, hide_justification=False, errors=''):
    """Save or update a proof line in the database"""
    
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
            'result_node': result_node,
            'hide_expression': hide_expression,
            'hide_justification': hide_justification,
            'errors': errors
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
    user = request.user
    data = request.data
    
    try:
        lhs_premise = data.get("lhsPremise")
        rhs_premise = data.get("rhsPremise")
        definitions = data.get("definitions", [])
        generics = data.get("generics", [])
        
        # Basic validation
        if not lhs_premise or not rhs_premise:
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
        lhs_line = ERProofLine(lhs_premise, proof_obj.LHS.debug, proof_obj.LHS.ruleSet, generics=proof_obj.LHS.generics)
        if lhs_line.errLog != []:
            return Response({
                "isValid": False,
                "errors": lhs_line.errLog
            }, status=status.HTTP_400_BAD_REQUEST)
        lhs_line.appliedRule = "Premise"
        proof_obj.LHS.proofLines.append(lhs_line)
        
        # RHS
        rhs_line = ERProofLine(rhs_premise, proof_obj.RHS.debug, proof_obj.RHS.ruleSet, generics=proof_obj.RHS.generics)
        if rhs_line.errLog != []:
            return Response({
                "isValid": False,
                "errors": rhs_line.errLog
            }, status=status.HTTP_400_BAD_REQUEST)
        rhs_line.appliedRule = "Premise"
        proof_obj.RHS.proofLines.append(rhs_line)
        
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
        error_msg = f"Exception in set_current_proof: {str(e)}"
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
    user = request.user
    data = request.data
    proof_obj, proof_id = get_or_set_equational_obj(user)
    _ensure_er_hydrated(proof_obj, proof_id)
    
    try:
        # Reload proof lines from database
        reload_proof_lines_from_db(proof_obj, proof_id)

        # Read support_value_mapping from DB (HIGH support = auto-infer params)
        _auto_infer = False
        if proof_id:
            try:
                _db_proof = EquationalProof.objects.get(id=proof_id)
                _auto_infer = bool(_db_proof.support_value_mapping)
            except EquationalProof.DoesNotExist:
                pass

        side = data.get("side", "LHS")
        current_racket = data.get("currentRacket", "")
        rule = data.get("rule")
        start_position = data.get("startPosition", 0)
        selected_node = data.get("selectedNode")
        substitution = data.get("substitution")
        line_number = data.get("lineNumber")
        support_rewrite_complexity = data.get("supportRewriteComplexity", True)

        # Guard: "rewrite math" must use the Substitution button, not the rule field
        rewrite_math_error = _check_rewrite_math_misuse(rule)
        if rewrite_math_error:
            # Write the error to the previous DB line if we can identify it
            if proof_id and line_number is not None and line_number > 0:
                prev = EquationalProofLine.objects.filter(
                    proof_id=proof_id,
                    side=side.upper(),
                    line_number=line_number - 1
                ).first()
                if prev:
                    sep = ", " if prev.errors else ""
                    prev.errors += f"{sep}{rewrite_math_error}"
                    prev.save()
            return Response({"isValid": False, "errors": [rewrite_math_error]}, status=status.HTTP_200_OK)

        target = proof_obj.LHS if side == "LHS" else proof_obj.RHS

        # Clear previous errors
        target.errLog = []
        
        # Mark proof incomplete when user edits
        proof_obj.isComplete = False

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

        # Apply the rule (skip if we already have errors from lemma lookup)
        if not target.errLog:
            if substitution is not None and substitution != "":
                target.addProofLine(current_racket, rule, int(start_position or 0), substitution, support_rewrite_complexity=support_rewrite_complexity)
            else:
                target.addProofLine(current_racket, rule, int(start_position or 0), auto_infer=_auto_infer)

        # Remove temporarily injected lemma rule
        if _lemma_injected and _lemma_name and _lemma_name in target.ruleSet.get('apply', {}):
            del target.ruleSet['apply'][_lemma_name]
        
        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        
        # Get rule and node info
        rule_with_params = ''
        result_node_id = 0
        json_tree = {}
        
        if not is_valid and len(target.proofLines) > 0:
            # append current line errors
            current_line = target.proofLines[line_number - 1]
            separator = ", " if current_line.errors else ""
            current_line.errors += f'{separator}{target.errLog}'
        
        if is_valid and len(target.proofLines) > 0:
            last_line = target.proofLines[-1]
            rule_with_params = last_line.appliedRule or rule or ''
            result_node_id = last_line.resultNodeId
            json_tree = makeJson(last_line.exprTree)
        
        save_equational_obj_to_cache(user, proof_obj, proof_id)
        
        # Save to database
        if proof_id and len(target.proofLines) > 0:
            calculated_line_number = line_number if line_number is not None else (len(target.proofLines) - 1)
            if is_valid:

                # Update previous line's selected_node
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

                error_value = ''
                if calculated_line_number < len(target.proofLines):
                    error_value = target.proofLines[calculated_line_number].errors
                
                # Save the new line
                save_proof_line_to_db(
                    proof_id=proof_id,
                    side=side,
                    racket=racket_str,
                    rule=rule_with_params,
                    start_position=start_position,
                    line_number=calculated_line_number,
                    substitution=substitution or '',
                    selected_node=start_position,
                    result_node=result_node_id,
                    errors=error_value
                )
            else:
                line_index = calculated_line_number - 1
                last_line_obj = target.proofLines[line_index]
                EquationalProofLine.objects.filter(
                    proof_id=proof_id,
                    side=side.upper(),
                    line_number=line_index
                ).update(errors=last_line_obj.errors)
        
        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "jsonTree": json_tree,
            "rule": rule_with_params,
            "resultNodeId": result_node_id,
            "errors": target.errLog
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        traceback.print_exc()
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
    user = request.user
    data = request.data
    proof_obj, proof_id = get_or_set_equational_obj(user)
    _ensure_er_hydrated(proof_obj, proof_id)
    
    try:
        side = data.get("side", "LHS")
        rule = data.get("rule")
        if rule and rule.lower() == "math":
            rule = "rewrite math"
        elif rule and rule.lower() == "logic":
            rule = "rewrite logic"
        current_racket = data.get("currentRacket", "")
        start_position = data.get("startPosition", 0)
        selected_node = data.get("selectedNode")
        substitution_expr = data.get("substitution")
        line_number = data.get("lineNumber")
        support_rewrite_complexity = data.get("supportRewriteComplexity", True)
        target = proof_obj.LHS if side == "LHS" else proof_obj.RHS
        target.errLog = []
        proof_obj.isComplete = False
        print(support_rewrite_complexity)
        # Apply substitution
        if substitution_expr is not None and substitution_expr != "":
            target.addProofLine(current_racket, rule, int(start_position or 0), substitution_expr, support_rewrite_complexity=support_rewrite_complexity)
        else:
            target.addProofLine(current_racket, rule, int(start_position or 0))
        
        is_valid = len(target.errLog) == 0
        racket_str = target.getPrevRacket() if is_valid else "Error generating racket"
        json_tree = makeJson(target.proofLines[-1].exprTree) if is_valid and len(target.proofLines) > 0 else {}

        if not is_valid and len(target.proofLines) > 0:
            # append current line errors
            current_line = target.proofLines[line_number - 1]
            separator = ", " if current_line.errors else ""
            current_line.errors += f'{separator}{target.errLog}'

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
        if proof_id and len(target.proofLines) > 0:
            if is_valid:
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
                        selected_node=start_position,
                        result_node=result_node_id
                    )
        else:
            line_index = line_number - 1
            last_line_obj = target.proofLines[line_index]
            EquationalProofLine.objects.filter(
                proof_id=proof_id,
                side=side.upper(),
                line_number=line_index
            ).update(errors=last_line_obj.errors)
        
        return Response({
            "isValid": is_valid,
            "racket": racket_str,
            "jsonTree": json_tree,
            "rule": rule_with_sub,
            "resultNodeId": result_node_id,
            "errors": target.errLog
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        traceback.print_exc()
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
    
    A proof is complete if:
    1. The proof engine says it's complete (LHS = RHS)
    2. There are no hidden fields remaining
    
    Returns: { isComplete: bool, message: str }
    """
    user = request.user
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    try:
        is_student = not user.is_instructor

        # Reload proof lines from database
        reload_proof_lines_from_db(proof_obj, proof_id)
        
        # Check if proof is mathematically complete (LHS = RHS)
        is_mathematically_complete = proof_obj.checkComplete(is_student)
        
        # Check if there are any hidden fields remaining
        has_hidden_fields = False
        if not user.is_instructor and proof_id:
            has_hidden_fields = EquationalProofLine.objects.filter(
                proof_id=proof_id
            ).filter(
                models.Q(hide_expression=True) | models.Q(hide_justification=True)
            ).exists()
        
        # Proof is only complete if mathematically correct AND no hidden fields
        is_complete = is_mathematically_complete and not has_hidden_fields
        
        # Update database
        if proof_id:
            EquationalProof.objects.filter(id=proof_id).update(is_complete=is_complete)

            # update assignment if it exists and is completed for the first time
            if is_complete:
                content_type = ContentType.objects.get(app_label="equational_reasoning_api", model="equationalproof")
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
    """Get all proof lines AND metadata"""
    user = request.user
    _, proof_id = get_or_set_equational_obj(user)
    
    if not proof_id:
        return Response({"hasProof": False}, status=status.HTTP_200_OK)
    
    try:
        proof = get_object_or_404(EquationalProof, id=proof_id)
        if (proof.user != user):
            proof_content_type = ContentType.objects.get_for_model(EquationalProof)
        
            is_authorized_instructor = StudentProofMapping.objects.filter(
                object_id=proof.id,
                content_type=proof_content_type,
                assignment__course__instructor=user
            ).exists()

            if not is_authorized_instructor:
                return Response({"hasProof": False}, status=status.HTTP_403_FORBIDDEN)
        
        # Fetch lines
        lhs_lines = EquationalProofLine.objects.filter(
            proof_id=proof_id, side='LHS'
        ).order_by('line_number')
        
        rhs_lines = EquationalProofLine.objects.filter(
            proof_id=proof_id, side='RHS'
        ).order_by('line_number')
        
        # Convert to camelCase for frontend
        def format_line(line):
            return {
                'lineNumber': line.line_number,  # camelCase!
                'racket': line.racket,
                'rule': line.rule,
                'jsonTree': line.json_tree,
                'selectedNode': line.selected_node,  # camelCase!
                'resultNode': line.result_node,      # camelCase!
                'substitution': line.substitution,
                'startPosition': line.start_position,  # camelCase!
                'hide_expression': line.hide_expression,
                'hide_justification': line.hide_justification,
                'errors': line.errors
            }
        
        definitions_and_generics = proof.definition if proof.definition else []
        definitions_data = []
        generics_data = []
        
        for item in definitions_and_generics:
            if item.get('is_generic'):
                generics_data.append(item)
            else:
                item['applied'] = True
                if 'def_type' in item and 'type' not in item:
                    item['type'] = item.pop('def_type')
                definitions_data.append(item)
        
        proof_user = {}
        proof_user['username'] = proof.user.username
        proof_user['is_student'] = not proof.user.is_instructor

        return Response({
            "hasProof": True,
            "user": proof_user,
            "lhsAnchorGoal": proof.lhs_goal,
            "rhsAnchorGoal": proof.rhs_goal,
            "proofName": proof.name,
            "tag": proof.tag,
            "proof_id": proof.id,
            "support_errors": proof.support_errors,
            "support_current_lhs_rhs": proof.support_current_lhs_rhs,
            "support_ih": proof.support_ih,
            "support_premise": proof.support_premise,
            "support_rule_set": proof.support_rule_set,
            "visible_rules": parse_visible_rules(proof.visible_rules),
            "support_rewrite_complexity": proof.support_rewrite_complexity,
            "support_value_mapping": proof.support_value_mapping,
            "LHS": [format_line(line) for line in lhs_lines],
            "RHS": [format_line(line) for line in rhs_lines],
            "definitions": definitions_data,
            "generics": generics_data
        }, status=status.HTTP_200_OK)
        
    except EquationalProof.DoesNotExist:
        return Response({"hasProof": False}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_visibility(request):
    user = request.user
    
    # 1. Get the session object
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    if not proof_id:
        return Response({"error": "Session expired or invalid proof ID"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reload_proof_lines_from_db(proof_obj, proof_id)

        side = request.data.get('side')
        line_number = request.data.get('lineNumber')
        field = request.data.get('field') 
        
        if not side or line_number is None or field not in ['expression', 'justification']:
            return Response({"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        side = side.upper()
        target_proof = proof_obj.LHS if side == 'LHS' else proof_obj.RHS
        
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
        save_equational_obj_to_cache(user, proof_obj, proof_id)
        
        # Update Database
        try:
            db_line = EquationalProofLine.objects.get(
                proof_id=proof_id, side=side, line_number=line_number
            )
            if field == 'expression':
                db_line.hide_expression = new_val
            else:
                db_line.hide_justification = new_val
            db_line.save()
        except EquationalProofLine.DoesNotExist:
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
    Validates Rule + Selection OR Expression via normalized AST JSON tree comparison.
    """    
    # 1. Validate User Context & Fetch Active Engine
    user = request.user
    proof_obj, proof_id = get_or_set_equational_obj(user)
    
    if not proof_id:
        return Response({"error": "No active proof session found. Please reload."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 2. Extract Data
        side = request.data.get('side')
        line_number = request.data.get('lineNumber')
        student_expression = request.data.get('studentExpression')
        student_rule = request.data.get('studentRule')
        student_selected = request.data.get('studentSelectedNode') 
        
        if not side or line_number is None:
            return Response({"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST)
            
        target = proof_obj.LHS if side.upper() == 'LHS' else proof_obj.RHS
        
        # 3. Get Database Line
        try:
            line = EquationalProofLine.objects.get(
                proof_id=proof_id, side=side.upper(), line_number=line_number
            )
        except EquationalProofLine.DoesNotExist:
            return Response({"error": "Line not found"}, status=status.HTTP_404_NOT_FOUND)
        
        errors = []
        changed = False
        is_correct = False
        
        # 4. Logic: Master Key Validation (Rule + Selection)
        if student_rule is not None:
            rule_text_match = compare_exact(student_rule, line.rule)
            
            selection_match = True
            if line.selected_node is not None and student_selected is not None:
                 if int(student_selected) != int(line.selected_node):
                     selection_match = False
                     errors.append("Incorrect selection.")

            if rule_text_match and selection_match:
                # Correct derivation! Reveal everything hidden on this line.
                if line.hide_justification:
                    line.hide_justification = False
                    changed = True
                if line.hide_expression:
                    line.hide_expression = False
                    changed = True
                is_correct = True
            elif not rule_text_match:
                errors.append("Rule does not match.")
        
        # 5. Logic: Expression Tree Match
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
                        is_correct = True
                    else:
                        errors.append("Expression does not match.")
                else:
                    errors.append("Syntax error in expression.")
            except Exception as e:
                errors.append(f"Error parsing expression: {str(e)}")
        else:
            errors.append("You must provide an expression.")

        if changed:
            line.save()
        
        # Determine success message
        message = "Correct!" if is_correct and not errors else None
        
        return Response({
            "isValid": is_correct,
            "errors": errors,
            "hide_expression": line.hide_expression,
            "hide_justification": line.hide_justification,
            "message": message
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        traceback.print_exc()
        return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_user_proofs(request):
    user = request.user
    page = request.GET.get("page", 1)
    query = request.GET.get("query", "")
    proof_data = user_proofs(user, page, query)

    return Response(proof_data, status=status.HTTP_200_OK)


def user_proofs(user, page=1, query="", proofs_per_page=12):
    proofs = EquationalProof.objects.filter(user=user, name__contains=query, is_active=True).order_by(
        "-created_at"
    )
    paginator = Paginator(proofs, proofs_per_page)

    try:
        paginated_proofs = paginator.page(int(page))
    except PageNotAnInteger:
        paginated_proofs = paginator.page(1)
    except EmptyPage:
        paginated_proofs = paginator.page(paginator.num_pages)

    proof_data = []

    for proof in paginated_proofs:
        proof_lines = EquationalProofLine.objects.filter(proof=proof)
        definitions = proof.definition
        proof_lines_data = []
        definitions_data = []

        for proof_line in proof_lines:
            proof_lines_data.append(
                {
                    "side": proof_line.side,
                    "racket": proof_line.racket,
                    "jsonTree": proof_line.json_tree,
                    "rule": proof_line.rule,
                    "substitution": proof_line.substitution,
                    "startPosition": proof_line.start_position,
                    "selectedNode": proof_line.selected_node,
                    "resultNode": proof_line.result_node,
                    "lineNumber": proof_line.line_number,
                    "hide_expression": proof_line.hide_expression,
                    "hide_justification": proof_line.hide_justification
                }
            )

        for definition in definitions:
            definitions_data.append(
                {
                    "id": definition.get("id"),
                    "label": definition.get("label"),
                    "type": definition.get("def_type"),
                    "expression": definition.get("expression"),
                    "notes": definition.get("notes", ""),
                    "applied": True,
                }
            )

        proof_data.append(
            {
                "id": proof.id,
                "name": proof.name,
                "tag": proof.tag,
                "lhs": proof.lhs_goal,
                "rhs": proof.rhs_goal,
                "isComplete": proof.is_complete,
                "proofLines": proof_lines_data,
                "definitions": definitions_data,
            }
        )

    return {
        "proofs": proof_data,
        "totalPages": paginator.num_pages,
        "currentPage": paginated_proofs.number,
        "hasNext": paginated_proofs.has_next(),
        "hasPrevious": paginated_proofs.has_previous(),
    }


def user_proof(user, proof_id):
    """
    Fetch a single proof from the DB and format it into a dictionary 
    compatible with the load_proof logic and frontend response.
    """
    # 1. Fetch the Proof using the correct field names
    proof = get_object_or_404(EquationalProof, id=proof_id)
    if (proof.user != user):
        proof_content_type = ContentType.objects.get_for_model(EquationalProof)
    
        is_authorized_instructor = StudentProofMapping.objects.filter(
            object_id=proof.id,
            content_type=proof_content_type,
            assignment__course__instructor=user
        ).exists()

        if not is_authorized_instructor:
            return None

    # 2. Fetch Lines ordered by line number
    lines = EquationalProofLine.objects.filter(proof=proof).order_by('line_number')

    proof_lines_data = []
    
    for line in lines:

        proof_lines_data.append({
            "side": line.side, 
            "racket": line.racket,            
            "jsonTree": line.json_tree,
            "rule": line.rule,
            "substitution": line.substitution,
            "startPosition": line.start_position,
            "selectedNode": line.selected_node,
            "resultNode": line.result_node,
            "lineNumber": line.line_number,
            "hide_expression": line.hide_expression,
            "hide_justification": line.hide_justification,
            "errors": line.errors,
            "deleted": False 
        })

    # 3. Fetch Definitions
    # 'definition' is a JSONField in your model, so access it directly.
    definitions_and_generics = proof.definition if proof.definition else []
    
    definitions_data = []
    generics_data = []
    
    for item in definitions_and_generics:
        if item.get('is_generic'):
            generics_data.append(item)
        else:
            item['applied'] = True
            definitions_data.append(item)

    # 5. Construct the Data Object
    proof_data = {
        "id": proof.id,
        "name": proof.name,
        "tag": proof.tag,
        "lhs": proof.lhs_goal,
        "rhs": proof.rhs_goal,
        "isComplete": proof.is_complete,
        "proofLines": proof_lines_data,
        "definitions": definitions_data,
        "generics": generics_data
    }

    return proof_data


def load_proof(proof_data):
    """
    Reconstructs the TwoSidedProof Python object from the data dictionary.
    This "hydrates" the engine so checks and next-steps can run.
    """
    proof = TwoSidedProof()

    # 1. Load Definitions into Engine
    definitions = proof_data.get("definitions", [])
    for definition in definitions:
        label = definition.get("label")
        def_type = definition.get("type")
        expression = definition.get("expression")
        
        if label and def_type and expression:
            proof.LHS.addUDF(label, def_type, expression)
            proof.RHS.addUDF(label, def_type, expression)

    # 2. Load Generics into Engine
    generics = proof_data.get("generics", [])
    for generic in generics:
        restrictions = generic.get("restrictions", {})
        try:
            proof.LHS.addGeneric(generic["label"], generic["type"], restrictions)
            proof.RHS.addGeneric(generic["label"], generic["type"], restrictions)
        except Exception as e:
            print(f"Error loading generic {generic.get('label')}: {e}")

    # 3. Restore Lines into Engine
    # Lines are loaded directly WITHOUT replaying rules. Replaying rules on the
    # already-computed result expression causes IndexError when the saved
    # startPosition (from the source tree) no longer exists in the result tree.
    # Every subsequent operation (apply_rule, check_completion, etc.) calls
    # reload_proof_lines_from_db() before acting, so the engine state is always
    # fresh -- rule replay here would be redundant AND unsafe.
    proof_lines = proof_data["proofLines"]
    sorted_lines = sorted(proof_lines, key=lambda x: x['lineNumber'])

    for line_data in sorted_lines:
        is_lhs = line_data['side'] == "LHS"
        target = proof.LHS if is_lhs else proof.RHS
        racket = line_data.get("racket", "")
        if not racket and line_data.get("rule", "") == "":
            continue  # skip blank trailing UI placeholder lines
        proof_line = ERProofLine(racket, target.debug, target.ruleSet, generics=target.generics)
        if proof_line.errLog == []:
            proof_line.appliedRule = line_data.get("rule", "")
            proof_line.appliedRuleNodeId = line_data.get("selectedNode", 0)
            proof_line.resultNodeId = line_data.get("resultNode", 0)
            proof_line.hide_expression = line_data.get("hide_expression", False)
            proof_line.hide_justification = line_data.get("hide_justification", False)
            proof_line.errors = line_data.get("errors", "")
            target.proofLines.append(proof_line)

    return proof


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_user_proof(request):
    user = request.user
    proof_id = request.data.get('proof_id')
    
    if not proof_id:
        return Response({"error": "Proof ID required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Get raw data from DB
        proof_data = user_proof(user, proof_id)
        if not proof_data:
            return Response({"error": "Proof not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Rebuild the Engine Object (This generates the valid trees in memory)
        proof_obj = load_proof(proof_data)

        # 3. Save to Cache
        save_equational_obj_to_cache(user, proof_obj, proof_id)

        return Response({"success": True, "message": "Proof loaded and DB repaired"}, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": "load_failed", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def clear_user_proofs(user):
    cache.delete(f"equational_obj_{user.username}")

@api_view(["POST"])
def clear_proof(request):
    """Clear the session cache without archiving the proof, so the user can start a new proof
    while the current one remains visible in All Proofs."""
    user = request.user
    clear_user_proofs(user)
    return Response({"message": "Session cleared successfully"}, status=status.HTTP_200_OK)

@api_view(["POST"])
def discard_proof(request):
    """Archive the active proof (set is_active=False) and clear the session cache.
    The proof will no longer appear in All Proofs."""
    user = request.user
    try:
        proof = EquationalProof.objects.filter(user=user, is_active=True).order_by('-created_at').first()
        if proof:
            proof.is_active = False
            proof.save()
        clear_user_proofs(user)
        return Response({"message": "Proof archived successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ========================
# Save/Create Proof Logic
# ========================

def get_or_create_proof(data, user, definitions, generics):
    """
    Finds an existing proof by name/tag to update, or creates a new one.
    Then populates it with lines and definitions.
    """
    # Reject reserved names
    _proof_name = (data.get("name") or "").strip()
    _RESERVED_PROOF_NAMES = {"IH", "length", "append", "reverse"}
    if _proof_name in _RESERVED_PROOF_NAMES:
        from rest_framework.response import Response as _Resp
        from rest_framework import status as _st
        return _Resp(
            {"error": f"'{_proof_name}' is a reserved name and cannot be used as a proof name."},
            status=_st.HTTP_400_BAD_REQUEST
        )
    # 1. Archive any existing active proof (Induction or ER) with the same name
    # Name alone is now sufficient to trigger archiving (cross-table)
    EquationalProof.objects.filter(
        name=data.get("name"),
        user=user,
        is_active=True
    ).update(is_active=False)
    from induction_api.models import InductionProof as _IndProof
    _IndProof.objects.filter(
        name=data.get("name"),
        user=user,
        is_active=True
    ).update(is_active=False)
        
    # 2. Create new proof if not found
    proof_serializer_data = {
        "name": data.get("name"),
        "tag": data.get("tag"),
        "lhs_goal": data.get("lHSGoal"),
        "rhs_goal": data.get("rHSGoal"),
        "user": user.id
    }

    # We manually create the object to avoid complex Serializer context issues with 'user'
    # validation, though Serializer usage is also valid.
    try:
        proof_instance = EquationalProof.objects.create(
            user=user,
            name=proof_serializer_data["name"],
            tag=proof_serializer_data["tag"],
            lhs_goal=proof_serializer_data["lhs_goal"],
            rhs_goal=proof_serializer_data["rhs_goal"]
        )
        add_data_to_proof(data, proof_instance, definitions, generics)
        return proof_instance
    except Exception as e:
        print(f"Error creating proof: {e}")
        return None


def create_proof_line(proof, side, line_number, data, is_premise=False):
    """
    Helper to safely create a single EquationalProofLine from frontend data.
    """
    try:
        # Extract fields, handling frontend vs backend naming differences
        racket = data.get("racket", "")
        rule = data.get("rule", "Premise" if is_premise else "")
        start_position = int(data.get("startPosition", 0) or 0)
        substitution = data.get("substitution", "")
        
        # Optional fields that might not exist in all requests
        selected_node = int(data.get("selectedNode", 0) or 0)
        result_node = int(data.get("resultNode", 0) or 0)
        errors = data.get("errors", "")

        json_tree = data.get("jsonTree", {})

        EquationalProofLine.objects.create(
            proof=proof,
            side=side,
            line_number=line_number,
            racket=racket,
            rule=rule,
            start_position=start_position,
            substitution=substitution,
            selected_node=selected_node,
            result_node=result_node,
            # Defaults
            hide_expression=False,
            hide_justification=False,
            errors=errors,
            json_tree=json_tree 
        )
    except Exception as e:
        print(f"Error saving line {line_number} on {side}: {e}")
        raise e


def add_data_to_proof(json_data, proof, definitions, generics):
    """
    Wipes existing lines for the proof and saves the current state 
    from the request data.
    """
    try:
        # 1. Clear existing proof lines to avoid duplication/ordering issues
        proof.proof_lines.all().delete()
        
        # 2. Save Premises (Line 0)
        left_premise = json_data.get("leftPremise")
        if left_premise:
            create_proof_line(proof, 'LHS', 0, left_premise, is_premise=True)
            
        right_premise = json_data.get("rightPremise")
        if right_premise:
            create_proof_line(proof, 'RHS', 0, right_premise, is_premise=True)

        # 3. Save Body Lines        
        left_lines = json_data.get("leftRacketsAndRules", [])
        for i, line_data in enumerate(left_lines):
            create_proof_line(proof, 'LHS', i + 1, line_data)
            
        right_lines = json_data.get("rightRacketsAndRules", [])
        for i, line_data in enumerate(right_lines):
            create_proof_line(proof, 'RHS', i + 1, line_data)
        
        final_definitions = []
        # 4. Save Definitions
        if definitions:
            final_definitions.extend(definitions)

        for generic in generics:
            g_entry = generic.copy()
            g_entry['is_generic'] = True
            final_definitions.append(g_entry)

        proof.definition = final_definitions

        # 5. Update Completion Status
        proof.is_complete = False # Re-validated on load
        proof.save()

    except Exception as e:
        # If saving fails midway, we might want to cleanup or just let the transaction roll back
        print(f"Error adding data to proof: {str(e)}")
        raise e


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_proof(request):
    """
    Endpoint to save the current proof state to the database.
    """
    try:
        data = request.data
        user = request.user

        definitions = []
        
        # Fallback: check if definitions are in the request data
        if not definitions:
            definitions = data.get("definitions", "")

        generics = data.get("generics", [])

        proof = get_or_create_proof(data, user, definitions, generics)

        if not proof:
            return Response(
                {"message": "Error saving proof"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Proof saved successfully", "proofId": proof.id}, 
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {"message": f"Error saving proof: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
        )
    

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
            updated_count = EquationalProof.objects.filter(id=proof_id, user=user).update(is_active=False)
            
            if updated_count == 0:
                return Response({"error": "Proof not found"}, status=status.HTTP_404_NOT_FOUND)

            # 2. Clear cache if active proof_id is the same as the current cache
            cached = cache.get(f"equational_obj_{user.username}") 
            cache_cleared = False
            if cached:
                cached_proof_id = cached.get('proof_id')   

                if cached_proof_id == proof_id:
                    cache_cleared = True
                    clear_user_proofs(user) 

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
    """Instructor-only: update the 6 support param fields on an EquationalProof."""
    user = request.user
    if not user.is_instructor:
        return Response({"error": "Instructor access required"}, status=status.HTTP_403_FORBIDDEN)
    proof_id = request.data.get('proof_id')
    try:
        proof = EquationalProof.objects.get(id=proof_id, user=user)
    except EquationalProof.DoesNotExist:
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
    from induction_api.models import InductionProof as _IndProof
    candidate = base_name
    suffix = 1
    while True:
        er_taken = EquationalProof.objects.filter(user=user, name=candidate, is_active=True).exists()
        ind_taken = _IndProof.objects.filter(user=user, name=candidate, is_active=True).exists()
        if not er_taken and not ind_taken:
            return candidate
        candidate = f"{base_name} (copy)" if suffix == 1 else f"{base_name} (copy {suffix})"
        suffix += 1


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_proof(request):
    """Export the full equational proof as a JSON payload for browser download."""
    user = request.user
    proof_id = request.GET.get('proof_id')
    if not proof_id:
        return Response({"error": "proof_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        proof = EquationalProof.objects.get(id=proof_id, user=user, is_active=True)
    except EquationalProof.DoesNotExist:
        return Response({"error": "Proof not found"}, status=status.HTTP_404_NOT_FOUND)
    lhs_lines = EquationalProofLine.objects.filter(proof=proof, side='LHS').order_by('line_number')
    rhs_lines = EquationalProofLine.objects.filter(proof=proof, side='RHS').order_by('line_number')
    def line_to_dict(line):
        return {
            'lineNumber': line.line_number,
            'racket': line.racket,
            'rule': line.rule,
            'startPosition': line.start_position,
            'selectedNode': line.selected_node,
            'resultNode': line.result_node,
            'substitution': line.substitution,
            'jsonTree': line.json_tree,
        }
    data = {
        'proofType': 'equational',
        'name': proof.name or '',
        'tag': proof.tag or '',
        'lhsGoal': proof.lhs_goal,
        'rhsGoal': proof.rhs_goal,
        'definition': proof.definition if proof.definition is not None else [],
        'support_errors': proof.support_errors,
        'support_current_lhs_rhs': proof.support_current_lhs_rhs,
        'support_ih': proof.support_ih,
        'support_premise': proof.support_premise,
        'support_rule_set': proof.support_rule_set,
        "visible_rules": parse_visible_rules(proof.visible_rules),
        'support_value_mapping': proof.support_value_mapping,
        'support_rewrite_complexity': proof.support_rewrite_complexity,
        'lines': {
            'LHS': [line_to_dict(l) for l in lhs_lines],
            'RHS': [line_to_dict(l) for l in rhs_lines],
        },
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_proof(request):
    """Import an equational proof from a JSON payload and create a new proof record."""
    user = request.user
    data = request.data
    if data.get('proofType') != 'equational':
        return Response({"error": "This file is not an equational reasoning proof."}, status=status.HTTP_400_BAD_REQUEST)
    base_name = (data.get('name') or 'Untitled').strip() or 'Untitled'
    name = _unique_proof_name(user, base_name)
    try:
        proof = EquationalProof.objects.create(
            user=user,
            name=name,
            tag=data.get('tag') or '',
            lhs_goal=data.get('lhsGoal', ''),
            rhs_goal=data.get('rhsGoal', ''),
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
        for side in ('LHS', 'RHS'):
            for line in lines_data.get(side, []):
                EquationalProofLine.objects.create(
                    proof=proof,
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
    

@api_view(["POST"])
def save_comment(request):

    try:
        user = request.user
        _, proof_id = get_or_set_equational_obj(user)

        data = request.data

        side = data.get("side")
        line_number = data.get("line_number")
        role = data.get("role")
        comment_text = data.get("comment")

        comment_obj, created = EquationalProofLineComment.objects.update_or_create(
            proof_id=proof_id,
            side=side,
            line_number=line_number,
            role=role,
            defaults={
                "comment": comment_text
            }
        )

        return Response({
            "success": True
        }, status=status.HTTP_200_OK)

    except Exception as e:

        print("SAVE COMMENT ERROR:", e)

        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    

@api_view(["GET"])
def get_comments(request):

    try:
        user = request.user
        _, proof_id = get_or_set_equational_obj(user)

        side = request.GET.get("side")
        line_number = request.GET.get("line_number")

        comments = EquationalProofLineComment.objects.filter(
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