import pytest
from datetime import datetime, timedelta
from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import FlashcardSet, FlashcardItem, FlashcardProgress
from tests.conftest import login

@pytest.fixture
def flashcard_setup(app):
    with app.app_context():
        # Find the student user
        user = User.query.filter_by(username="student").first()
        
        # Create a set
        fset = FlashcardSet(title="Animals", description="Animal vocabulary", user_id=user.id, is_public=True)
        db.session.add(fset)
        db.session.flush()
        
        # Add items
        item1 = FlashcardItem(set_id=fset.id, term="Cat", definition="Con mèo", order=1)
        item2 = FlashcardItem(set_id=fset.id, term="Dog", definition="Con chó", order=2)
        item3 = FlashcardItem(set_id=fset.id, term="Bird", definition="Con chim", order=3)
        item4 = FlashcardItem(set_id=fset.id, term="Fish", definition="Con cá", order=4)
        db.session.add_all([item1, item2, item3, item4])
        db.session.commit()
        return fset.id, [item1.id, item2.id, item3.id, item4.id]

def test_flashcard_sets_lobby_requires_login(client):
    response = client.get("/flashcard-sets")
    assert response.status_code == 302

def test_flashcard_sets_lobby_success(client, flashcard_setup):
    login(client)
    response = client.get("/flashcard-sets")
    assert response.status_code == 200
    assert "Animals" in response.get_data(as_text=True)

def test_flashcard_set_create_success(client, app):
    login(client)
    response = client.post("/flashcard-sets/new", data={
        "title": "Colors",
        "description": "Colors vocabulary",
        "is_public": "on",
        "terms[]": ["Red", "Blue"],
        "definitions[]": ["Màu đỏ", "Màu xanh dương"],
        "images[]": ["", ""],
        "item_ids[]": ["", ""]
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Colors" in response.get_data(as_text=True)
    
    with app.app_context():
        fset = FlashcardSet.query.filter_by(title="Colors").first()
        assert fset is not None
        assert len(fset.items) == 2

def test_flashcard_set_sync_srs(client, app, flashcard_setup):
    login(client)
    set_id, item_ids = flashcard_setup
    
    # Sync progress: 2 known, 1 learning
    response = client.post(f"/flashcard-sets/{set_id}/sync", json={
        "progress": {
            "know_ids": [item_ids[0], item_ids[1]],
            "learning_ids": [item_ids[2]]
        },
        "completed_round": 1
    })
    
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    
    with app.app_context():
        # Check known cards
        p1 = FlashcardProgress.query.filter_by(item_id=item_ids[0]).first()
        assert p1.is_known is True
        assert p1.srs_level == 2 # 1 + 1
        assert p1.next_review_at > datetime.utcnow() + timedelta(days=2) # Level 2 -> 3 days
        
        # Check learning card
        p3 = FlashcardProgress.query.filter_by(item_id=item_ids[2]).first()
        assert p3.is_known is False
        assert p3.srs_level == 1
        assert p3.next_review_at < datetime.utcnow() + timedelta(days=2) # Level 1 -> 1 day

def test_game_srs_due_filtering(client, app, flashcard_setup):
    login(client)
    set_id, item_ids = flashcard_setup
    
    # Calculate stats with srs_due (since there is no progress, all 4 cards should be considered due)
    response = client.post("/games/calculate-stats", json={
        "set_id": set_id,
        "status": "srs_due"
    })
    assert response.status_code == 200
    assert response.json["available_count"] == 4
    
    # Sync progress to make some not due (easy known will advance to 3 days from now, so not due now)
    client.post(f"/flashcard-sets/{set_id}/sync", json={
        "progress": {
            "know_ids": [item_ids[0], item_ids[1]],
            "learning_ids": []
        },
        "completed_round": 1
    })
    
    # Calculate stats with srs_due again (2 should be due: item 3 and 4 which were never reviewed)
    response = client.post("/games/calculate-stats", json={
        "set_id": set_id,
        "status": "srs_due"
    })
    assert response.status_code == 200
    assert response.json["available_count"] == 2
