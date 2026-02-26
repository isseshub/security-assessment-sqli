from pprint import pformat
from flask import Flask, request, jsonify, render_template
import requests, time

app = Flask(__name__)
app.jinja_env.filters["pprint"] = pformat

UC_URL = "http://127.0.0.1:5001/risk-score"

def log(event):
    with open("security.log", "a") as f:
        f.write(f"{int(time.time())} {event}\n")

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

def to_int(x, default=0):
    try:
        return int(str(x).strip())
    except Exception:
        return default

@app.route("/")
def home():
    return render_template("index.html", result=None)

@app.route("/apply")
def apply():
    applicant_id = request.args.get("applicant_id", "")
    income = request.args.get("income_monthly", "")
    debt = request.args.get("existing_debt", "")

    income_i = to_int(income, 0)
    debt_i = to_int(debt, 0)

    # 1) Hämta UC-data
    try:
        resp = requests.get(UC_URL, params={"applicant_id": applicant_id}, timeout=2)
        resp.raise_for_status()
        uc_data = resp.json()
    except Exception as e:
        log(f"UC failure: {e}")
        result = build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "UC_TIMEOUT",
            "Din ansökan kräver manuell granskning.",
            "UC did not respond / failed within 2s. Policy: REVIEW on vendor failure.",
            None
        )
        return render_template("index.html", result=result)

    # 2) Validera UC-response
    score = uc_data.get("risk_score")
    if score is None:
        log(f"UC malformed: {uc_data}")
        result = build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "UC_MALFORMED",
            "Din ansökan kräver manuell granskning.",
            "UC response missing risk_score. Policy: REVIEW on malformed vendor data.",
            uc_data
        )
        return render_template("index.html", result=result)

    # 3) Policy (UC high risk)
    if score > 70:
        result = build_result(
            "DEFENSE", applicant_id, income, debt,
            "DENIED",
            "UC_HIGH_RISK",
            "Ansökan kan inte beviljas baserat på riskbedömningen.",
            f"UC risk_score={score} > 70. Policy: DENY on high risk.",
            uc_data
        )
        return render_template("index.html", result=result)

    # 4) Suspicious low score -> REVIEW
    if score < 10:
        log(f"Suspicious low UC score: {uc_data}")
        result = build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "UC_SUSPICIOUS_LOW",
            "Din ansökan kräver manuell granskning.",
            f"UC risk_score={score} is suspiciously low. Policy: REVIEW to prevent blind trust / manipulation.",
            uc_data
        )
        return render_template("index.html", result=result)

    # 5) Minimal plausibility check (one-liner wow-effekt)
    # Om skulder är höga och inkomst låg -> REVIEW även om UC är OK
    if debt_i > 200000 and income_i < 25000:
        log(f"Inconsistent data: income={income_i}, debt={debt_i}, uc={uc_data}")
        result = build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "INCONSISTENT_DATA",
            "Din ansökan kräver manuell granskning.",
            f"Internal plausibility check triggered: income={income_i} < 25000 AND debt={debt_i} > 200000.",
            uc_data
        )
        return render_template("index.html", result=result)

    # OK
    result = build_result(
        "DEFENSE", applicant_id, income, debt,
        "APPROVED",
        "OK",
        "Ansökan kan beviljas.",
        f"UC risk_score={score} within acceptable range and no internal red flags.",
        uc_data
    )
    return render_template("index.html", result=result)

@app.route("/loan")
def loan():
    applicant_id = request.args.get("applicant_id", "")
    income = request.args.get("income_monthly", "")
    debt = request.args.get("existing_debt", "")

    income_i = to_int(income, 0)
    debt_i = to_int(debt, 0)

    try:
        resp = requests.get(UC_URL, params={"applicant_id": applicant_id}, timeout=2)
        resp.raise_for_status()
        uc_data = resp.json()
    except Exception as e:
        log(f"UC failure: {e}")
        return jsonify(build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "UC_TIMEOUT",
            "Din ansökan kräver manuell granskning.",
            "UC did not respond / failed within 2s. Policy: REVIEW on vendor failure.",
            None
        )), 502

    score = uc_data.get("risk_score")
    if score is None:
        return jsonify(build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "UC_MALFORMED",
            "Din ansökan kräver manuell granskning.",
            "UC response missing risk_score.",
            uc_data
        )), 200

    if score > 70:
        return jsonify(build_result(
            "DEFENSE", applicant_id, income, debt,
            "DENIED",
            "UC_HIGH_RISK",
            "Ansökan kan inte beviljas baserat på riskbedömningen.",
            f"UC risk_score={score} > 70.",
            uc_data
        )), 200

    if score < 10:
        return jsonify(build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "UC_SUSPICIOUS_LOW",
            "Din ansökan kräver manuell granskning.",
            f"UC risk_score={score} is suspiciously low.",
            uc_data
        )), 200

    if debt_i > 200000 and income_i < 25000:
        return jsonify(build_result(
            "DEFENSE", applicant_id, income, debt,
            "REVIEW",
            "INCONSISTENT_DATA",
            "Din ansökan kräver manuell granskning.",
            f"Internal plausibility check: income={income_i} < 25000 AND debt={debt_i} > 200000.",
            uc_data
        )), 200

    return jsonify(build_result(
        "DEFENSE", applicant_id, income, debt,
        "APPROVED",
        "OK",
        "Ansökan kan beviljas.",
        f"UC score OK and no internal red flags.",
        uc_data
    )), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5003)
