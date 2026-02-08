from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))

    severity = Column(String(20), nullable=False)  # IMPORTANT (see problem 2)

    scan = relationship(
        "Scan",
        back_populates="findings"
    )
