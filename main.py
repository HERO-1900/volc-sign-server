from fastapi import FastAPI, Request
import requests

app = FastAPI()

@app.post("/sign-and-forward")
async def sign_and_forward(req: Request):
    body = await req.body()
    
    # TODO: 在这里调用你自建的签名逻辑函数，生成签名头 headers
    # 示例 headers 结构如下（你需要根据火山签名算法生成）：
    headers = {
        "Content-Type": "application/json",
        "Authorization": "HMAC-SHA256 Credential=xxx/xxx/xxx/xxx, SignedHeaders=..., Signature=...",
        "X-Date": "20250417T123456Z",
        "X-Content-Sha256": "xxxxxxxxxxxxxxxxxxxxxx"
    }

    volc_url = "https://visual.volcengineapi.com/?Action=CVProcess&Version=2022-08-31"
    response = requests.post(volc_url, data=body, headers=headers)

    return {
        "status_code": response.status_code,
        "response": response.json()
    }
