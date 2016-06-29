from sqlalchemy import Column, String
from .super import Base


class Meta(Base):
    __tablename__ = 'tblMeta'

    key = Column('pkKey', String(64), primary_key=True)
    value = Column('cValue', String(256))
