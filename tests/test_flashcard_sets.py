import pytest
from datetime import datetime, timedelta
from app.extensions import db
from app.backend.auth.models import User
from app.backend.learning.models import FlashcardSet, FlashcardItem, FlashcardProgress
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
    response = client.get("/flashcard-sets", follow_redirects=True)
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


def test_flashcard_set_sharing_and_cloning(client, app, flashcard_setup):
    set_id, item_ids = flashcard_setup
    
    with app.app_context():
        fset = db.session.get(FlashcardSet, set_id)
        share_code = fset.get_share_code()
        assert share_code is not None
        assert len(share_code) >= 8

    # 1. Unauthenticated user can view shared flashcard page
    response = client.get(f"/flashcards/share/{share_code}")
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "Animals" in content
    assert "Cat" in content
    assert "Dog" in content
    assert "Đăng nhập để sao chép bộ thẻ" in content

    # Alternate route /flashcard-sets/share/<share_code> also works
    response2 = client.get(f"/flashcard-sets/share/{share_code}")
    assert response2.status_code == 200

    # 2. Cloning requires login
    clone_res = client.post(f"/flashcards/share/{share_code}/clone")
    assert clone_res.status_code == 302 # redirect to login

    # 3. Authenticated user clones the set
    login(client)
    clone_res2 = client.post(f"/flashcards/share/{share_code}/clone", follow_redirects=True)
    assert clone_res2.status_code == 200
    assert "Đã sao chép thành công bộ flashcard" in clone_res2.get_data(as_text=True)

    with app.app_context():
        # Verify cloned set in DB
        user = User.query.filter_by(username="student").first()
        cloned_sets = FlashcardSet.query.filter_by(user_id=user.id).all()
        assert len(cloned_sets) >= 2 # Original + cloned
        new_set = cloned_sets[-1]
        assert new_set.id != set_id
        assert len(new_set.items) == 4
        assert new_set.share_code != share_code # New unique share code

    # 4. Clone by set_id
    clone_res3 = client.post(f"/flashcard-sets/{set_id}/clone", follow_redirects=True)
    assert clone_res3.status_code == 200
    assert "Đã sao chép thành công bộ flashcard" in clone_res3.get_data(as_text=True)


def test_flashcard_share_404_on_invalid_code(client):
    response = client.get("/flashcards/share/invalid_code_12345")
    assert response.status_code == 404


def test_flashcard_set_privacy_toggle_and_filtering(client, app, flashcard_setup):
    login(client)
    set_id, _ = flashcard_setup
    
    # 1. Toggle privacy via POST
    response = client.post(f"/flashcard-sets/{set_id}/toggle-privacy", headers={"X-Requested-With": "XMLHttpRequest"})
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["is_public"] is False # toggled from True to False

    with app.app_context():
        fset = db.session.get(FlashcardSet, set_id)
        assert fset.is_public is False

    # 2. Toggle back to public
    response2 = client.post(f"/flashcard-sets/{set_id}/toggle-privacy", follow_redirects=True)
    assert response2.status_code == 200

    with app.app_context():
        fset = db.session.get(FlashcardSet, set_id)
        assert fset.is_public is True


def test_flashcard_set_create_private(client, app):
    login(client)
    response = client.post("/flashcard-sets/new", data={
        "title": "Private Vocab Set",
        "description": "Only for me",
        # is_public omitted -> default False
        "terms[]": ["Secret"],
        "definitions[]": ["Bí mật"],
        "images[]": [""],
        "item_ids[]": [""]
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with app.app_context():
        fset = FlashcardSet.query.filter_by(title="Private Vocab Set").first()
        assert fset is not None
        assert fset.is_public is False


