from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    TEXT = "text"
    SELECT = "select"
    NUMBER = "number"
    DATE = "date"
    TEXTAREA = "textarea"

class QuestionBase(BaseModel):
    question_number: int = Field(..., ge=1, description="Номер вопроса")
    question_text: str = Field(..., min_length=5, max_length=1000, description="Текст вопроса")
    field_name: str = Field(..., min_length=1, max_length=100, description="Название поля в БД")
    question_type: QuestionType = Field(default=QuestionType.TEXT, description="Тип вопроса")
    options: Optional[List[str]] = Field(default=None, description="Варианты ответов для select")
    hint_text: Optional[str] = Field(default=None, max_length=500, description="Подсказка/пример ответа")
    is_required: bool = Field(default=True, description="Обязательный вопрос")
    follow_up_question: Optional[str] = Field(default=None, max_length=500, description="Уточняющий вопрос")
    validation_rules: Optional[Dict[str, Any]] = Field(default=None, description="Правила валидации")
    is_active: bool = Field(default=True, description="Активный вопрос")

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(QuestionBase):
    question_number: Optional[int] = Field(None, ge=1)
    question_text: Optional[str] = Field(None, min_length=5, max_length=1000)
    field_name: Optional[str] = Field(None, min_length=1, max_length=100)

class Question(QuestionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class QuestionReorder(BaseModel):
    id: int
    new_number: int = Field(..., ge=1)

class QuestionTest(BaseModel):
    test_answer: str = Field(..., min_length=1)

class ValidationResult(BaseModel):
    is_valid: bool
    message: str
    errors: Optional[List[str]] = None

class QuestionTestResponse(BaseModel):
    question: Question
    test_answer: str
    validation_result: ValidationResult
    is_valid: bool 