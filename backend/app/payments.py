import uuid,httpx
from .config import settings
async def create_yookassa_payment(amount,description,order_id):
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key: raise RuntimeError("ЮKassa не настроена")
    payload={"amount":{"value":f"{amount:.2f}","currency":"RUB"},"capture":True,"description":description[:128],"metadata":{"order_id":order_id},"confirmation":{"type":"redirect","return_url":settings.yookassa_return_url}}
    async with httpx.AsyncClient(timeout=settings.xui_request_timeout) as c:
        r=await c.post("https://api.yookassa.ru/v3/payments",auth=(settings.yookassa_shop_id,settings.yookassa_secret_key),headers={"Idempotence-Key":str(uuid.uuid4())},json=payload);r.raise_for_status();d=r.json()
    return d["id"],d["confirmation"]["confirmation_url"]
async def create_cryptocloud_invoice(amount,order_id,email):
    if not settings.cryptocloud_api_key or not settings.cryptocloud_shop_id: raise RuntimeError("CryptoCloud не настроен")
    payload={"shop_id":settings.cryptocloud_shop_id,"amount":amount,"currency":"RUB","order_id":order_id,"email":email,"success_url":settings.cryptocloud_return_url,"fail_url":settings.cryptocloud_fail_url}
    async with httpx.AsyncClient(timeout=settings.xui_request_timeout) as c:
        r=await c.post("https://api.cryptocloud.plus/v2/invoice/create",headers={"Authorization":f"Token {settings.cryptocloud_api_key}"},json=payload);r.raise_for_status();d=r.json()
    x=d.get("result") or d.get("data") or d
    return str(x.get("uuid") or x.get("invoice_id") or order_id),x.get("link") or x.get("pay_url") or x.get("url")
