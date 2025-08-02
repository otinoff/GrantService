from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class QuestionModel(Base):
    __tablename__ = "interview_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_number = Column(Integer, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    field_name = Column(String(100), nullable=False)
    question_type = Column(String(50), default="text", nullable=False)
    options = Column(JSON, nullable=True)  # Список вариантов для select
    hint_text = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    follow_up_question = Column(Text, nullable=True)
    validation_rules = Column(JSON, nullable=True)  # Правила валидации
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Question(id={self.id}, number={self.question_number}, text='{self.question_text[:50]}...')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "field_name": self.field_name,
            "question_type": self.question_type,
            "options": self.options,
            "hint_text": self.hint_text,
            "is_required": self.is_required,
            "follow_up_question": self.follow_up_question,
            "validation_rules": self.validation_rules,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 