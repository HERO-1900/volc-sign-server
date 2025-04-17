from fastapi import FastAPI
from pydantic import BaseModel
import requests, hashlib, hmac, datetime
import json

app = FastAPI()

# 替换成你自己的 AccessKey 和 SecretKey
import os

access_key = os.environ.get("VOLC_ACCESS_KEY")
secret_key = os.environ.get("VOLC_SECRET_KEY")


# 定义 logo_info 的结构
class LogoInfo(BaseModel):
    add_logo: bool
    position: int
    language: int
    opacity: float
    logo_text_content: str

# 定义整个请求体结构（FastAPI 会在接口文档自动显示）
class CVRequest(BaseModel):
    req_key: str
    prompt: str
    seed: int
    scale: float
    width: int
    height: int
    return_url: bool
    logo_info: LogoInfo

# 签名辅助函数
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(key.encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    return sign(k_service, "request")

# 核心签名逻辑
def generate_signed_headers(body_str: str):
    method = "POST"
    service = "cv"
    host = "visual.volcengineapi.com"
    region = "cn-north-1"
    endpoint = "https://visual.volcengineapi.com"
    canonical_uri = "/"
    canonical_querystring = "Action=CVProcess&Version=2022-08-31"
    content_type = "application/json"

    t = datetime.datetime.utcnow()
    current_date = t.strftime("%Y%m%dT%H%M%SZ")
    datestamp = t.strftime("%Y%m%d")

    payload_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()
    canonical_headers = (
        f"content-type:{content_type}\nhost:{host}\n"
        f"x-content-sha256:{payload_hash}\nx-date:{current_date}\n"
    )
    signed_headers = "content-type;host;x-content-sha256;x-date"
    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )
    credential_scope = f"{datestamp}/{region}/{service}/request"
    string_to_sign = (
        f"HMAC-SHA256\n{current_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )
    signing_key = get_signature_key(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "Content-Type": content_type,
        "Host": host,
        "X-Date": current_date,
        "X-Content-Sha256": payload_hash,
        "Authorization": authorization,
    }

from fastapi.responses import JSONResponse
import traceback

@app.post("/sign-and-forward")
async def sign_and_forward(payload: CVRequest):
    try:
        body_dict = payload.dict()
        body_str = json.dumps(body_dict)

        headers = generate_signed_headers(body_str)
        url = "https://visual.volcengineapi.com/?Action=CVProcess&Version=2022-08-31"

        response = requests.post(url, data=body_str, headers=headers)

        return {
            "status_code": response.status_code,
            "response": response.json(),
        }

    except Exception as e:
        # 将错误打印到 Render 的日志控制台
        print("❌ Exception occurred in /sign-and-forward:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

