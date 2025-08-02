from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ..database.database import get_db
from ..services.question_service import QuestionService
from ..models.question import (
    Question, QuestionCreate, QuestionUpdate, 
    QuestionReorder, QuestionTest, QuestionTestResponse,
    ValidationResult
)

router = APIRouter(prefix="/api/questions", tags=["questions"])

@router.get("/", response_model=List[Question])
async def get_questions(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    active_only: bool = Query(True, description="Только активные вопросы"),
    search: Optional[str] = Query(None, description="Поиск по тексту вопроса"),
    question_type: Optional[str] = Query(None, description="Фильтр по типу вопроса"),
    db: Session = Depends(get_db)
):
    """Получить список всех вопросов с фильтрацией"""
    try:
        service = QuestionService(db)
        questions = service.get_questions(
            skip=skip,
            limit=limit,
            active_only=active_only,
            search=search,
            question_type=question_type
        )
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения вопросов: {str(e)}")

@router.get("/active", response_model=List[Question])
async def get_active_questions(db: Session = Depends(get_db)):
    """Получить все активные вопросы (для Telegram бота)"""
    try:
        service = QuestionService(db)
        questions = service.get_active_questions()
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения активных вопросов: {str(e)}")

@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """Получить конкретный вопрос по ID"""
    service = QuestionService(db)
    question = service.get_question_by_id(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    return question

@router.post("/", response_model=Question)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """Создать новый вопрос"""
    try:
        service = QuestionService(db)
        new_question = service.create_question(question)
        return new_question
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания вопроса: {str(e)}")

@router.put("/{question_id}", response_model=Question)
async def update_question(
    question_id: int, 
    question: QuestionUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить существующий вопрос"""
    try:
        service = QuestionService(db)
        updated_question = service.update_question(question_id, question)
        
        if not updated_question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        
        return updated_question
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления вопроса: {str(e)}")

@router.delete("/{question_id}")
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """Удалить вопрос (мягкое удаление - деактивация)"""
    service = QuestionService(db)
    success = service.delete_question(question_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    return {"message": "Вопрос успешно деактивирован"}

@router.post("/reorder")
async def reorder_questions(
    question_orders: List[QuestionReorder], 
    db: Session = Depends(get_db)
):
    """Изменить порядок вопросов"""
    try:
        service = QuestionService(db)
        orders_data = [{"id": order.id, "new_number": order.new_number} for order in question_orders]
        success = service.reorder_questions(orders_data)
        
        if success:
            return {"message": "Порядок вопросов успешно обновлен"}
        else:
            raise HTTPException(status_code=500, detail="Ошибка обновления порядка")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка изменения порядка: {str(e)}")

@router.post("/{question_id}/test", response_model=QuestionTestResponse)
async def test_question(
    question_id: int, 
    test_data: QuestionTest, 
    db: Session = Depends(get_db)
):
    """Протестировать вопрос с примером ответа"""
    service = QuestionService(db)
    
    # Получаем вопрос
    question = service.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Валидируем ответ
    validation_result = service.validate_answer(question_id, test_data.test_answer)
    
    return QuestionTestResponse(
        question=question,
        test_answer=test_data.test_answer,
        validation_result=validation_result,
        is_valid=validation_result.is_valid
    )

@router.post("/{question_id}/duplicate", response_model=Question)
async def duplicate_question(question_id: int, db: Session = Depends(get_db)):
    """Дублировать вопрос"""
    service = QuestionService(db)
    duplicated_question = service.duplicate_question(question_id)
    
    if not duplicated_question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    return duplicated_question

@router.get("/statistics/summary")
async def get_questions_statistics(db: Session = Depends(get_db)):
    """Получить статистику по вопросам"""
    try:
        service = QuestionService(db)
        stats = service.get_questions_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.post("/import")
async def import_questions(
    questions_data: List[dict], 
    db: Session = Depends(get_db)
):
    """Импорт вопросов из файла"""
    try:
        service = QuestionService(db)
        imported_count = 0
        
        for question_data in questions_data:
            try:
                # Преобразуем данные в формат QuestionCreate
                question_create = QuestionCreate(**question_data)
                service.create_question(question_create)
                imported_count += 1
            except Exception as e:
                # Пропускаем некорректные записи
                continue
        
        return {
            "message": f"Импортировано {imported_count} из {len(questions_data)} вопросов",
            "imported_count": imported_count,
            "total_count": len(questions_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.get("/export/json")
async def export_questions_json(db: Session = Depends(get_db)):
    """Экспорт всех вопросов в JSON"""
    try:
        service = QuestionService(db)
        questions = service.get_questions(active_only=False, limit=1000)
        
        export_data = []
        for question in questions:
            export_data.append(question.to_dict())
        
        return {
            "questions": export_data,
            "export_date": datetime.utcnow().isoformat(),
            "total_count": len(export_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}") 