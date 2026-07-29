"""TEST FIXTURE: pengujian CRUD & import/export kamus dengan kata uji sintetis."""

import pytest

DICT_TYPES = ["positive", "negative", "stopwords"]


@pytest.mark.parametrize("dict_type", ["positive", "negative"])
def test_create_positive_negative_entry(client, auth_headers, dict_type):
    response = client.post(
        f"/api/v1/dictionaries/{dict_type}",
        json={"word": "ujicoba", "weight": 2.0},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["word"] == "ujicoba"
    assert response.json()["weight"] == 2.0


def test_create_duplicate_word_rejected(client, auth_headers):
    payload = {"word": "duplikatuji", "weight": 1.0}
    first = client.post("/api/v1/dictionaries/positive", json=payload, headers=auth_headers)
    assert first.status_code == 201
    second = client.post("/api/v1/dictionaries/positive", json=payload, headers=auth_headers)
    assert second.status_code == 409


def test_word_is_normalized_lowercase(client, auth_headers):
    response = client.post(
        "/api/v1/dictionaries/positive", json={"word": "  BaGus  ", "weight": 1.0}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["word"] == "bagus"


def test_create_normalization_entry(client, auth_headers):
    response = client.post(
        "/api/v1/dictionaries/normalization",
        json={"informal_word": "gak", "formal_word": "tidak"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["informal_word"] == "gak"
    assert response.json()["formal_word"] == "tidak"


def test_create_stopword_entry(client, auth_headers):
    response = client.post("/api/v1/dictionaries/stopwords", json={"word": "adalah"}, headers=auth_headers)
    assert response.status_code == 201


def test_update_and_delete_entry(client, auth_headers):
    create_resp = client.post(
        "/api/v1/dictionaries/positive", json={"word": "hapusaku", "weight": 1.0}, headers=auth_headers
    )
    entry_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/v1/dictionaries/positive/{entry_id}", json={"weight": 5.0}, headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["weight"] == 5.0

    delete_resp = client.delete(f"/api/v1/dictionaries/positive/{entry_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    list_resp = client.get("/api/v1/dictionaries/positive?search=hapusaku", headers=auth_headers)
    assert list_resp.json()["pagination"]["total_items"] == 0


def test_list_dictionary_with_pagination(client, auth_headers):
    for i in range(5):
        client.post(
            "/api/v1/dictionaries/positive", json={"word": f"katauji{i}", "weight": 1.0}, headers=auth_headers
        )
    response = client.get("/api/v1/dictionaries/positive?page=1&page_size=2", headers=auth_headers)
    body = response.json()
    assert len(body["items"]) == 2
    assert body["pagination"]["total_items"] >= 5


def test_unknown_dictionary_type_returns_404(client, auth_headers):
    response = client.get("/api/v1/dictionaries/tidakada", headers=auth_headers)
    assert response.status_code == 404


def test_import_positive_dictionary_csv(client, auth_headers):
    csv_content = "word,weight\nmantapuji,2.0\nbagusuji,1.5\nmantapuji,2.0\n"
    response = client.post(
        "/api/v1/dictionaries/positive/import",
        files={"file": ("kamus.csv", csv_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["inserted"] == 2
    assert body["duplicates_skipped"] == 1


def test_import_then_export_roundtrip(client, auth_headers):
    csv_content = "word\nstopworduji1\nstopworduji2\n"
    import_resp = client.post(
        "/api/v1/dictionaries/stopwords/import",
        files={"file": ("stop.csv", csv_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["inserted"] == 2

    export_resp = client.get("/api/v1/dictionaries/stopwords/export", headers=auth_headers)
    assert export_resp.status_code == 200
    assert "stopworduji1" in export_resp.text
    assert "stopworduji2" in export_resp.text
