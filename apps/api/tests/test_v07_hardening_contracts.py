from app.hardening_services import lexical_score, _chunks, encrypt_secret, decrypt_secret
from app.hardening_schemas import ConsentUpsert, ProviderCredentialCreate


def test_lexical_retrieval_prefers_matching_text() -> None:
    query = "قیمت سرویس طراحی سایت"
    assert lexical_score(query, "قیمت سرویس طراحی سایت از پایه محاسبه می‌شود") > lexical_score(query, "ساعات کاری شرکت شنبه تا سه شنبه است")


def test_chunking_keeps_long_text_retrievable() -> None:
    text = "الف " * 2000
    chunks = _chunks(text, size=300, overlap=40)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_provider_secret_is_encrypted_at_rest() -> None:
    secret = "super-secret-provider-token"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert secret not in encrypted
    assert decrypt_secret(encrypted) == secret


def test_marketing_consent_contract_is_explicit() -> None:
    payload = ConsentUpsert(purpose="marketing", channel="telegram", status="granted", evidence="user opted in")
    assert payload.status == "granted"
    assert payload.purpose == "marketing"


def test_provider_credential_contract_never_returns_secret_field() -> None:
    payload = ProviderCredentialCreate(provider="telegram", credential_name="primary", secret="12345678-token")
    assert payload.secret
