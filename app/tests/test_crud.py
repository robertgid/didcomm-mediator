import uuid

import pytest
from databases import Database

from app.db.crud import ensure_agent_exists, load_agent, load_agent_via_verkey, ensure_endpoint_exists, load_endpoint


@pytest.mark.asyncio
async def test_agent_ops(test_database: Database, random_me: (str, str, str), random_fcm_device_id: str):
    did, verkey, secret = random_me
    await ensure_agent_exists(test_database, did, verkey)
    # Check-1: ensure agent is stored in db
    agent = await load_agent(test_database, did)
    assert agent is not None
    assert agent['id']
    assert agent['did'] == did
    assert agent['verkey'] == verkey
    assert agent['metadata'] is None
    # Check-2: check unknown agent is None
    agent = await load_agent(test_database, 'invalid-did')
    assert agent is None
    # Check-3: update verkey
    verkey2 = 'VERKEY2'
    await ensure_agent_exists(test_database, did, verkey2)
    agent = await load_agent(test_database, did)
    assert agent['verkey'] == verkey2
    # Check-4: update metadata
    metadata = {'key1': 'value1', 'key2': 111}
    await ensure_agent_exists(test_database, did, verkey2, metadata)
    agent = await load_agent(test_database, did)
    assert agent['metadata'] == metadata
    # Check-5: call to ensure_exists don't clear metadata
    await ensure_agent_exists(test_database, did, verkey2)
    agent = await load_agent(test_database, did)
    assert agent['metadata'] == metadata
    # Check-6: FCM device id
    await ensure_agent_exists(test_database, did, verkey=verkey2, fcm_device_id=random_fcm_device_id)
    agent = await load_agent(test_database, did)
    assert agent['fcm_device_id'] == random_fcm_device_id
    # Check-7: load agent via verkey
    agent_via_verkey = await load_agent_via_verkey(test_database, verkey2)
    assert agent == agent_via_verkey


@pytest.mark.asyncio
async def test_endpoints_ops(test_database: Database, random_redis_pub_sub: str):
    uid = uuid.uuid4().hex
    await ensure_endpoint_exists(test_database, uid, random_redis_pub_sub)
    # Check-1: ensure endpoint is stored in db
    endpoint = await load_endpoint(test_database, uid)
    assert endpoint is not None
    assert endpoint['uid'] == uid
    assert endpoint['agent_id'] is None
    assert endpoint['redis_pub_sub'] == random_redis_pub_sub
    # Check-2: set agent_id
    agent_id = uuid.uuid4().hex
    await ensure_endpoint_exists(test_database, uid, agent_id=agent_id)
    endpoint = await load_endpoint(test_database, uid)
    assert endpoint is not None
    assert endpoint['uid'] == uid
    assert endpoint['agent_id'] == agent_id
    assert endpoint['redis_pub_sub'] == random_redis_pub_sub

