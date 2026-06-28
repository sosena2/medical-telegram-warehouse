import json
from pathlib import Path


def test_project_structure():
    """Check key project folders exist."""
    assert Path("src").exists()
    assert Path("api").exists()
    assert Path("tests").exists()


def test_message_structure():
    """Test message record has required fields."""
    required_fields = [
        "message_id", "channel_name", "message_date",
        "message_text", "has_media", "views", "forwards"
    ]
    message = {
        "message_id": 1,
        "channel_name": "tikvahpharma",
        "message_date": "2024-06-01T08:30:00",
        "message_text": "Amoxicillin in stock",
        "has_media": False,
        "views": 100,
        "forwards": 5,
    }
    for field in required_fields:
        assert field in message


def test_json_read_write(tmp_path):
    """Test saving and loading JSON."""
    data = [{"message_id": 1, "text": "test"}]
    f = tmp_path / "test.json"
    f.write_text(json.dumps(data))
    loaded = json.loads(f.read_text())
    assert loaded[0]["message_id"] == 1