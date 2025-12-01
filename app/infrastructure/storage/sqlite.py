from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    external_auth_id = Column(String, nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PlanModel(Base):
    __tablename__ = "plans"

    name = Column(String, primary_key=True)
    vcpu = Column(Integer, nullable=False)
    memory_mb = Column(Integer, nullable=False)
    disk_gb = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    proxmox_host_id = Column(String, nullable=True)
    proxmox_node = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    template_vmid = Column(Integer, nullable=True)
    disk_storage = Column(String, nullable=True)
    clone_mode = Column(String, default="full", nullable=True)
    price = Column(Float, nullable=True)
    default_expire_days = Column(Integer, nullable=True)


class UpgradeModel(Base):
    __tablename__ = "upgrades"

    name = Column(String, primary_key=True)
    add_vcpu = Column(Integer, default=0)
    add_memory_mb = Column(Integer, default=0)
    add_disk_gb = Column(Integer, default=0)
    price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)


class ProxmoxHostModel(Base):
    __tablename__ = "proxmox_hosts"

    id = Column(String, primary_key=True)
    api_url = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    realm = Column(String, nullable=False)
    node = Column(String, nullable=True)
    location = Column(String, nullable=False)


class ServerModel(Base):
    __tablename__ = "servers"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan = Column(String, ForeignKey("plans.name"), nullable=False)
    location = Column(String, nullable=False)
    proxmox_host_id = Column(String, ForeignKey("proxmox_hosts.id"), nullable=True)
    proxmox_node = Column(String, nullable=True)
    vcpu = Column(Integer, nullable=True)
    memory_mb = Column(Integer, nullable=True)
    disk_gb = Column(Integer, nullable=True)
    disk_storage = Column(String, nullable=True)
    primary_ip = Column(String, nullable=True)
    expire_in_days = Column(Integer, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    external_id = Column(String, nullable=True)
    last_notified_at = Column(DateTime, nullable=True)

    upgrades = relationship("ServerUpgradeModel", back_populates="server", cascade="all, delete-orphan")


class ServerUpgradeModel(Base):
    __tablename__ = "server_upgrades"
    __table_args__ = (
        UniqueConstraint("server_id", "upgrade_name", "applied_at", name="uq_server_upgrade"),
    )

    server_id = Column(String, ForeignKey("servers.id"), primary_key=True)
    upgrade_name = Column(String, ForeignKey("upgrades.name"), primary_key=True)
    applied_at = Column(DateTime, default=datetime.utcnow, primary_key=True)
    price = Column(Float, nullable=True)

    server = relationship("ServerModel", back_populates="upgrades")


class SQLAlchemyDataStore:
    """SQLAlchemy-backed datastore with SQLite default."""

    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        url = path if "://" in path else f"sqlite:///{path}"
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
        Base.metadata.create_all(self.engine)

    def session(self) -> Session:
        return self.SessionLocal()
