import sqlalchemy

from .database import metadata


users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True, index=True),
    sqlalchemy.Column("hashed_password", sqlalchemy.String),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=True)
)


agents = sqlalchemy.Table(
    "agents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("did", sqlalchemy.String, unique=True, index=True),
    sqlalchemy.Column("verkey", sqlalchemy.String, index=True),
    sqlalchemy.Column("metadata", sqlalchemy.JSON, nullable=True),
    sqlalchemy.Column("fcm_device_id", sqlalchemy.String, nullable=True, index=True)
)


pairwises = sqlalchemy.Table(
    'pairwises',
    metadata,
    sqlalchemy.Column("their_did", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("their_verkey", sqlalchemy.String, index=True),
    sqlalchemy.Column("my_did", sqlalchemy.String, index=True),
    sqlalchemy.Column("my_verkey", sqlalchemy.String, index=True),
    sqlalchemy.Column("metadata", sqlalchemy.JSON)
)


endpoints = sqlalchemy.Table(
    'endpoints',
    metadata,
    sqlalchemy.Column("uid", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("verkey", sqlalchemy.String, index=True),
    sqlalchemy.Column("agent_id", sqlalchemy.String, index=True, nullable=True),
    sqlalchemy.Column("redis_pub_sub", sqlalchemy.String),
)
