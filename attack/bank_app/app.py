from pprint import pformat
from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)
app.jinja_env.filters["pprint"] = pformat

UC_URL = "http://127.0.0.1:5001/risk-score"

def build_result(mode, applicant_id, income, debt, decision, reason_code, reason_user, reason_internal, uc_data=None):
    r = {
        "mode": mode,
        "applicant_id": applicant_id,
        "income_monthly": income,
        "existing_debt": debt,
        "decision": decision,
        "reason_code": reason_code,
        "reason_user": reason_user,
        "reason_internal": reason_internal,
    }
    if uc_data is not None:
        r["uc_data"] = uc_data
    return r

@app.route("/")
def home():
    return render_template("index.html", result=None)

@app.route("/apply")
def apply():
    applicant_id = request.args.get("applicant_id", "")
    income = request.args.get("income_monthly", "")
    debt = request.args.get("existing_debt", "")

    try:
        r = requests.get(UC_URL, params={"applicant_id": applicant_id}, timeout=2)
        r.raise_for_status()
        uc_data = r.json()
    except Exception as e:
        result = build_result(
            "ATTACK", applicant_id, income, debt,
            "ERROR",
            "UC_TIMEOUT",
            "Tekniskt fel vid kreditkontroll. Försök igen senare.",
            f"UC call failed: {e}",
            None
        )
        return render_template("index.html", result=result)

    # ATTACK: blint förtroende (ingen plausibility check på lön/skulder)
    decision = "APPROVED" if uc_data.get("risk_level") == "LOW" else "DENIED"

    result = build_result(
        "ATTACK", applicant_id, income, debt,
        decision,
        "BLIND_TRUST",
        "Din ansökan är behandlad.",
        "No validation. Trusting UC response only.",
        uc_data
    )
    return render_template("index.html", result=result)

@app.route("/loan")
def loan():
    applicant_id = request.args.get("applicant_id", "")
    income = request.args.get("income_monthly", "")
    debt = request.args.get("existing_debt", "")
    uc_data = requests.get(UC_URL, params={"applicant_id": applicant_id}, timeout=2).json()
    decision = "APPROVED" if uc_data.get("risk_level") == "LOW" else "DENIED"
    return jsonify(build_result(
        "ATTACK", applicant_id, income, debt,
        decision,
        "BLIND_TRUST",
        "Din ansökan är behandlad.",
        "No validation. Trusting UC response only.",
        uc_data
    ))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
