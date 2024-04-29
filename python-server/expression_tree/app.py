from flask import Flask, jsonify, request
from flask_cors import CORS
from ERProofEngine import ERProof, ERProofLine

currentProof = None
isValid = True

#Instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JSON_SORT_KEYS'] = False

#Enable Cors
CORS(app, resources={r'/*': {'origins': '*'}})

# Racket Rule Subsitution and Evaluation
@app.route('/api/v1/proof/er-generate', methods=['GET'])
def  get_er_proof_data():
    return jsonify({'name': 'test'})

@app.route('/api/v1/proof/er-definitions', methods=['POST'])
def add_definitions():
    print(request.get_json())
    return jsonify(request.get_json())

@app.route('/api/v1/proof/er-generate', methods=['POST'])
def apply_rule():
    global isValid #this should be in larger ProofOjb, not this lineObj
    global currentProof

    with app.app_context():
        json_data = request.get_json()
        currentProof = ERProofLine(json_data['currentRacket'])
        print(str(currentProof.exprTree), json_data['startPosition'])
        currentProof.applyRule(rule=json_data['rule'], startPos=json_data['startPosition'])
        #print(f"tree={currentProof.exprTree} errs={currentProof.errLog}")
        updateIsValid()

        if isValid:
            racketStr = str(currentProof.exprTree)
        else:
            racketStr = "Error generating racket"

        return jsonify({'isValid': isValid, 'racket': racketStr, 'errors': currentProof.errLog }), 200

# Proof Goal Checking
@app.route('/api/v1/proof/check-goal', methods=['POST'])
def check_goal():
    global isValid
    global currentProof

    with app.app_context():
        json_data = request.get_json()
        currentProof = ERProofLine(json_data['goal'])
        updateIsValid()
            
        return jsonify({'isValid': isValid, 'errors': currentProof.errLog }), 200

# Helper function to update the global isValid variable
def updateIsValid():
    global isValid
    global currentProof
    isValid = currentProof.errLog == []

if __name__ == '__main__':
    app.run(host='localhost', port=9095, debug=True)
