import asyncio

import httpx
from fastapi import FastAPI

from app.services import collaboration as collab
from app.services.team_push import TeamPush


def test_team_message_reaches_push_delivery(tmp_path, monkeypatch):
    """A saved team message must reach push delivery without calling the AI."""
    push = TeamPush(tmp_path / 'push')
    monkeypatch.setattr(collab, 'push', push)
    monkeypatch.setattr(collab, 'store', collab.Store(tmp_path / 'collaboration.sqlite3'))
    monkeypatch.setattr(collab, 'connections', {})
    delivered = []
    monkeypatch.setattr(push, 'deliver', lambda room, event: delivered.append((room, event)))
    app = FastAPI()
    app.include_router(collab.router)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            project = (await client.post('/api/collaboration/projects', json={
                'diagram': {'name': 'Push', 'classes': [], 'relationships': []}
            })).json()
            room = project['projectId']
            with push.connect() as db:
                db.execute('INSERT INTO native_subscriptions VALUES(?,?,?)', (room, 'test', 'fake-device-token'))
            response = await client.post(f'/api/collaboration/{room}/conversation',
                headers={'Authorization': 'Bearer ' + project['token']},
                json={'actor': 'Alejandro', 'message': 'Prueba de aviso', 'askAI': False})
            assert response.status_code == 200
            await asyncio.gather(*push.tasks)
            assert delivered == [(room, response.json()['event'])]
            assert response.json()['event']['kind'] == 'message'

    asyncio.run(scenario())
