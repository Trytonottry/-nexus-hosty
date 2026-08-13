# NEXUS VPN — full-stack + 3x-ui provisioning

## End-to-end flow

`landing → register/login → checkout → payment webhook → order paid → subscription → 3x-ui client → VPN links → dashboard`

The backend is intentionally the source of truth for **commercial entitlements**; 3x-ui is the source of truth for **Xray client credentials and actual traffic counters**.

## 3x-ui integration

Current 3x-ui documentation exposes Bearer-token authentication and client endpoints under `/panel/api/clients`. The API can create a client and attach it to one or more inbound IDs; the panel can also return client links and traffic counters. See official docs: https://github.com/MHSanaei/3x-ui/blob/main/docs/content/docs/en/reference/api/clients.mdx and https://github.com/MHSanaei/3x-ui/blob/main/frontend/public/openapi.json

Configure one or more nodes in `.env`:

```env
XUI_PROVISION_ENABLED=true
XUI_VERIFY_TLS=true
XUI_NODES_JSON=[{"name":"ru-1","base_url":"https://xui.example.com","api_token":"SECRET","inbound_ids":[1]},{"name":"de-1","base_url":"https://xui-de.example.com","api_token":"SECRET2","inbound_ids":[2]}]
```

For production, use a real secret manager instead of putting API tokens in a plain `.env` committed to git.

### What happens after payment

1. Webhook marks `Order` as paid.
2. `activate_order()` creates or extends `Subscription`.
3. `provision_subscription()` chooses an XUI node.
4. It creates a client using `/panel/api/clients/add`.
5. 3x-ui generates protocol credentials if omitted.
6. Backend requests `/panel/api/clients/links/{email}` and stores the returned URLs.
7. Dashboard shows the links and expiry.
8. Worker polls `/panel/api/clients/traffic/{email}` every 60 seconds and updates used traffic.
9. Expired local subscriptions become `expired`; 3x-ui also receives `expiryTime` when the client is provisioned.

### Multi-node architecture

The current implementation supports multiple 3x-ui panels through `XUI_NODES_JSON`. The selection policy is intentionally simple: first configured node. This is a safe baseline for the MVP.

For your planned multi-node topology, the next production step is to replace first-node selection with a database-backed node scheduler:

- node capacity / current client count;
- geographic preference;
- health checks;
- failover;
- per-plan node pools;
- automatic migration/reprovisioning.

## Important: config URL vs raw credentials

The dashboard displays protocol links returned by 3x-ui. It does **not** expose the 3x-ui admin API token. If the panel returns a subscription URL, it is stored as `vpn_config_url`; individual protocol links are stored in `vpn_links_json`.

## Production requirements

Before real customers:

- HTTPS everywhere; set `COOKIE_SECURE=true`.
- Configure exact 3x-ui inbound IDs and verify their protocol/transport/REALITY settings.
- Verify the exact CryptoCloud webhook payload/signature for your account and current API version.
- Add Alembic migrations.
- Add Redis-backed rate limiting for auth/checkout/webhooks.
- Add email verification and password reset.
- Add CSRF strategy if frontend/API origins become separate.
- Add payment reconciliation jobs (do not trust browser redirects).
- Add a provisioning retry/dead-letter mechanism.
- Add audit logs for subscription and provisioning state changes.
- Back up PostgreSQL.

## Run

```bash
cp .env.example .env
openssl rand -hex 32
# put it into SECRET_KEY

docker compose up -d --build
```

`/` — landing
`/dashboard.html` — account
`/api/health` — healthcheck
