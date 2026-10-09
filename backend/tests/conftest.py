import pytest
import fakeredis
from backend.app import create_app
from backend.config import TestConfig
from backend.extensions import db
import backend.extensions as extensions
from backend.services.email_service import EmailService

@pytest.fixture
def fake_redis_client():
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server, decode_responses=True)
    return client

@pytest.fixture
def app(fake_redis_client, monkeypatch):
    test_app = create_app(TestConfig)
    
    # Inject fake redis client into extensions
    monkeypatch.setattr(extensions, "redis_client", fake_redis_client)
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return test_app_client(app)

def test_app_client(app):
    return app.test_client()

@pytest.fixture
def mock_smtp(monkeypatch):
    sent_emails = []
    
    def fake_send(to_email, name, otp, expiry_minutes=5):
        sent_emails.append({
            "to_email": to_email,
            "name": name,
            "otp": otp,
            "expiry_minutes": expiry_minutes
        })
        return True

    monkeypatch.setattr(EmailService, "send_otp_email", fake_send)
    return sent_emails
