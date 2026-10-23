from datetime import datetime

from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, JSON

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Simulation(Base):

    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    patient_id: Mapped[Optional[int]] = mapped_column(

        Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True

    )

                 

    drug_identifier: Mapped[str] = mapped_column(String(256), nullable=False, index=True)

    dose_mg: Mapped[float] = mapped_column(Float, nullable=False)

    route: Mapped[str] = mapped_column(String(16), nullable=False, default="oral")

    frequency: Mapped[str] = mapped_column(String(64), nullable=False)

    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

                                     

    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    overall_confidence: Mapped[str] = mapped_column(String(16), nullable=False)

    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

                                                

    patient_cmax: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    patient_half_life_h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    patient_auc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    clearance_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    accumulation_risk: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

                                                                  

    full_report: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    patient: Mapped[Optional["Patient"]] = relationship("Patient", back_populates="simulations")

    def __repr__(self) -> str:

        return f"<Simulation id={self.id} drug={self.drug_identifier} risk={self.risk_level}>"

