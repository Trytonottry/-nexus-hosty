from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "NEXUS VPN"
    app_env: str = "production"
    secret_key: str
    access_token_expire_minutes: int = 1440
    cookie_secure: bool = True
    cors_origins: str = "https://vpn.example.com"
    database_url: str

    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_return_url: str = "https://vpn.example.com/payment/success"
    cryptocloud_api_key: str = ""
    cryptocloud_shop_id: str = ""
    cryptocloud_return_url: str = "https://vpn.example.com/payment/success"
    cryptocloud_fail_url: str = "https://vpn.example.com/payment/fail"

    # JSON array: [{"name":"ru-1","base_url":"https://xui.example.com","api_token":"...","inbound_ids":[1]}]
    xui_nodes_json: str = "[]"
    xui_verify_tls: bool = True
    xui_request_timeout: float = 20.0
    xui_provision_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
