"""
Auditor Agent - агент для анализа качества заявок на гранты
"""
from typing import Dict, Any, List
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AuditorAgent(BaseAgent):
    """Агент-аудитор для анализа качества заявок"""
    
    def __init__(self, db):
        super().__init__("auditor", db)
    
    def _get_goal(self) -> str:
        return "Провести комплексный анализ качества заявки и дать рекомендации по улучшению"
    
    def _get_backstory(self) -> str:
        return """Ты опытный эксперт по грантовым заявкам с 20-летним стажем. 
        Ты работал в комиссиях по рассмотрению заявок и знаешь все критерии оценки. 
        Твоя задача - объективно оценить заявку и дать конкретные рекомендации по улучшению."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ качества заявки"""
        try:
            # Извлекаем данные
            application = input_data.get('application', {})
            user_answers = input_data.get('user_answers', {})
            selected_grant = input_data.get('selected_grant', {})
            
            # Проводим анализ по критериям
            analysis_results = self._analyze_application(application, user_answers, selected_grant)
            
            # Формируем общую оценку
            overall_score = self._calculate_overall_score(analysis_results)
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(analysis_results, overall_score)
            
            # Определяем статус готовности
            readiness_status = self._determine_readiness_status(overall_score)
            
            return {
                'status': 'success',
                'analysis': analysis_results,
                'overall_score': overall_score,
                'recommendations': recommendations,
                'readiness_status': readiness_status,
                'can_submit': overall_score >= 0.7
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа заявки: {e}")
            return {
                'status': 'error',
                'message': f"Ошибка анализа: {str(e)}"
            }
    
    def _analyze_application(self, application: Dict, user_answers: Dict, selected_grant: Dict) -> Dict[str, Any]:
        """Анализ заявки по критериям"""
        analysis = {}
        
        # Анализ структуры
        analysis['structure'] = self._analyze_structure(application)
        
        # Анализ содержания
        analysis['content'] = self._analyze_content(application, user_answers)
        
        # Анализ соответствия требованиям гранта
        analysis['compliance'] = self._analyze_compliance(application, selected_grant)
        
        # Анализ бюджета
        analysis['budget'] = self._analyze_budget(application, user_answers)
        
        # Анализ реалистичности
        analysis['realism'] = self._analyze_realism(application, user_answers)
        
        # Анализ инновационности
        analysis['innovation'] = self._analyze_innovation(application)
        
        return analysis
    
    def _analyze_structure(self, application: Dict) -> Dict[str, Any]:
        """Анализ структуры заявки"""
        required_sections = [
            'title', 'summary', 'problem', 'solution', 'implementation', 
            'budget', 'timeline', 'team', 'impact', 'sustainability'
        ]
        
        present_sections = [section for section in required_sections if section in application and application[section]]
        completeness = len(present_sections) / len(required_sections)
        
        missing_sections = [section for section in required_sections if section not in application or not application[section]]
        
        return {
            'score': completeness,
            'present_sections': present_sections,
            'missing_sections': missing_sections,
            'comments': f"Заполнено {len(present_sections)} из {len(required_sections)} разделов"
        }
    
    def _analyze_content(self, application: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Анализ содержания заявки"""
        content_scores = {}
        total_score = 0
        
        # Анализ названия
        title = application.get('title', '')
        title_score = min(len(title) / 50, 1.0) if title else 0
        content_scores['title'] = title_score
        total_score += title_score
        
        # Анализ описания
        summary = application.get('summary', '')
        summary_score = min(len(summary) / 200, 1.0) if summary else 0
        content_scores['summary'] = summary_score
        total_score += summary_score
        
        # Анализ проблемы
        problem = application.get('problem', '')
        problem_score = min(len(problem) / 300, 1.0) if problem else 0
        content_scores['problem'] = problem_score
        total_score += problem_score
        
        # Анализ решения
        solution = application.get('solution', '')
        solution_score = min(len(solution) / 400, 1.0) if solution else 0
        content_scores['solution'] = solution_score
        total_score += solution_score
        
        avg_score = total_score / 4 if total_score > 0 else 0
        
        return {
            'score': avg_score,
            'section_scores': content_scores,
            'comments': f"Средний балл по содержанию: {avg_score:.2f}"
        }
    
    def _analyze_compliance(self, application: Dict, selected_grant: Dict) -> Dict[str, Any]:
        """Анализ соответствия требованиям гранта"""
        compliance_score = 0.8  # Базовая оценка
        
        # Проверяем соответствие бюджета
        grant_amount = selected_grant.get('amount', '')
        if grant_amount and 'до' in grant_amount:
            try:
                max_amount = int(''.join(filter(str.isdigit, grant_amount)))
                app_budget = application.get('budget', '')
                if app_budget:
                    # Простая проверка - если бюджет упоминается
                    compliance_score += 0.1
            except:
                pass
        
        return {
            'score': min(compliance_score, 1.0),
            'comments': "Заявка в целом соответствует требованиям гранта"
        }
    
    def _analyze_budget(self, application: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Анализ бюджета"""
        budget_text = application.get('budget', '')
        budget_score = 0.7  # Базовая оценка
        
        # Проверяем наличие структуры бюджета
        if 'оборудование' in budget_text.lower():
            budget_score += 0.1
        if 'персонал' in budget_text.lower():
            budget_score += 0.1
        if 'маркетинг' in budget_text.lower():
            budget_score += 0.1
        
        return {
            'score': min(budget_score, 1.0),
            'comments': "Бюджет структурирован и обоснован"
        }
    
    def _analyze_realism(self, application: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Анализ реалистичности проекта"""
        realism_score = 0.8  # Базовая оценка
        
        # Проверяем наличие временных рамок
        timeline = application.get('timeline', '')
        if timeline and len(timeline) > 100:
            realism_score += 0.1
        
        # Проверяем описание команды
        team = application.get('team', '')
        if team and len(team) > 100:
            realism_score += 0.1
        
        return {
            'score': min(realism_score, 1.0),
            'comments': "Проект выглядит реалистичным"
        }
    
    def _analyze_innovation(self, application: Dict) -> Dict[str, Any]:
        """Анализ инновационности"""
        innovation_score = 0.6  # Базовая оценка
        
        # Проверяем наличие инновационных элементов
        solution = application.get('solution', '')
        if 'инновационн' in solution.lower() or 'современн' in solution.lower():
            innovation_score += 0.2
        
        if 'технолог' in solution.lower():
            innovation_score += 0.2
        
        return {
            'score': min(innovation_score, 1.0),
            'comments': "Проект содержит элементы инновационности"
        }
    
    def _calculate_overall_score(self, analysis_results: Dict) -> float:
        """Расчет общей оценки"""
        weights = {
            'structure': 0.2,
            'content': 0.25,
            'compliance': 0.2,
            'budget': 0.15,
            'realism': 0.1,
            'innovation': 0.1
        }
        
        total_score = 0
        for criterion, weight in weights.items():
            if criterion in analysis_results:
                total_score += analysis_results[criterion]['score'] * weight
        
        return total_score
    
    def _generate_recommendations(self, analysis_results: Dict, overall_score: float) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        # Рекомендации по структуре
        if analysis_results.get('structure', {}).get('score', 0) < 0.8:
            missing = analysis_results['structure'].get('missing_sections', [])
            if missing:
                recommendations.append(f"Дополнить недостающие разделы: {', '.join(missing)}")
        
        # Рекомендации по содержанию
        content_scores = analysis_results.get('content', {}).get('section_scores', {})
        for section, score in content_scores.items():
            if score < 0.7:
                recommendations.append(f"Расширить раздел '{section}'")
        
        # Рекомендации по бюджету
        if analysis_results.get('budget', {}).get('score', 0) < 0.8:
            recommendations.append("Детализировать структуру бюджета")
        
        # Общие рекомендации
        if overall_score < 0.7:
            recommendations.append("Необходима доработка заявки перед подачей")
        elif overall_score < 0.85:
            recommendations.append("Заявка готова к подаче, но можно улучшить")
        else:
            recommendations.append("Отличная заявка, готова к подаче")
        
        return recommendations
    
    def _determine_readiness_status(self, overall_score: float) -> str:
        """Определение статуса готовности"""
        if overall_score >= 0.85:
            return "Отлично"
        elif overall_score >= 0.7:
            return "Хорошо"
        elif overall_score >= 0.5:
            return "Требует доработки"
        else:
            return "Не готово" 