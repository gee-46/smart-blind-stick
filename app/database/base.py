"""
Shared SQLAlchemy declarative base.

All ORM models import `Base` from here. Keeping the base in its own module
(instead of inside database.py) avoids circular imports between
database.py, models/*, and Alembic migrations later on.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
