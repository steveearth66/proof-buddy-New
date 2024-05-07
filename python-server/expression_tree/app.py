from flask import Flask, jsonify, request
from flask_cors import CORS
from ERProofEngine import ERProof
import copy
proofOne = ERProof()
proofTwo = ERProof()
currentProof = proofOne

isValid = True
pOneIsActive = True

# Instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JSON_SORT_KEYS'] = False

# Enable Cors
CORS(app, resources={r'/*': {'origins': '*'}})

# Racket Rule Subsitution and Evaluation
@app.route('/api/v1/proof/er-generate', methods=['GET'])
def get_er_proof_data():
    return jsonify({'name': 'test'})

@app.route('/api/v1/proof/er-definitions', methods=['POST'])
def add_definitions():
    global proofOne
    global proofTwo
    global currentProof
    global isValid

    json_data = request.get_json()

    if json_data['label'] not in proofOne.ruleSet.keys():
        proofOne.addUDF(json_data['label'],
                        json_data['type'], json_data['expression'])
    if proofTwo != None:
        if json_data['label'] not in proofTwo.ruleSet.keys():
            proofTwo.addUDF(
                json_data['label'], json_data['type'], json_data['expression'])

    updateCurrentProof()
    updateIsValid()
    #print(currentProof.errLog)
    #print(currentProof.ruleSet)
    prevErrors = getErrorsAndClear()
    return jsonify({'isValid': isValid, 'errors': prevErrors}), 200

@app.route('/api/v1/proof/er-generate', methods=['POST'])
def apply_rule():
    global isValid
    global proofOne
    global proofTwo
    global pOneIsActive
    global currentProof

    with app.app_context():
        json_data = request.get_json()
        if pOneIsActive:
            if proofOne.getPrevRacket() != json_data['currentRacket']:
                pOneIsActive = False
                proofTwo.addProofLine(
                    json_data['currentRacket'], json_data['rule'], json_data['startPosition'])
            else:
                proofOne.addProofLine(
                    json_data['currentRacket'], json_data['rule'], json_data['startPosition'])
        elif proofTwo.getPrevRacket() != json_data['currentRacket']:
            pOneIsActive = True
            proofOne.addProofLine(
                json_data['currentRacket'], json_data['rule'], json_data['startPosition'])
        else:
            proofTwo.addProofLine(
                json_data['currentRacket'], json_data['rule'], json_data['startPosition'])

        # print(f"tree={currentProof.exprTree} errs={currentProof.errLog}")

        updateCurrentProof()
        updateIsValid()

        racketStr = currentProof.getPrevRacket() if isValid else "Error generating racket"

        prevErrors = getErrorsAndClear()
        return jsonify({'isValid': isValid, 'racket': racketStr, 'errors': prevErrors}), 200

# Proof Goal Checking
@app.route('/api/v1/proof/check-goal', methods=['POST'])
def check_goal():
    global isValid
    global proofOne
    global proofTwo
    global pOneIsActive
    global currentProof

    with app.app_context():
        json_data = request.get_json()

        if currentProof.proofLines == []:
            currentProof.addProofLine(json_data['goal'])
        else:
            pOneIsActive = not pOneIsActive
            updateCurrentProof()
            currentProof.addProofLine(json_data['goal'])

        updateIsValid()

        prevErrors = getErrorsAndClear()
        return jsonify({'isValid': isValid, 'errors': prevErrors}), 200

def updateCurrentProof():
    global proofOne
    global proofTwo
    global pOneIsActive
    global currentProof

    currentProof = proofOne if pOneIsActive else proofTwo

def getErrorsAndClear():
    global currentProof

    errors = copy.copy(currentProof.errLog)
    currentProof.errLog = []

    return errors
# Helper function to update the global isValid variable
def updateIsValid():
    global isValid
    global currentProof

    isValid = currentProof.errLog == []

if __name__ == '__main__':
    app.run(host='localhost', port=9095, debug=True)
