"""Persistent, capability-authorized collaborative diagrams with three-way merging."""
import asyncio
import copy
import hashlib
import json
import secrets
import sqlite3
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

router = APIRouter()
MISSING = object()


class MergeConflict(Exception):
    def __init__(self, path):
        self.path = path


def merge(base, local, remote, path='diagram'):
    """Merge independent fields and ID-addressed collections; never choose a silent winner."""
    if local == base:
        return copy.deepcopy(remote) if remote is not MISSING else MISSING
    if remote == base or local == remote:
        return copy.deepcopy(local) if local is not MISSING else MISSING
    if all(isinstance(v, dict) for v in (base, local, remote)):
        result = {}
        for key in base.keys() | local.keys() | remote.keys():
            value = merge(base.get(key, MISSING), local.get(key, MISSING), remote.get(key, MISSING), f'{path}.{key}')
            if value is not MISSING:
                result[key] = value
        return result
    if all(isinstance(v, list) for v in (base, local, remote)):
        if all(isinstance(x, dict) and isinstance(x.get('id'), str) for v in (base, local, remote) for x in v):
            maps = [{x['id']: x for x in v} for v in (base, local, remote)]
            if any(len(m) != len(v) for m, v in zip(maps, (base, local, remote))):
                raise MergeConflict(path)
            joined = merge(*maps, path)
            order = list(dict.fromkeys([x['id'] for x in remote + local]))
            return [joined[key] for key in order if key in joined]
    raise MergeConflict(path)


def validate_diagram(value):
    if not isinstance(value, dict) or not isinstance(value.get('classes'), list) or not isinstance(value.get('relationships'), list):
        raise ValueError('Diagrama invalido')
    if len(json.dumps(value)) > 2_000_000:
        raise ValueError('Diagrama demasiado grande')
    classes = value['classes']
    ids = [c.get('id') for c in classes if isinstance(c, dict)]
    if len(ids) != len(classes) or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Identificadores de clases invalidos')
    for rel in value['relationships']:
        if not isinstance(rel, dict) or any(rel.get(side, {}).get('classId') not in ids for side in ('source', 'target')):
            raise ValueError('Relacion sin clase: resuelva el conflicto de borrado')


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS rooms(id TEXT PRIMARY KEY, revision INTEGER, diagram TEXT);
            CREATE TABLE IF NOT EXISTS tokens(room TEXT, hash TEXT PRIMARY KEY, role TEXT);
            CREATE TABLE IF NOT EXISTS revisions(room TEXT, revision INTEGER, diagram TEXT, PRIMARY KEY(room,revision));''')

    def connect(self):
        return sqlite3.connect(self.path)

    def snapshot(self, room, revision=None):
        with self.connect() as db:
            row = db.execute('SELECT revision,diagram FROM rooms WHERE id=?', (room,)).fetchone() if revision is None else db.execute('SELECT revision,diagram FROM revisions WHERE room=? AND revision=?', (room, revision)).fetchone()
        return None if row is None else {'revision': row[0], 'diagram': json.loads(row[1])}

    def role(self, room, token):
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as db:
            row = db.execute('SELECT role FROM tokens WHERE room=? AND hash=?', (room, digest)).fetchone()
        return row[0] if row else None

    def token(self, room, role):
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('INSERT INTO tokens VALUES(?,?,?)', (room, hashlib.sha256(token.encode()).hexdigest(), role))
        return token

    def create(self, diagram):
        validate_diagram(diagram)
        room = secrets.token_urlsafe(18)
        encoded = json.dumps(diagram)
        with self.connect() as db:
            db.execute('INSERT INTO rooms VALUES(?,?,?)', (room, 0, encoded))
            db.execute('INSERT INTO revisions VALUES(?,?,?)', (room, 0, encoded))
        return {'projectId': room, 'token': self.token(room, 'admin'), 'revision': 0, 'diagram': diagram}

    def update(self, room, revision, diagram):
        validate_diagram(diagram)
        base = self.snapshot(room, revision)
        current = self.snapshot(room)
        if base is None:
            raise MergeConflict('revision')
        joined = merge(base['diagram'], diagram, current['diagram'])
        validate_diagram(joined)
        next_revision = current['revision'] + 1
        encoded = json.dumps(joined)
        with self.connect() as db:
            changed = db.execute('UPDATE rooms SET revision=?,diagram=? WHERE id=? AND revision=?', (next_revision, encoded, room, current['revision'])).rowcount
            if not changed:
                raise MergeConflict('revision')
            db.execute('INSERT INTO revisions VALUES(?,?,?)', (room, next_revision, encoded))
        return {'revision': next_revision, 'diagram': joined}


store = Store(Path(__file__).resolve().parents[3] / '.runtime' / 'collaboration.sqlite3')
connections = {}
locks = {}
_rate_limits: dict[str, list[float]] = {}


def check_rate_limit(key: str, max_requests: int = 30, window_seconds: int = 60):
    import time
    now = time.time()
    timestamps = [t for t in _rate_limits.get(key, []) if now - t < window_seconds]
    if len(timestamps) >= max_requests:
        raise HTTPException(429, 'Demasiadas peticiones. Por favor intente más tarde.')
    timestamps.append(now)
    _rate_limits[key] = timestamps


@router.post('/api/collaboration/projects')
async def create_project(request: Request):
    client_ip = request.client.host if request.client else 'unknown'
    check_rate_limit(f'create_{client_ip}', max_requests=30, window_seconds=60)
    try:
        data = await request.json()
        return store.create(data.get('diagram'))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(400, str(exc))


@router.post('/api/collaboration/{room}/invite')
async def invite(room: str, request: Request):
    client_ip = request.client.host if request.client else 'unknown'
    check_rate_limit(f'invite_{client_ip}', max_requests=60, window_seconds=60)
    token = request.headers.get('Authorization', '').removeprefix('Bearer ')
    if store.role(room, token) != 'admin':
        raise HTTPException(403, 'Solo el administrador puede invitar')
    data = await request.json()
    role = data.get('role')
    if role not in ('editor', 'viewer'):
        raise HTTPException(400, 'Rol invalido')
    return {'token': store.token(room, role), 'role': role, 'projectId': room}


async def broadcast(room, message):
    for ws in list(connections.get(room, set())):
        try:
            await ws.send_json(message)
        except Exception:
            connections[room].discard(ws)


@router.websocket('/ws/collaboration/{room}')
async def collaboration(ws: WebSocket, room: str):
    await ws.accept()
    try:
        auth = await asyncio.wait_for(ws.receive_json(), timeout=10)
        role = store.role(room, str(auth.get('token', '')))
        if role is None:
            await ws.close(code=4403)
            return
        connections.setdefault(room, set()).add(ws)
        await ws.send_json({'type': 'snapshot', 'role': role, **store.snapshot(room)})
        await broadcast(room, {'type': 'presence', 'count': len(connections[room])})
        while True:
            msg = await ws.receive_json()
            if msg.get('type') != 'update':
                continue
            if role == 'viewer':
                await ws.send_json({'type': 'error', 'message': 'Enlace de solo lectura'})
                continue
            async with locks.setdefault(room, asyncio.Lock()):
                try:
                    version = msg.get('revision')
                    if not isinstance(version, int):
                        raise ValueError('Revision invalida')
                    result = store.update(room, version, msg.get('diagram'))
                    await ws.send_json({'type': 'ack', **result})
                    await broadcast(room, {'type': 'snapshot', **result})
                except (MergeConflict, ValueError, TypeError) as exc:
                    await ws.send_json({'type': 'conflict', 'message': getattr(exc, 'path', str(exc)), **store.snapshot(room)})
    except (WebSocketDisconnect, asyncio.TimeoutError, ValueError):
        pass
    finally:
        connections.get(room, set()).discard(ws)
        await broadcast(room, {'type': 'presence', 'count': len(connections.get(room, set()))})
