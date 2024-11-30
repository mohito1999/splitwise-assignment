from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    memberships = relationship("GroupMembership", back_populates="group")
    expenses = relationship("Expense", back_populates="group")
    balances = relationship("Balance", back_populates="group")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

    memberships = relationship("GroupMembership", back_populates="user")
    expenses_added = relationship("Expense", back_populates="added_by_user")
    balances_owed = relationship("Balance", foreign_keys="[Balance.user_id]", back_populates="user")
    balances_to_receive = relationship("Balance", foreign_keys="[Balance.owe_to]", back_populates="owed_to")


class GroupMembership(Base):
    __tablename__ = 'group_memberships'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    group = relationship("Group", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    added_by = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    description = Column(String)
    split_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="expenses")
    added_by_user = relationship("User", back_populates="expenses_added")
    user = relationship("User", foreign_keys=[added_by])


class Balance(Base):
    __tablename__ = 'balances'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owe_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="balances_owed")
    owed_to = relationship("User", foreign_keys=[owe_to], back_populates="balances_to_receive")
    group = relationship("Group", back_populates="balances")