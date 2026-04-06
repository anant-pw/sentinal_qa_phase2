from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class TestPlan(Base):
    __tablename__ = "test_plans"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    status = Column(String, default="pending")  # pending, approved, running
    claimed_by = Column(String, nullable=True)  # xdist worker id
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    steps = relationship("TestStep", back_populates="plan", cascade="all, delete-orphan")

class TestStep(Base):
    __tablename__ = "test_steps"
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("test_plans.id"))
    action = Column(String)
    selector = Column(String, nullable=True)
    data = Column(String, nullable=True)
    sequence = Column(Integer)
    plan = relationship("TestPlan", back_populates="steps")

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("test_plans.id"))
    status = Column(String)  # passed / failed
    failing_selector = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    plan = relationship("TestPlan")
