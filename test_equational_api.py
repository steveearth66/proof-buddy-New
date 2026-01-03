"""
Manual API Testing Script for Equational Reasoning Backend
Tests all 6 endpoints to verify they work correctly before frontend implementation.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/equational"

# You'll need to get a valid auth token first
# For now, we'll test without auth to see what happens
HEADERS = {
    "Content-Type": "application/json",
}

def print_response(test_name, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response Text: {response.text}")
    print(f"{'='*60}\n")

def test_set_current_proof():
    """Test 1: Initialize a new equational proof"""
    url = f"{BASE_URL}/set-current-proof"
    payload = {
        "lhsPremise": "(+ 1 2)",
        "rhsPremise": "3",
        "definitions": []
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    print_response("SET CURRENT PROOF", response)
    return response

def test_apply_rule():
    """Test 2: Apply a rule to generate next line"""
    url = f"{BASE_URL}/apply-rule"
    payload = {
        "side": "LHS",
        "currentRacket": "(+ 1 2)",
        "rule": "arithmetic",
        "startPosition": 0,
        "selectedNode": 0,
        "lineNumber": 0
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    print_response("APPLY RULE", response)
    return response

def test_substitution():
    """Test 3: Apply substitution with eval rule"""
    url = f"{BASE_URL}/substitution"
    payload = {
        "side": "LHS",
        "currentRacket": "(if #t (+ 1 2) 5)",
        "rule": "eval if",
        "substitution": "",
        "startPosition": 0,
        "selectedNode": 0,
        "lineNumber": 0
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    print_response("SUBSTITUTION", response)
    return response

def test_get_proof_lines():
    """Test 4: Get all proof lines"""
    url = f"{BASE_URL}/get-proof-lines"
    response = requests.get(url, headers=HEADERS)
    print_response("GET PROOF LINES", response)
    return response

def test_check_completion():
    """Test 5: Check if proof is complete"""
    url = f"{BASE_URL}/check-completion"
    response = requests.post(url, headers=HEADERS)
    print_response("CHECK COMPLETION", response)
    return response

def test_delete_line():
    """Test 6: Delete/clear a proof line"""
    url = f"{BASE_URL}/delete-line/LHS/1"
    response = requests.delete(url, headers=HEADERS)
    print_response("DELETE LINE", response)
    return response

def run_all_tests():
    """Run all API tests in sequence"""
    print("\n" + "="*60)
    print("EQUATIONAL REASONING API - MANUAL TESTING")
    print("="*60)
    
    # Test 1: Initialize proof
    test_set_current_proof()
    
    # Test 2: Apply a rule
    test_apply_rule()
    
    # Test 3: Test substitution with eval if (the bug we fixed!)
    test_substitution()
    
    # Test 4: Get proof lines
    test_get_proof_lines()
    
    # Test 5: Check completion
    test_check_completion()
    
    # Test 6: Delete a line
    test_delete_line()
    
    # Test 4 again: Verify line was cleared
    test_get_proof_lines()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nNOTE: If you see 401/403 errors, you need authentication.")
    print("Check if the endpoints require login and add token to HEADERS.")

if __name__ == "__main__":
    run_all_tests()
