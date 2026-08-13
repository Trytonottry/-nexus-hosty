import json
from datetime import datetime,timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Subscription
from .xui import XUIClient,choose_node,extract_links,extract_obj
from .config import settings

async def provision_subscription(db:AsyncSession,sub:Subscription):
    if not settings.xui_provision_enabled: return
    node=choose_node(); client=XUIClient(node)
    email=sub.xui_email or f"u{sub.user_id}-s{sub.id}@nexus"
    sub_id=sub.xui_sub_id or f"nexus-{sub.id}"
    # inbound_ids are configured per node; this deliberately keeps node topology out of the public API.
    inbound_ids=node.get("inbound_ids",[])
    if not inbound_ids: raise RuntimeError(f"У ноды {node.get('name')} нет inbound_ids")
    expiry_ms=int(sub.expires_at.timestamp()*1000)
    total_bytes=0 if sub.traffic_limit_gb is None else int(sub.traffic_limit_gb*1024**3)
    existing=None
    try: existing=extract_obj(await client.get_client(email))
    except Exception: pass
    if not existing:
        await client.add_client(email,expiry_ms,total_bytes,inbound_ids,sub_id)
    else:
        # Update requires full client payload. Reuse returned client object where possible.
        c=existing.get("client") if isinstance(existing,dict) else existing
        if isinstance(c,dict):
            c.update({"email":email,"enable":True,"expiryTime":expiry_ms,"totalGB":total_bytes,"subId":sub_id})
            await client.update_client(email,c)
    links=extract_links(await client.links(email))
    sub.xui_node=node.get("name") or node["base_url"]
    sub.xui_email=email;sub.xui_sub_id=sub_id
    sub.vpn_links_json=json.dumps(links,ensure_ascii=False)
    sub.vpn_config_url=links[0] if links else None
    await db.commit()
    return links

async def sync_subscription(db:AsyncSession,sub:Subscription):
    if not sub.xui_email or not sub.xui_node: return
    node=next((n for n in __import__('json').loads(settings.xui_nodes_json or '[]') if (n.get('name') or n.get('base_url'))==sub.xui_node),None)
    if not node: return
    c=XUIClient(node)
    up,down,total=__import__('app.xui',fromlist=['extract_traffic']).extract_traffic(await c.traffic(sub.xui_email))
    sub.traffic_used_mb=total//(1024*1024)
    await db.commit()
