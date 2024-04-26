from flask import Flask, jsonify, request
from flask_cors import CORS
from ERProofEngine import ERProof

currentProof = None
isValid = True

#Instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JSON_SORT_KEYS'] = False

#Enable Cors
CORS(app, resources={r'/*': {'origins': '*'}})

# Racket Rule Subsitution and Evaluation
@app.route('/api/v1/proof/er-generate', methods=['POST'])
def apply_rule():
    global isValid
    global currentProof

    with app.app_context():
        json_data = request.get_json()
        currentProof = ERProof(json_data['currentRacket'])
        currentProof.applyRule(json_data['startPosition'], json_data['rule'])
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
        currentProof = ERProof(json_data['goal'])
        updateIsValid()
            
        return jsonify({'isValid': isValid, 'errors': currentProof.errLog }), 200

# Helper function to update the global isValid variable
def updateIsValid():
    global isValid
    global currentProof
    isValid = currentProof.errLog == []

if __name__ == '__main__':
    app.run(host='localhost', port=9095, debug=True)
