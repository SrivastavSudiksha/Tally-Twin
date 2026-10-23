from datetime import datetime

from typing import Optional, List

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Patient(Base):

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)

                  

    age: Mapped[int] = mapped_column(Integer, nullable=False)

    sex: Mapped[str] = mapped_column(String(16), nullable=False)

    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

          

    serum_creatinine: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    egfr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    alt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ast: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    bilirubin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    albumin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

              

    conditions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    allergies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    current_medicines: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    smoking: Mapped[bool] = mapped_column(Boolean, default=False)

    alcohol: Mapped[str] = mapped_column(String(32), default="none")

                             

    cyp2d6: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    cyp2c19: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    cyp2c9: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    qtc_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

                                      

    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    clearance_adjustment_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(

        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow

    )

    simulations: Mapped[List["Simulation"]] = relationship(

        "Simulation", back_populates="patient", cascade="all, delete-orphan"

    )

    def __repr__(self) -> str:

        return f"<Patient id={self.id} age={self.age} sex={self.sex}>"

