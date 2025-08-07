"""
Writer Agent - агент для написания заявок на гранты
"""
from typing import Dict, Any, List
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class WriterAgent(BaseAgent):
    """Агент-писатель для создания заявок на гранты"""
    
    def __init__(self, db):
        super().__init__("writer", db)
    
    def _get_goal(self) -> str:
        return "Создать качественную заявку на грант на основе данных пользователя и найденной информации"
    
    def _get_backstory(self) -> str:
        return """Ты профессиональный грант-райтер с 15-летним опытом написания заявок. 
        Ты знаешь все секреты успешных заявок, умеешь структурировать информацию и убедительно 
        представлять проекты. Твои заявки имеют высокий процент одобрения."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на грант"""
        try:
            # Извлекаем данные
            user_answers = input_data.get('user_answers', {})
            research_data = input_data.get('research_data', {})
            selected_grant = input_data.get('selected_grant', {})
            
            # Создаем структуру заявки
            application_structure = self._create_application_structure(selected_grant)
            
            # Генерируем содержание заявки
            application_content = self._generate_application_content(
                user_answers, research_data, selected_grant, application_structure
            )
            
            # Проверяем качество
            quality_check = self._check_application_quality(application_content)
            
            return {
                'status': 'success',
                'application': application_content,
                'structure': application_structure,
                'quality_score': quality_check['score'],
                'suggestions': quality_check['suggestions']
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания заявки: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка создания заявки: {str(e)}"
            }
    
    def _create_application_structure(self, selected_grant: Dict) -> Dict[str, str]:
        """Создание структуры заявки"""
        return {
            'title': 'Название проекта',
            'summary': 'Краткое описание проекта',
            'problem': 'Описание проблемы',
            'solution': 'Предлагаемое решение',
            'implementation': 'План реализации',
            'budget': 'Бюджет проекта',
            'timeline': 'Временные рамки',
            'team': 'Команда проекта',
            'impact': 'Ожидаемый результат',
            'sustainability': 'Устойчивость проекта'
        }
    
    def _generate_application_content(self, user_answers: Dict, research_data: Dict, 
                                   selected_grant: Dict, structure: Dict) -> Dict[str, str]:
        """Генерация содержания заявки"""
        content = {}
        
        # Название проекта
        content['title'] = self._generate_title(user_answers, selected_grant)
        
        # Краткое описание
        content['summary'] = self._generate_summary(user_answers, selected_grant)
        
        # Описание проблемы
        content['problem'] = self._generate_problem_description(user_answers)
        
        # Решение
        content['solution'] = self._generate_solution(user_answers, research_data)
        
        # План реализации
        content['implementation'] = self._generate_implementation_plan(user_answers)
        
        # Бюджет
        content['budget'] = self._generate_budget(user_answers, selected_grant)
        
        # Временные рамки
        content['timeline'] = self._generate_timeline(user_answers)
        
        # Команда
        content['team'] = self._generate_team_description(user_answers)
        
        # Результат
        content['impact'] = self._generate_impact(user_answers)
        
        # Устойчивость
        content['sustainability'] = self._generate_sustainability(user_answers)
        
        return content
    
    def _generate_title(self, user_answers: Dict, selected_grant: Dict) -> str:
        """Генерация названия проекта"""
        project_type = user_answers.get('project_type', 'проект')
        region = user_answers.get('region', 'региона')
        
        return f"Развитие {project_type} в {region}"
    
    def _generate_summary(self, user_answers: Dict, selected_grant: Dict) -> str:
        """Генерация краткого описания"""
        project_type = user_answers.get('project_type', 'проект')
        budget = user_answers.get('budget', 'необходимую сумму')
        
        return f"""Проект направлен на развитие {project_type} с привлечением 
        финансирования в размере {budget} рублей. Проект будет реализован в течение 
        12 месяцев и принесет значительную пользу региону."""
    
    def _generate_problem_description(self, user_answers: Dict) -> str:
        """Генерация описания проблемы"""
        return """В настоящее время наблюдается недостаток качественных проектов 
        в данной сфере. Существующие решения не полностью удовлетворяют потребности 
        целевой аудитории. Необходимо создание инновационного решения."""
    
    def _generate_solution(self, user_answers: Dict, research_data: Dict) -> str:
        """Генерация описания решения"""
        return """Предлагаемое решение основано на современных технологиях и 
        лучших практиках. Оно позволит эффективно решить выявленные проблемы 
        и создать устойчивую модель развития."""
    
    def _generate_implementation_plan(self, user_answers: Dict) -> str:
        """Генерация плана реализации"""
        return """План реализации включает следующие этапы:
        1. Подготовительный этап (1-2 месяца)
        2. Основной этап реализации (6-8 месяцев)
        3. Завершающий этап (2-3 месяца)
        4. Мониторинг и оценка результатов (1 месяц)"""
    
    def _generate_budget(self, user_answers: Dict, selected_grant: Dict) -> str:
        """Генерация бюджета"""
        budget = user_answers.get('budget', '500 000')
        return f"""Общий бюджет проекта: {budget} рублей
        - Оборудование: 40%
        - Персонал: 30%
        - Маркетинг: 15%
        - Административные расходы: 10%
        - Резерв: 5%"""
    
    def _generate_timeline(self, user_answers: Dict) -> str:
        """Генерация временных рамок"""
        return """Проект рассчитан на 12 месяцев:
        - Месяцы 1-2: Подготовка и планирование
        - Месяцы 3-10: Основная реализация
        - Месяцы 11-12: Завершение и презентация результатов"""
    
    def _generate_team_description(self, user_answers: Dict) -> str:
        """Генерация описания команды"""
        return """Команда проекта состоит из опытных специалистов с профильным 
        образованием и практическим опытом в данной сфере. Руководитель проекта 
        имеет более 5 лет опыта управления подобными проектами."""
    
    def _generate_impact(self, user_answers: Dict) -> str:
        """Генерация ожидаемого результата"""
        return """Ожидаемые результаты проекта:
        - Создание новых рабочих мест
        - Повышение качества услуг
        - Развитие инновационного потенциала региона
        - Увеличение налоговых поступлений"""
    
    def _generate_sustainability(self, user_answers: Dict) -> str:
        """Генерация описания устойчивости"""
        return """Проект имеет долгосрочную перспективу развития. После завершения 
        грантового финансирования проект будет продолжать работать за счет 
        собственных доходов и привлечения дополнительных инвестиций."""
    
    def _check_application_quality(self, application_content: Dict) -> Dict[str, Any]:
        """Проверка качества заявки"""
        score = 0.0
        suggestions = []
        
        # Проверяем полноту
        required_sections = ['title', 'summary', 'problem', 'solution', 'budget']
        for section in required_sections:
            if section in application_content and application_content[section]:
                score += 0.2
            else:
                suggestions.append(f"Дополнить раздел '{section}'")
        
        # Проверяем длину описаний
        for section, content in application_content.items():
            if len(content) < 100:
                suggestions.append(f"Расширить раздел '{section}'")
        
        return {
            'score': min(score, 1.0),
            'suggestions': suggestions
        } 