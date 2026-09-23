"""
Unit and integration tests for Voice Commands and FastAPI endpoints.
"""

from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.database import Base, get_db
from app.database.models import Points, Food
from app.voice.commands import VoiceCommandRouter

from sqlalchemy.pool import StaticPool

# Setup isolated test database with StaticPool for multi-threaded TestClient
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_voice_command_router():
    db = TestingSessionLocal()
    # Add starting points and chicken
    db.add(Points(points=100, reason="Initial"))
    today = date.today()
    db.add(Food(name="Chicken", expiry_date=today + timedelta(days=1), status="active"))
    db.commit()

    router = VoiceCommandRouter(db)

    # Test "What expires soon?"
    res1 = router.process("Hey Alina, what expires soon?")
    assert res1["intent"] == "expiring_soon"
    assert "Chicken" in res1["response"]

    # Test "What should I cook today?"
    res2 = router.process("What should I cook today?")
    assert res2["intent"] == "recipe_cook"
    assert "Chicken" in res2["response"]

    # Test "How many points do I have?"
    res3 = router.process("How many points do I have?")
    assert res3["intent"] == "points"
    assert "100" in res3["response"]

    db.close()


def test_api_endpoints():
    # Test health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # Test system status
    res_status = client.get("/api/status")
    assert res_status.status_code == 200
    assert "database" in res_status.json()

    # Test add food via API
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    food_payload = {
        "name": "Milk",
        "quantity": 1.0,
        "unit": "litre",
        "expiry_date": tomorrow,
        "category": "Dairy",
    }
    res_add = client.post("/api/foods", json=food_payload)
    assert res_add.status_code == 201
    food_data = res_add.json()
    assert food_data["name"] == "Milk"
    assert food_data["days_remaining"] == 1
    assert food_data["priority"] == "CRITICAL"

    # Test ask API
    res_ask = client.post("/api/ask", json={"query": "What do we have in the fridge?", "speak_output": False})
    assert res_ask.status_code == 200
    assert res_ask.json()["intent"] == "list_food"


def test_chat_endpoint_recipe_recommendation():
    """
    Dedicated test for chat endpoint:
    Verifies 'What should I cook today?' and 'Cook today.' return HTTP 200,
    valid JSON, successful response with message, and no Internal Server Error.
    """
    # Test "What should I cook today?"
    res = client.post("/api/ask", json={"query": "What should I cook today?", "speak_output": False})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "message" in data
    assert len(data["message"]) > 0
    assert data["intent"] == "recipe_cook"
    assert data["alina_state"] in ("happy", "concerned", "celebration", "idle")

    # Test "Cook today."
    res2 = client.post("/api/ask", json={"query": "Cook today.", "speak_output": False})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is True
    assert "message" in data2
    assert len(data2["message"]) > 0
    assert data2["intent"] == "recipe_cook"
