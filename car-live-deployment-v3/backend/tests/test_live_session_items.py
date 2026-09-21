"""Live-session item model: create, edit, add, delete, progress and re-sync."""
from fastapi.testclient import TestClient
import pytest

from app import main
from app.config import settings
from app.db import init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'database_path', tmp_path / 'live.sqlite3')
    monkeypatch.setattr(settings, 'upload_dir', tmp_path / 'uploads')
    monkeypatch.setattr(settings, 'llm_base_url', '')
    monkeypatch.setattr(settings, 'llm_model', '')
    init_db()
    return TestClient(main.app)


SCRIPT = "第一句话，介绍今天的直播主题。第二句话，原本介绍续航表现。第三句话，最后说明购车政策。"
SCRIPT_EDITED = "第一句话，介绍今天的直播主题。第二句话，改成重点介绍智能驾驶表现。第三句话，最后说明购车政策。"


def create(client, script=SCRIPT):
    response = client.post('/api/live/sessions', json={'vehicle': '欧拉5', 'script': script, 'voice_id': 'steady'})
    assert response.status_code == 200, response.text
    return response.json()


def item_ids(session):
    return [item['id'] for item in session['items']]


def test_session_create_splits_script_into_ordered_items(client):
    session = create(client)
    assert [item['text'] for item in session['items']] == [
        '第一句话，介绍今天的直播主题。',
        '第二句话，原本介绍续航表现。',
        '第三句话，最后说明购车政策。',
    ]
    assert [item['revision'] for item in session['items']] == [0, 0, 0]
    assert {item['status'] for item in session['items']} == {'待播'}


def test_edit_queued_item_bumps_revision_in_place(client):
    session = create(client)
    target = session['items'][1]
    response = client.patch(f"/api/live/sessions/{session['id']}/items/{target['id']}", json={'text': '改成重点介绍智能驾驶表现。'})
    assert response.status_code == 200, response.text
    updated = response.json()['items'][1]
    assert updated['id'] == target['id']
    assert updated['text'] == '改成重点介绍智能驾驶表现。'
    assert updated['revision'] == 1


def test_add_item_after_position_and_delete(client):
    session = create(client)
    first_id = session['items'][0]['id']
    response = client.post(f"/api/live/sessions/{session['id']}/items", json={'text': '这是新增话术。', 'after_id': first_id})
    assert response.status_code == 200, response.text
    items = response.json()['items']
    assert [item['text'] for item in items][1] == '这是新增话术。'
    new_id = items[1]['id']
    assert new_id not in item_ids(session)

    removed = client.delete(f"/api/live/sessions/{session['id']}/items/{new_id}")
    assert removed.status_code == 200, removed.text
    assert [item['text'] for item in removed.json()['items']] == [item['text'] for item in session['items']]


def test_played_items_are_protected(client):
    session = create(client)
    first_id = session['items'][0]['id']
    progressed = client.patch(f"/api/live/sessions/{session['id']}/progress", json={'current_item_id': session['items'][1]['id'], 'status': 'playing'})
    assert progressed.status_code == 200, progressed.text
    assert progressed.json()['items'][0]['status'] == '已播放'
    assert progressed.json()['items'][1]['status'] == '播放中'

    blocked = client.patch(f"/api/live/sessions/{session['id']}/items/{first_id}", json={'text': '不允许修改'})
    assert blocked.status_code == 409, blocked.text
    blocked = client.delete(f"/api/live/sessions/{session['id']}/items/{first_id}")
    assert blocked.status_code == 409, blocked.text


def test_progress_none_marks_everything_played(client):
    session = create(client)
    response = client.patch(f"/api/live/sessions/{session['id']}/progress", json={'current_item_id': None, 'status': 'completed'})
    assert response.status_code == 200, response.text
    assert {item['status'] for item in response.json()['items']} == {'已播放'}


def test_script_resync_updates_unplayed_tail(client):
    session = create(client)
    client.patch(f"/api/live/sessions/{session['id']}/progress", json={'current_item_id': session['items'][1]['id'], 'status': 'playing'})
    response = client.patch(f"/api/live/sessions/{session['id']}/script", json={'script': SCRIPT_EDITED, 'sentence': 1})
    assert response.status_code == 200, response.text
    items = response.json()['items']
    # The played prefix is preserved and the unplayed tail is re-synced.
    assert items[0]['text'] == '第一句话，介绍今天的直播主题。'
    assert items[0]['status'] == '已播放'
    assert items[1]['revision'] >= 1


def test_script_resync_rejects_touching_played_item(client):
    session = create(client)
    client.patch(f"/api/live/sessions/{session['id']}/progress", json={'current_item_id': session['items'][1]['id'], 'status': 'playing'})
    response = client.patch(f"/api/live/sessions/{session['id']}/script", json={'script': '改掉第一句。' + SCRIPT_EDITED, 'sentence': 0})
    assert response.status_code == 409, response.text
    reloaded = client.get(f"/api/live/sessions/{session['id']}").json()
    assert reloaded['items'][0]['text'] == '第一句话，介绍今天的直播主题。'


def test_add_after_played_item_lands_after_the_playing_item(client):
    session = create(client)
    first_id = session['items'][0]['id']
    playing_id = session['items'][1]['id']
    # Item 1 is played and item 2 is playing once playback moves to item 2.
    client.patch(f"/api/live/sessions/{session['id']}/progress", json={'current_item_id': playing_id, 'status': 'playing'})
    response = client.post(f"/api/live/sessions/{session['id']}/items", json={'text': '新增话术。', 'after_id': first_id})
    assert response.status_code == 200, response.text
    items = response.json()['items']
    assert items[0]['id'] == first_id and items[0]['status'] == '已播放'
    # The table order must match the audible order: a new item inserted after a
    # played row plays right after the item that is currently playing.
    assert items[1]['id'] == playing_id and items[1]['status'] == '播放中'
    assert items[2]['text'] == '新增话术。'


def test_unknown_session_and_item_fail_explicitly(client):
    session = create(client)
    assert client.get('/api/live/sessions/nope').status_code == 404
    assert client.patch(f"/api/live/sessions/{session['id']}/items/999", json={'text': 'x'}).status_code == 404
    assert client.post(f"/api/live/sessions/{session['id']}/items", json={'text': 'x', 'after_id': 999}).status_code == 404
