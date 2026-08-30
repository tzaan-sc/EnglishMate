import pytest
from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import FlashcardSet, FlashcardItem, GameSession
from tests.conftest import login

@pytest.fixture
def games_setup(app):
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        fset = FlashcardSet.query.filter_by(user_id=user.id).first()
        if not fset:
            fset = FlashcardSet(title="Bộ từ game test", user_id=user.id)
            db.session.add(fset)
            db.session.flush()
            
            items = [
                FlashcardItem(set_id=fset.id, term="Apple", definition="Quả táo"),
                FlashcardItem(set_id=fset.id, term="Banana", definition="Quả chuối"),
                FlashcardItem(set_id=fset.id, term="Orange", definition="Quả cam"),
                FlashcardItem(set_id=fset.id, term="Grape", definition="Quả nho"),
                FlashcardItem(set_id=fset.id, term="Mango", definition="Quả xoài"),
            ]
            db.session.add_all(items)
            db.session.commit()
        return fset.id

def test_game_lobby_loads(client):
    login(client)
    response = client.get("/games")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Ghép từ vựng" in html
    assert "Quiz tốc độ" in html
    assert "Sắp xếp từ" in html
    assert "Hangman" in html
    assert "Ô chữ Crossword" in html
    assert "Nhớ thẻ bài" in html
    assert "Đánh vần" in html
    assert "Đua ngữ pháp" in html

@pytest.mark.parametrize("game_type", [
    "MATCHING",
    "SPEED_QUIZ",
    "SCRAMBLE",
    "HANGMAN",
    "CROSSWORD",
    "MEMORY",
    "SPELLING_BEE",
    "GRAMMAR_RACE"
])
def test_start_and_play_all_game_types(client, games_setup, game_type):
    login(client)
    # Start game session
    start_resp = client.post("/games/start", data={
        "game_type": game_type,
        "set_id": "all",
        "status": "all",
        "sort_by": "random",
        "quantity": "10"
    }, follow_redirects=False)
    
    assert start_resp.status_code == 302
    redirect_url = start_resp.headers["Location"]
    assert "/games/play/" in redirect_url
    
    session_id = redirect_url.split("/games/play/")[-1]
    
    # Load game play page
    play_resp = client.get(redirect_url)
    assert play_resp.status_code == 200
    
    # Test API data endpoint
    api_resp = client.get(f"/games/api/data/{session_id}")
    assert api_resp.status_code == 200
    data = api_resp.get_json()
    assert data["status"] == "ok"
    assert data["game_type"] == game_type
    assert len(data["items"]) > 0
    if game_type == "GRAMMAR_RACE":
        assert "grammar_items" in data

def test_submit_game_results_and_xp(client, app, games_setup):
    login(client)
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        initial_xp = user.xp or 0
        
    submit_resp = client.post("/games/submit", json={
        "session_id": "test-session-123",
        "game_type": "SPEED_QUIZ",
        "total_questions": 5,
        "correct_answers": 5,
        "accuracy_rate": 100,
        "duration_seconds": 35
    })
    
    assert submit_resp.status_code == 200
    assert submit_resp.get_json()["status"] == "ok"
    
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.xp >= initial_xp + 25
        gs = GameSession.query.filter_by(session_id="test-session-123").first()
        assert gs is not None
        assert gs.game_type == "SPEED_QUIZ"
        assert gs.accuracy_rate == 100
