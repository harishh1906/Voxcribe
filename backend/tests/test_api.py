def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_transcription(client):
    r = client.post("/api/transcriptions/", json={
        "title": "Test Recording",
        "transcription_text": "Hello world",
        "language_detected": "en",
        "duration_seconds": 5.0,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Test Recording"
    assert data["word_count"] == 2
    assert data["id"]


def test_list_transcriptions(client):
    client.post("/api/transcriptions/", json={"title": "One", "transcription_text": "a"})
    client.post("/api/transcriptions/", json={"title": "Two", "transcription_text": "b c"})
    r = client.get("/api/transcriptions/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_transcription(client):
    created = client.post("/api/transcriptions/", json={"title": "Get me", "transcription_text": "text"}).json()
    r = client.get(f"/api/transcriptions/{created['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Get me"


def test_update_transcription(client):
    created = client.post("/api/transcriptions/", json={"title": "Old", "transcription_text": "old text"}).json()
    r = client.put(f"/api/transcriptions/{created['id']}", json={"title": "New", "transcription_text": "new text here"})
    assert r.status_code == 200
    assert r.json()["title"] == "New"
    assert r.json()["word_count"] == 3


def test_delete_transcription(client):
    created = client.post("/api/transcriptions/", json={"title": "Delete me", "transcription_text": ""}).json()
    r = client.delete(f"/api/transcriptions/{created['id']}")
    assert r.status_code == 200
    r2 = client.get(f"/api/transcriptions/{created['id']}")
    assert r2.status_code == 404


def test_not_found(client):
    r = client.get("/api/transcriptions/nonexistent-id")
    assert r.status_code == 404


def test_search(client):
    client.post("/api/transcriptions/", json={"title": "Python notes", "transcription_text": "hello"})
    client.post("/api/transcriptions/", json={"title": "Java notes", "transcription_text": "world"})
    r = client.get("/api/transcriptions/?search=Python")
    assert r.json()["total"] == 1


def test_dashboard_stats(client):
    client.post("/api/transcriptions/", json={"title": "T1", "transcription_text": "a b c", "duration_seconds": 10.0, "language_detected": "en"})
    r = client.get("/api/transcriptions/stats/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_transcriptions"] == 1
    assert data["total_words"] == 3
