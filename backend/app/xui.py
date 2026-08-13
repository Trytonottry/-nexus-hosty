import json,uuid
from datetime import datetime,timezone
import httpx
from .config import settings
class XUIError(RuntimeError): pass

def nodes(): return json.loads(settings.xui_nodes_json or "[]")
class XUIClient:
    def __init__(self,node): self.node=node
    async def request(self,method,path,**kwargs):
        url=self.node["base_url"].rstrip("/")+path
        headers=kwargs.pop("headers",{});headers["Authorization"]=f"Bearer {self.node['api_token']}"
        async with httpx.AsyncClient(timeout=settings.xui_request_timeout,verify=settings.xui_verify_tls) as c:
            r=await c.request(method,url,headers=headers,**kwargs)
            if r.status_code>=400: raise XUIError(f"3x-ui {r.status_code}: {r.text[:500]}")
            d=r.json()
            if d.get("success") is False: raise XUIError(str(d.get("msg") or d))
            return d
    async def add_client(self,email,expiry_ms,total_bytes,inbound_ids,sub_id):
        # Current 3x-ui API accepts a client plus inboundIds; secrets are generated server-side.
        body={"client":{"email":email,"enable":True,"expiryTime":expiry_ms,"totalGB":total_bytes,"subId":sub_id,"comment":"NEXUS VPN"},"inboundIds":inbound_ids}
        return await self.request("POST","/panel/api/clients/add",json=body)
    async def get_client(self,email): return await self.request("GET",f"/panel/api/clients/get/{email}")
    async def links(self,email): return await self.request("GET",f"/panel/api/clients/links/{email}")
    async def traffic(self,email): return await self.request("GET",f"/panel/api/clients/traffic/{email}")
    async def update_client(self,email,client): return await self.request("POST",f"/panel/api/clients/update/{email}",json=client)

def choose_node():
    ns=nodes()
    if not ns: raise XUIError("XUI_NODES_JSON не настроен")
    return ns[0]

def extract_obj(d): return d.get("obj") or d.get("data") or d.get("result") or d

def extract_links(d):
    x=extract_obj(d)
    if isinstance(x,dict):
        for k in ("links","urls","obj"): 
            if isinstance(x.get(k),list): return x[k]
        if isinstance(x.get("url"),str): return [x["url"]]
    if isinstance(x,list): return x
    return []

def extract_traffic(d):
    x=extract_obj(d)
    if isinstance(x,dict):
        up=int(x.get("up",0) or 0);down=int(x.get("down",0) or 0);total=int(x.get("total",up+down) or up+down)
        return up,down,total
    return 0,0,0
