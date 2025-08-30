from flask import Flask, request, jsonify
import razorpay
import hmac, hashlib

app = Flask(__name__)

# ⚡ Replace with your LIVE keys when you go live!
RAZORPAY_KEY_ID = "rzp_test_RBTHxrPSu8kBlk"
RAZORPAY_KEY_SECRET = "ST1hNgnV1lyzucZQJ6IPnmRQ"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Simple in-memory balance store (replace with DB for production)
balances = {}

@app.route("/balance")
def balance():
    user = request.args.get("user")
    return jsonify({"balance": balances.get(user, 0)})

@app.route("/create_order", methods=["POST"])
def create_order():
    data = request.json
    amount = int(data["amount"])
    user = data["user"]

    order = client.order.create({
        "amount": amount * 100,  # in paise
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify({
        "order_id": order["id"],
        "amount": order["amount"],
        "key_id": RAZORPAY_KEY_ID
    })

@app.route("/verify_payment", methods=["POST"])
def verify_payment():
    data = request.json
    order_id = data["razorpay_order_id"]
    payment_id = data["razorpay_payment_id"]
    signature = data["razorpay_signature"]
    user = data["user"]
    amount = int(data["amount"])

    # Generate server-side signature
    generated = hmac.new(
        bytes(RAZORPAY_KEY_SECRET, "utf-8"),
        bytes(order_id + "|" + payment_id, "utf-8"),
        hashlib.sha256
    ).hexdigest()

    if generated == signature:
        balances[user] = balances.get(user, 0) + amount
        return jsonify({"success": True, "balance": balances[user]})
    return jsonify({"success": False, "error": "Signature mismatch"})

@app.route("/withdraw", methods=["POST"])
def withdraw():
    data = request.json
    user = data["user"]
    amount = int(data["amount"])
    dest = data["dest"]

    if balances.get(user, 0) < amount:
        return jsonify({"success": False, "error": "Insufficient balance"})

    balances[user] -= amount
    return jsonify({"success": True, "message": f"Payout of ₹{amount} to {dest} will be processed manually."})

if __name__ == "__main__":
    app.run(debug=True)
