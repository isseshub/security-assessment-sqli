from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/risk-score")
def risk_score():
    applicant_id = (request.args.get("applicant_id", "") or "").strip()

    # Manipulerad / misstänkt identitet -> "för bra" score
    if applicant_id.lower() == "attacker":
        return jsonify(applicant_id=applicant_id, risk_score=5, risk_level="LOW")

    # En "normal" kund ska inte ligga på 80 som default
    # Returnera en medelrisk som ofta blir APPROVED i både attack/defense
    return jsonify(applicant_id=applicant_id, risk_score=30, risk_level="LOW")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
