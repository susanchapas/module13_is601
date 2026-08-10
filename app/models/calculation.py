# app/models/calculation.py
import uuid
from functools import reduce
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base, utcnow
from app.operations import add, subtract, multiply, divide

class AbstractCalculation:
    """Abstract base class for calculations"""
    
    @declared_attr
    def __tablename__(cls):
        return 'calculations'

    @declared_attr
    def id(cls):
        return Column(
            UUID(as_uuid=True), 
            primary_key=True, 
            default=uuid.uuid4,
            nullable=False
        )

    @declared_attr
    def user_id(cls):
        return Column(
            UUID(as_uuid=True), 
            ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        )

    @declared_attr
    def type(cls):
        return Column(
            String(50), 
            nullable=False,
            index=True
        )

    @declared_attr
    def inputs(cls):
        return Column(
            JSON, 
            nullable=False
        )

    @declared_attr
    def result(cls):
        return Column(
            Float,
            nullable=True
        )

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            default=utcnow,
            nullable=False
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            default=utcnow,
            onupdate=utcnow,
            nullable=False
        )

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID, inputs: List[float]) -> "Calculation":
        """Factory method to create calculations"""
        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return calculation_class(user_id=user_id, inputs=inputs)

    _operation = None

    def get_result(self) -> float:
        """Reduce the inputs with this calculation's arithmetic operation."""
        if self._operation is None:
            raise NotImplementedError
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        return reduce(self._operation, self.inputs)

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"

class Calculation(Base, AbstractCalculation):
    """Base calculation model"""
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
        #"with_polymorphic": "*"
    }

class Addition(Calculation):
    """Addition calculation"""
    __mapper_args__ = {"polymorphic_identity": "addition"}
    _operation = staticmethod(add)

class Subtraction(Calculation):
    """Subtraction calculation"""
    __mapper_args__ = {"polymorphic_identity": "subtraction"}
    _operation = staticmethod(subtract)

class Multiplication(Calculation):
    """Multiplication calculation"""
    __mapper_args__ = {"polymorphic_identity": "multiplication"}
    _operation = staticmethod(multiply)

class Division(Calculation):
    """Division calculation"""
    __mapper_args__ = {"polymorphic_identity": "division"}
    _operation = staticmethod(divide)
