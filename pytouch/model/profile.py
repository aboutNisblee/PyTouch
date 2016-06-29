from sqlalchemy import Column, Integer, String
from .super import Base


class Profile(Base):
    __tablename__ = 'tblProfile'

    name = Column('pkProfileName', String, primary_key=True)
    skillLevel = Column('cSkillLevel', Integer, nullable=False, default=0)
