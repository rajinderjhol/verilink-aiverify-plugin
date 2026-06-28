import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/v1/auth/token")
async def get_token():
    return {"trust_token": "mock-jit-token-xyz-123"}

@app.post("/v1/governance/verify-aibom")
async def verify_aibom():
    return {"valid": True, "model_status": "verified"}

@app.post("/v1/analytics/predict")
async def predict():
    return {"failure_probability": 0.05, "risk_level": "low"}

@app.post("/v1/governance/receipt")
async def generate_receipt():
    return {
        "receipt_id": "rcpt-mock-uuid-12345",
        "merkle_root": "0x7d5a0975a6c112a20dc6f57849e79822955f2d9f78f696085a73e6e06b9b378a",
        "timestamp": 1687890000.0
    }

@app.get("/v1/governance/receipt/{receipt_id}/verify")
async def verify_receipt(receipt_id: str):
    return {"verified": True, "status": "valid"}

if __name__ == "__main__":
    print("🛠️ Starting VeriLinkOS Mock Server on http://127.0.0.1:8000")
    print("Use this to test your plugin without a live internet connection.")
    uvicorn.run(app, host="127.0.0.1", port=8000)