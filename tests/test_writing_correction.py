import pytest
from app.backend.learning.grammar_checker import check_grammar_and_spelling, check_with_local_rules
from tests.conftest import login


def test_local_grammar_checker_spelling():
    """Test local rule-based spell checker for common English misspellings."""
    text = "I recieved teh letter and it is seperate from tommorow goverment report."
    matches = check_with_local_rules(text)
    
    rule_ids = [m["rule_id"] for m in matches]
    assert any("RECIEVE" in r for r in rule_ids)
    assert any("TEH" in r for r in rule_ids)
    assert any("SEPERATE" in r for r in rule_ids)
    assert any("TOMMOROW" in r for r in rule_ids)
    assert any("GOVERMENT" in r for r in rule_ids)


def test_local_grammar_checker_capitalization():
    """Test capitalization rules for pronoun 'I' and start of sentence."""
    text = "hello world. i am learning english. it is great."
    matches = check_with_local_rules(text)
    
    rule_ids = [m["rule_id"] for m in matches]
    assert "PRONOUN_I_CAPITALIZATION" in rule_ids
    assert "SENTENCE_START_CAPITALIZATION" in rule_ids


def test_local_grammar_checker_repeated_words():
    """Test repeated/duplicated word detection."""
    text = "We went to the the park and and played games."
    matches = check_with_local_rules(text)
    
    repeat_matches = [m for m in matches if m["rule_id"] == "REPEATED_WORD"]
    assert len(repeat_matches) >= 2


def test_local_grammar_checker_subject_verb_agreement():
    """Test subject-verb agreement and article rules."""
    text = "He have a apple and they has an book."
    matches = check_with_local_rules(text)
    
    categories = [m["category"] for m in matches]
    assert any("Grammar" in c for c in categories)


def test_local_grammar_checker_clean_text():
    """Test clean grammatically correct English text."""
    text = "She goes to school every day. The students are studying hard in the library."
    matches = check_with_local_rules(text)
    assert len(matches) == 0


def test_check_grammar_and_spelling_empty():
    """Test grammar checker with empty text."""
    res = check_grammar_and_spelling("")
    assert res["success"] is True
    assert len(res["matches"]) == 0
    assert res["stats"]["word_count"] == 0


def test_check_writing_api_authenticated(client):
    """Test POST /check-writing API endpoint when logged in."""
    login(client)
    
    res = client.post(
        "/check-writing",
        json={"text": "i have a apple and teh book."}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "matches" in data
    assert len(data["matches"]) >= 2
    assert "stats" in data
    assert data["stats"]["word_count"] > 0


def test_check_writing_api_lessons_alias(client):
    """Test alias POST /lessons/check-writing."""
    login(client)
    
    res = client.post(
        "/lessons/check-writing",
        json={"text": "She write well and they is happy."}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True


def test_check_writing_api_unauthorized(client):
    """Test that unauthorized requests are redirected or rejected."""
    res = client.post(
        "/check-writing",
        json={"text": "Some text"}
    )
    # Flask-Login redirects to login page for unauthorized requests
    assert res.status_code in [302, 401]
