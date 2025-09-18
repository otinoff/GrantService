"""
Auditor Agent - агент для анализа качества заявок на гранты
"""
import sys
import os
from typing import Dict, Any, List
import logging
import asyncio
import time

# Добавляем пути к модулям
sys.path.append('/var/GrantService/shared')
sys.path.append('/var/GrantService/telegram-bot/services')

from base_agent import BaseAgent

try:
    from llm.unified_llm_client import UnifiedLLMClient
    from llm.config import AGENT_CONFIGS
    UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    try:
        from services.llm_router import LLMRouter, LLMProvider
        UNIFIED_CLIENT_AVAILABLE = False
    except ImportError:
        print("⚠️ LLM сервисы недоступны")
        UNIFIED_CLIENT_AVAILABLE = False

logger = logging.getLogger(__name__)

class AuditorAgent(BaseAgent):
    """Агент-аудитор для анализа качества заявок"""
    
    def __init__(self, db, llm_provider: str = "auto"):
        super().__init__("auditor", db, llm_provider)
        
        if UNIFIED_CLIENT_AVAILABLE:
            self.llm_client = UnifiedLLMClient()
            self.config = AGENT_CONFIGS.get("auditor", AGENT_CONFIGS["auditor"])
        else:
            self.llm_router = LLMRouter()
    
    def _get_goal(self) -> str:
        return "Провести комплексный анализ качества заявки и дать рекомендации по улучшению"
    
    def _get_backstory(self) -> str:
        return """Ты опытный эксперт по грантовым заявкам с 20-летним стажем. 
        Ты работал в комиссиях по рассмотрению заявок и знаешь все критерии оценки. 
        Твоя задача - объективно оценить заявку и дать конкретные рекомендации по улучшению."""
    
    async def audit_application_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронный анализ качества заявки"""
        try:
            start_time = time.time()
            self.log_activity("audit_started", {"input_keys": list(input_data.keys())})
            
            # Извлекаем данные
            application = input_data.get('application', {})
            if isinstance(application, str):
                application = self._parse_application_text(application)
            
            user_answers = input_data.get('user_answers', {})
            research_data = input_data.get('research_data', {})
            selected_grant = input_data.get('selected_grant', {})
            
            # Проводим многоуровневый анализ
            analysis_results = await self._analyze_application_comprehensive(
                application, user_answers, research_data, selected_grant
            )
            
            # Формируем общую оценку
            overall_score = self._calculate_overall_score(analysis_results)
            
            # Генерируем рекомендации
            recommendations = self._generate_recommendations(analysis_results, overall_score)
            
            # Определяем статус готовности
            readiness_status = self._determine_readiness_status(overall_score)
            
            # Создаем финальную заявку с улучшениями
            final_application = await self._create_improved_application(
                application, recommendations, analysis_results
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'status': 'success',
                'provider': 'gigachat' if UNIFIED_CLIENT_AVAILABLE else 'router',
                'processing_time': processing_time,
                'analysis': analysis_results,
                'overall_score': overall_score,
                'completeness_score': analysis_results.get('structure', {}).get('score', 0) * 10,
                'quality_score': analysis_results.get('content', {}).get('score', 0) * 10,
                'compliance_score': analysis_results.get('compliance', {}).get('score', 0) * 10,
                'recommendations': recommendations,
                'readiness_status': readiness_status,
                'can_submit': overall_score >= 0.7,
                'final_application': final_application,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.log_activity("audit_completed", {
                "overall_score": overall_score,
                "readiness_status": readiness_status,
                "processing_time": processing_time
            })
            
            return self.prepare_output(result)
            
        except Exception as e:
            logger.error(f"Ошибка анализа заявки: {e}")
            return self.handle_error(e, "audit_application_async")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронная обертка для совместимости"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.audit_application_async(input_data))
        except RuntimeError:
            # Если нет активного event loop, создаем новый
            return asyncio.run(self.audit_application_async(input_data))
    
    async def _analyze_application_comprehensive(self, application: Dict, user_answers: Dict, 
                                              research_data: Dict, selected_grant: Dict) -> Dict[str, Any]:
        """Комплексный анализ заявки"""
        analysis = {}
        
        # Параллельно запускаем разные виды анализа
        tasks = []
        
        # Структурный анализ (быстрый, без LLM)
        analysis['structure'] = self._analyze_structure(application)
        
        # Анализ содержания (быстрый, без LLM)
        analysis['content'] = self._analyze_content(application, user_answers)
        
        # Анализ соответствия требованиям (быстрый, без LLM)
        analysis['compliance'] = self._analyze_compliance(application, selected_grant)
        
        # Анализ бюджета (быстрый, без LLM)
        analysis['budget'] = self._analyze_budget(application, user_answers)
        
        # LLM-анализы (асинхронно)
        if UNIFIED_CLIENT_AVAILABLE:
            tasks.extend([
                self._analyze_with_llm_completeness(application),
                self._analyze_with_llm_quality(application, research_data),
                self._analyze_with_llm_compliance(application, selected_grant),
                self._analyze_with_llm_innovation(application)
            ])
            
            # Запускаем LLM задачи параллельно
            llm_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            analysis['llm_completeness'] = llm_results[0] if len(llm_results) > 0 and not isinstance(llm_results[0], Exception) else {'score': 0.7, 'comments': 'LLM анализ недоступен'}
            analysis['llm_quality'] = llm_results[1] if len(llm_results) > 1 and not isinstance(llm_results[1], Exception) else {'score': 0.7, 'comments': 'LLM анализ недоступен'}
            analysis['llm_compliance'] = llm_results[2] if len(llm_results) > 2 and not isinstance(llm_results[2], Exception) else {'score': 0.7, 'comments': 'LLM анализ недоступен'}
            analysis['llm_innovation'] = llm_results[3] if len(llm_results) > 3 and not isinstance(llm_results[3], Exception) else {'score': 0.7, 'comments': 'LLM анализ недоступен'}
        else:
            # Fallback на старую логику без LLM
            analysis['realism'] = self._analyze_realism(application, user_answers)
            analysis['innovation'] = self._analyze_innovation(application)
        
        return analysis
    
    async def _analyze_with_llm_completeness(self, application: Dict) -> Dict[str, Any]:
        """LLM анализ полноты заявки"""
        try:
            prompt = self.format_prompt("Проверка полноты", {
                'application_text': self._format_application_for_analysis(application)
            })
            
            if not prompt:
                # Fallback промпт
                prompt = f"""Проанализируй полноту следующей заявки на грант:

{self._format_application_for_analysis(application)}

Оцени по шкале 1-10:
1. Наличие всех необходимых разделов
2. Детальность описания
3. Четкость формулировок

Дай оценку и краткие комментарии."""
            
            response = await self.llm_client.generate_async(
                prompt,
                provider="gigachat",
                **self.config
            )
            
            score = self._extract_score_from_text(response)
            
            return {
                'score': score,
                'analysis': response,
                'comments': f"LLM оценка полноты: {score:.1f}/10"
            }
            
        except Exception as e:
            logger.error(f"Ошибка LLM анализа полноты: {e}")
            return {'score': 0.7, 'comments': f'Ошибка LLM анализа: {str(e)}'}
    
    async def _analyze_with_llm_quality(self, application: Dict, research_data: Dict) -> Dict[str, Any]:
        """LLM анализ качества содержания"""
        try:
            prompt = self.format_prompt("Оценка качества", {
                'application_text': self._format_application_for_analysis(application),
                'research_data': str(research_data)
            })
            
            if not prompt:
                # Fallback промпт
                prompt = f"""Оцени качество содержания заявки на грант:

ЗАЯВКА:
{self._format_application_for_analysis(application)}

ДАННЫЕ ИССЛЕДОВАНИЯ:
{str(research_data)}

Оцени по шкале 1-10:
1. Качество изложения
2. Логичность структуры
3. Убедительность аргументов
4. Соответствие данным исследования

Дай оценку и рекомендации."""
            
            response = await self.llm_client.generate_async(
                prompt,
                provider="gigachat",
                **self.config
            )
            
            score = self._extract_score_from_text(response)
            
            return {
                'score': score,
                'analysis': response,
                'comments': f"LLM оценка качества: {score:.1f}/10"
            }
            
        except Exception as e:
            logger.error(f"Ошибка LLM анализа качества: {e}")
            return {'score': 0.7, 'comments': f'Ошибка LLM анализа: {str(e)}'}
    
    async def _analyze_with_llm_compliance(self, application: Dict, selected_grant: Dict) -> Dict[str, Any]:
        """LLM анализ соответствия требованиям"""
        try:
            grant_criteria = self._format_grant_criteria(selected_grant)
            
            prompt = self.format_prompt("Соответствие требованиям", {
                'application_text': self._format_application_for_analysis(application),
                'grant_criteria': grant_criteria
            })
            
            if not prompt:
                # Fallback промпт
                prompt = f"""Проанализируй соответствие заявки требованиям гранта:

ЗАЯВКА:
{self._format_application_for_analysis(application)}

ТРЕБОВАНИЯ ГРАНТА:
{grant_criteria}

Оцени по шкале 1-10:
1. Соответствие тематике гранта
2. Соответствие бюджетным ограничениям
3. Соответствие срокам реализации
4. Выполнение формальных требований

Дай оценку и укажи несоответствия."""
            
            response = await self.llm_client.generate_async(
                prompt,
                provider="gigachat",
                **self.config
            )
            
            score = self._extract_score_from_text(response)
            
            return {
                'score': score,
                'analysis': response,
                'comments': f"LLM оценка соответствия: {score:.1f}/10"
            }
            
        except Exception as e:
            logger.error(f"Ошибка LLM анализа соответствия: {e}")
            return {'score': 0.7, 'comments': f'Ошибка LLM анализа: {str(e)}'}
    
    async def _analyze_with_llm_innovation(self, application: Dict) -> Dict[str, Any]:
        """LLM анализ инновационности"""
        try:
            response = await self.llm_client.generate_async(
                f"""Оцени инновационность проекта:

{self._format_application_for_analysis(application)}

Оцени по шкале 1-10:
1. Новизна подхода
2. Технологическую инновационность
3. Потенциал влияния
4. Уникальность решения

Дай оценку и обоснование.""",
                provider="gigachat",
                **self.config
            )
            
            score = self._extract_score_from_text(response)
            
            return {
                'score': score,
                'analysis': response,
                'comments': f"LLM оценка инновационности: {score:.1f}/10"
            }
            
        except Exception as e:
            logger.error(f"Ошибка LLM анализа инновационности: {e}")
            return {'score': 0.6, 'comments': f'Ошибка LLM анализа: {str(e)}'}
    
    async def _create_improved_application(self, application: Dict, recommendations: List[str], 
                                         analysis_results: Dict) -> Dict[str, Any]:
        """Создание улучшенной версии заявки"""
        try:
            if not UNIFIED_CLIENT_AVAILABLE or not recommendations:
                return application
            
            improvement_prompt = f"""На основе анализа заявки и рекомендаций, создай улучшенную версию:

ИСХОДНАЯ ЗАЯВКА:
{self._format_application_for_analysis(application)}

РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:
{chr(10).join([f"- {rec}" for rec in recommendations])}

АНАЛИЗ КАЧЕСТВА:
- Структура: {analysis_results.get('structure', {}).get('score', 0):.2f}
- Содержание: {analysis_results.get('content', {}).get('score', 0):.2f}

Создай улучшенную версию заявки, учитывающую все рекомендации."""
            
            improved_text = await self.llm_client.generate_async(
                improvement_prompt,
                provider="gigachat",
                max_tokens=3000,
                temperature=0.3
            )
            
            return {
                'improved_text': improved_text,
                'status': 'improved',
                'improvement_basis': recommendations,
                'confidence_score': min(analysis_results.get('llm_quality', {}).get('score', 0.7) + 0.2, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания улучшенной заявки: {e}")
            return application
    
    def _parse_application_text(self, text: str) -> Dict[str, str]:
        """Парсинг текста заявки в структуру"""
        # Простой парсер для преобразования текста в структуру
        sections = {
            'title': '',
            'summary': '',
            'problem': '',
            'solution': '',
            'implementation': '',
            'budget': '',
            'timeline': '',
            'team': '',
            'impact': ''
        }
        
        # Ищем ключевые разделы в тексте
        lines = text.split('\n')
        current_section = 'summary'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Определяем раздел по ключевым словам
            line_lower = line.lower()
            if any(word in line_lower for word in ['название', 'заголовок', 'title']):
                current_section = 'title'
            elif any(word in line_lower for word in ['проблема', 'problem']):
                current_section = 'problem'
            elif any(word in line_lower for word in ['решение', 'solution']):
                current_section = 'solution'
            elif any(word in line_lower for word in ['бюджет', 'budget', 'финансы']):
                current_section = 'budget'
            elif any(word in line_lower for word in ['команда', 'team']):
                current_section = 'team'
            elif any(word in line_lower for word in ['план', 'timeline', 'этапы']):
                current_section = 'timeline'
            else:
                sections[current_section] += line + ' '
        
        return sections
    
    def _analyze_structure(self, application: Dict) -> Dict[str, Any]:
        """Анализ структуры заявки"""
        required_sections = [
            'title', 'summary', 'problem', 'solution', 'implementation', 
            'budget', 'timeline', 'team', 'impact', 'sustainability'
        ]
        
        present_sections = []
        for section in required_sections:
            if section in application and application[section] and len(str(application[section]).strip()) > 10:
                present_sections.append(section)
        
        completeness = len(present_sections) / len(required_sections)
        missing_sections = [section for section in required_sections if section not in present_sections]
        
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
        sections_checked = 0
        
        # Анализ основных разделов
        sections_to_check = {
            'title': {'min_length': 20, 'max_length': 100, 'weight': 0.1},
            'summary': {'min_length': 100, 'max_length': 500, 'weight': 0.2},
            'problem': {'min_length': 150, 'max_length': 800, 'weight': 0.2},
            'solution': {'min_length': 200, 'max_length': 1000, 'weight': 0.25},
            'budget': {'min_length': 50, 'max_length': 500, 'weight': 0.15},
            'timeline': {'min_length': 100, 'max_length': 500, 'weight': 0.1}
        }
        
        for section, criteria in sections_to_check.items():
            if section in application and application[section]:
                text = str(application[section]).strip()
                length = len(text)
                
                # Оценка по длине и структуре
                if length >= criteria['min_length']:
                    length_score = min(length / criteria['max_length'], 1.0)
                    # Бонус за структурированность (наличие списков, абзацев)
                    structure_bonus = 0.1 if any(marker in text for marker in ['-', '•', '1.', '2.', '\n\n']) else 0
                    section_score = min(length_score + structure_bonus, 1.0)
                else:
                    section_score = length / criteria['min_length']
                
                content_scores[section] = section_score
                total_score += section_score * criteria['weight']
                sections_checked += criteria['weight']
            else:
                content_scores[section] = 0
        
        avg_score = total_score / sections_checked if sections_checked > 0 else 0
        
        return {
            'score': avg_score,
            'section_scores': content_scores,
            'comments': f"Средний балл по содержанию: {avg_score:.2f}"
        }
    
    def _analyze_compliance(self, application: Dict, selected_grant: Dict) -> Dict[str, Any]:
        """Анализ соответствия требованиям гранта"""
        compliance_score = 0.5  # Базовая оценка
        compliance_factors = []
        
        # Проверяем соответствие бюджета
        if selected_grant.get('amount'):
            grant_amount_str = str(selected_grant['amount'])
            app_budget = str(application.get('budget', ''))
            
            if app_budget and any(char.isdigit() for char in app_budget):
                compliance_score += 0.2
                compliance_factors.append("Бюджет указан")
                
                # Попытка извлечь числовые значения для сравнения
                import re
                app_numbers = re.findall(r'\d+', app_budget)
                grant_numbers = re.findall(r'\d+', grant_amount_str)
                
                if app_numbers and grant_numbers:
                    try:
                        app_amount = int(''.join(app_numbers[:2]))  # Первые два числа
                        grant_max = int(''.join(grant_numbers[-1:]))  # Последнее число
                        
                        if app_amount <= grant_max:
                            compliance_score += 0.2
                            compliance_factors.append("Бюджет в пределах гранта")
                    except:
                        pass
        
        # Проверяем тематическое соответствие
        if selected_grant.get('requirements'):
            requirements = str(selected_grant['requirements']).lower()
            app_text = ' '.join([str(v) for v in application.values()]).lower()
            
            # Простое совпадение ключевых слов
            key_matches = 0
            req_words = requirements.split()[:10]  # Первые 10 слов требований
            
            for word in req_words:
                if len(word) > 3 and word in app_text:
                    key_matches += 1
            
            if key_matches > 0:
                theme_score = min(key_matches / len(req_words), 0.3)
                compliance_score += theme_score
                compliance_factors.append(f"Тематическое соответствие: {key_matches} совпадений")
        
        return {
            'score': min(compliance_score, 1.0),
            'factors': compliance_factors,
            'comments': f"Соответствие требованиям: {compliance_score:.2f}"
        }
    
    def _analyze_budget(self, application: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Анализ бюджета"""
        budget_text = str(application.get('budget', '')).lower()
        budget_score = 0.3  # Базовая оценка
        budget_factors = []
        
        if not budget_text or len(budget_text) < 20:
            return {
                'score': 0.1,
                'factors': ["Бюджет отсутствует или слишком краткий"],
                'comments': "Требуется детализация бюджета"
            }
        
        # Проверяем структуру бюджета
        structure_keywords = [
            ('персонал', 'зарплата', 'оплата труда'),
            ('оборудование', 'закупки', 'материалы'),
            ('операционные', 'расходы', 'услуги'),
            ('маркетинг', 'продвижение', 'реклама')
        ]
        
        for keyword_group in structure_keywords:
            if any(keyword in budget_text for keyword in keyword_group):
                budget_score += 0.15
                budget_factors.append(f"Указаны расходы на {keyword_group[0]}")
        
        # Проверяем наличие конкретных сумм
        import re
        numbers = re.findall(r'\d+', budget_text)
        if len(numbers) >= 3:
            budget_score += 0.1
            budget_factors.append("Указаны конкретные суммы")
        
        # Проверяем обоснование
        justification_words = ['потому что', 'так как', 'обосновано', 'необходимо', 'требуется']
        if any(word in budget_text for word in justification_words):
            budget_score += 0.1
            budget_factors.append("Есть обоснование расходов")
        
        return {
            'score': min(budget_score, 1.0),
            'factors': budget_factors,
            'comments': f"Анализ бюджета: {budget_score:.2f}"
        }
    
    def _analyze_realism(self, application: Dict, user_answers: Dict) -> Dict[str, Any]:
        """Анализ реалистичности проекта (fallback без LLM)"""
        realism_score = 0.6  # Базовая оценка
        realism_factors = []
        
        # Проверяем наличие временных рамок
        timeline = str(application.get('timeline', ''))
        if timeline and len(timeline) > 50:
            realism_score += 0.15
            realism_factors.append("Указаны временные рамки")
            
            # Проверяем детализацию этапов
            if any(word in timeline.lower() for word in ['этап', 'месяц', 'квартал', 'фаза']):
                realism_score += 0.1
                realism_factors.append("Детализированы этапы")
        
        # Проверяем описание команды
        team = str(application.get('team', ''))
        if team and len(team) > 50:
            realism_score += 0.15
            realism_factors.append("Описана команда")
            
            # Проверяем указание ролей и опыта
            if any(word in team.lower() for word in ['опыт', 'роль', 'специалист', 'менеджер']):
                realism_score += 0.1
                realism_factors.append("Указаны роли и опыт")
        
        return {
            'score': min(realism_score, 1.0),
            'factors': realism_factors,
            'comments': f"Оценка реалистичности: {realism_score:.2f}"
        }
    
    def _analyze_innovation(self, application: Dict) -> Dict[str, Any]:
        """Анализ инновационности (fallback без LLM)"""
        innovation_score = 0.4  # Базовая оценка
        innovation_factors = []
        
        # Объединяем весь текст заявки
        full_text = ' '.join([str(v) for v in application.values()]).lower()
        
        # Проверяем инновационные ключевые слова
        innovation_keywords = [
            'инновационн', 'современн', 'новейш', 'уникальн', 'передов',
            'технолог', 'цифров', 'автоматизац', 'искусственн', 'машинн'
        ]
        
        found_keywords = [keyword for keyword in innovation_keywords if keyword in full_text]
        
        if found_keywords:
            keyword_score = min(len(found_keywords) * 0.1, 0.4)
            innovation_score += keyword_score
            innovation_factors.append(f"Упоминаются инновационные аспекты: {', '.join(found_keywords[:3])}")
        
        # Проверяем наличие технических деталей
        tech_words = ['алгоритм', 'платформа', 'система', 'приложение', 'программа', 'сервис']
        tech_found = [word for word in tech_words if word in full_text]
        
        if tech_found:
            innovation_score += 0.2
            innovation_factors.append("Содержит технические решения")
        
        return {
            'score': min(innovation_score, 1.0),
            'factors': innovation_factors,
            'comments': f"Оценка инновационности: {innovation_score:.2f}"
        }
    
    def _calculate_overall_score(self, analysis_results: Dict) -> float:
        """Расчет общей оценки"""
        if UNIFIED_CLIENT_AVAILABLE and 'llm_completeness' in analysis_results:
            # Новые веса с учетом LLM анализа
            weights = {
                'structure': 0.15,
                'content': 0.20,
                'compliance': 0.15,
                'budget': 0.10,
                'llm_completeness': 0.15,
                'llm_quality': 0.15,
                'llm_compliance': 0.05,
                'llm_innovation': 0.05
            }
        else:
            # Старые веса для fallback
            weights = {
                'structure': 0.25,
                'content': 0.30,
                'compliance': 0.20,
                'budget': 0.15,
                'realism': 0.05,
                'innovation': 0.05
            }
        
        total_score = 0
        total_weight = 0
        
        for criterion, weight in weights.items():
            if criterion in analysis_results and 'score' in analysis_results[criterion]:
                total_score += analysis_results[criterion]['score'] * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _generate_recommendations(self, analysis_results: Dict, overall_score: float) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        # Рекомендации по структуре
        structure_analysis = analysis_results.get('structure', {})
        if structure_analysis.get('score', 0) < 0.8:
            missing = structure_analysis.get('missing_sections', [])
            if missing:
                recommendations.append(f"Дополнить недостающие разделы: {', '.join(missing[:3])}")
        
        # Рекомендации по содержанию
        content_analysis = analysis_results.get('content', {})
        section_scores = content_analysis.get('section_scores', {})
        weak_sections = [section for section, score in section_scores.items() if score < 0.6]
        
        if weak_sections:
            recommendations.append(f"Усилить разделы: {', '.join(weak_sections[:3])}")
        
        # Рекомендации по бюджету
        budget_analysis = analysis_results.get('budget', {})
        if budget_analysis.get('score', 0) < 0.7:
            recommendations.append("Детализировать структуру бюджета с обоснованием расходов")
        
        # Рекомендации по соответствию
        compliance_analysis = analysis_results.get('compliance', {})
        if compliance_analysis.get('score', 0) < 0.7:
            recommendations.append("Усилить соответствие требованиям гранта")
        
        # LLM рекомендации
        if UNIFIED_CLIENT_AVAILABLE:
            for key in ['llm_completeness', 'llm_quality', 'llm_compliance']:
                analysis = analysis_results.get(key, {})
                if analysis.get('score', 0) < 0.7 and 'analysis' in analysis:
                    # Извлекаем рекомендации из LLM анализа
                    llm_recommendations = self._extract_recommendations_from_text(analysis['analysis'])
                    recommendations.extend(llm_recommendations[:2])  # Максимум 2 от каждого LLM анализа
        
        # Общие рекомендации
        if overall_score < 0.5:
            recommendations.append("⚠️ Заявка требует существенной доработки")
        elif overall_score < 0.7:
            recommendations.append("📝 Заявка нуждается в улучшениях перед подачей")
        elif overall_score < 0.85:
            recommendations.append("✅ Заявка готова к подаче с небольшими улучшениями")
        else:
            recommendations.append("🏆 Отличная заявка, готова к подаче")
        
        return recommendations[:7]  # Ограничиваем количество рекомендаций
    
    def _determine_readiness_status(self, overall_score: float) -> str:
        """Определение статуса готовности"""
        if overall_score >= 0.9:
            return "Отлично"
        elif overall_score >= 0.75:
            return "Хорошо"
        elif overall_score >= 0.6:
            return "Удовлетворительно"
        elif overall_score >= 0.4:
            return "Требует доработки"
        else:
            return "Не готово"
    
    def _format_application_for_analysis(self, application: Dict) -> str:
        """Форматирование заявки для анализа"""
        sections = []
        
        section_titles = {
            'title': 'НАЗВАНИЕ',
            'summary': 'РЕЗЮМЕ',
            'problem': 'ПРОБЛЕМА',
            'solution': 'РЕШЕНИЕ',
            'implementation': 'РЕАЛИЗАЦИЯ',
            'budget': 'БЮДЖЕТ',
            'timeline': 'ПЛАН РЕАЛИЗАЦИИ',
            'team': 'КОМАНДА',
            'impact': 'ОЖИДАЕМОЕ ВЛИЯНИЕ'
        }
        
        for key, title in section_titles.items():
            if key in application and application[key]:
                sections.append(f"{title}: {application[key]}")
        
        return "\n\n".join(sections)
    
    def _format_grant_criteria(self, selected_grant: Dict) -> str:
        """Форматирование критериев гранта"""
        criteria = []
        
        if selected_grant.get('name'):
            criteria.append(f"Название гранта: {selected_grant['name']}")
        
        if selected_grant.get('requirements'):
            criteria.append(f"Требования: {selected_grant['requirements']}")
            
        if selected_grant.get('amount'):
            criteria.append(f"Максимальная сумма: {selected_grant['amount']}")
            
        if selected_grant.get('deadline'):
            criteria.append(f"Срок подачи: {selected_grant['deadline']}")
        
        if selected_grant.get('criteria'):
            criteria.append(f"Критерии оценки: {selected_grant['criteria']}")
        
        return "\n".join(criteria) if criteria else "Критерии гранта не указаны"
    
    def _extract_score_from_text(self, text: str) -> float:
        """Извлечение оценки из текста LLM"""
        try:
            import re
            
            # Ищем различные паттерны оценок
            patterns = [
                r'(\d+(?:\.\d+)?)/10',  # X/10
                r'(\d+(?:\.\d+)?)\s*из\s*10',  # X из 10
                r'оценка[:\s]*(\d+(?:\.\d+)?)',  # оценка: X
                r'балл[:\s]*(\d+(?:\.\d+)?)',  # балл: X
                r'(\d+(?:\.\d+)?)\s*балл',  # X балл
                r'(\d+(?:\.\d+)?)\s*очков',  # X очков
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text.lower())
                if matches:
                    try:
                        score = float(matches[-1])  # Берем последнее найденное значение
                        # Нормализуем к диапазону 0-1
                        if score <= 1.0:
                            return score
                        elif score <= 10.0:
                            return score / 10.0
                        elif score <= 100.0:
                            return score / 100.0
                    except ValueError:
                        continue
            
            # Если не нашли числовую оценку, ищем качественные оценки
            if any(word in text.lower() for word in ['отлично', 'превосходно', 'великолепно']):
                return 0.9
            elif any(word in text.lower() for word in ['хорошо', 'качественно', 'удачно']):
                return 0.8
            elif any(word in text.lower() for word in ['удовлетворительно', 'нормально', 'неплохо']):
                return 0.7
            elif any(word in text.lower() for word in ['слабо', 'недостаточно', 'плохо']):
                return 0.5
            elif any(word in text.lower() for word in ['очень плохо', 'неприемлемо', 'критично']):
                return 0.3
            
            # Базовая оценка, если ничего не найдено
            return 0.7
            
        except Exception:
            return 0.7
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Извлечение рекомендаций из текста LLM"""
        try:
            recommendations = []
            lines = text.split('\n')
            in_recommendations = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Ищем начало раздела с рекомендациями
                if any(keyword in line.lower() for keyword in [
                    'рекомендации', 'рекомендуется', 'предложения', 'советы',
                    'улучшения', 'доработки', 'предлагаю'
                ]):
                    in_recommendations = True
                    continue
                
                # Если мы в разделе рекомендаций
                if in_recommendations and line:
                    # Ищем строки, которые выглядят как рекомендации
                    if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                        clean_rec = line.lstrip('-•*0123456789. ').strip()
                        if len(clean_rec) > 10:  # Игнорируем слишком короткие
                            recommendations.append(clean_rec)
                    elif len(line) > 15 and not line.isupper():
                        recommendations.append(line)
                
                # Останавливаемся если встретили новый раздел
                if in_recommendations and line.isupper() and len(line) > 10:
                    break
            
            return recommendations[:3]  # Максимум 3 рекомендации из одного анализа
            
        except Exception:
            return []

    # Методы для совместимости с Web Admin
    def audit_application(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Совместимость с существующим интерфейсом"""
        return self.process(input_data)


