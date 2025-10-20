#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage Report Generator - генерация PDF отчетов для каждого этапа грантового workflow

Поддерживаемые этапы:
- Interview (Анкета пользователя - 24 Q&A)
- Audit (Результаты аудита проекта)
- Research (Исследование - 27 queries)
- Grant (Финальная грантовая заявка)
- Review (Заключение ревьювера)
"""

import logging
import io
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class StageReportGenerator:
    """Генератор PDF отчетов для этапов грантового workflow"""

    def __init__(self):
        """Инициализация генератора"""
        self.font_name = self._register_russian_font()

    def _register_russian_font(self) -> str:
        """
        Регистрация русского шрифта для PDF

        Returns:
            Имя зарегистрированного шрифта
        """
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Попытка 1: Windows Arial (лучшая поддержка кириллицы на Windows)
            try:
                arial_path = r'C:\Windows\Fonts\arial.ttf'
                pdfmetrics.registerFont(TTFont('Arial', arial_path))
                logger.info("✅ Зарегистрирован шрифт Arial (Windows)")
                return 'Arial'
            except:
                pass

            # Попытка 2: DejaVu Sans
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                logger.info("✅ Зарегистрирован шрифт DejaVuSans")
                return 'DejaVuSans'
            except:
                pass

            # Fallback: Helvetica (без русских букв, но работает)
            logger.warning("⚠️ Русские шрифты не найдены, используется Helvetica (кириллица может не работать)")
            return 'Helvetica'

        except ImportError:
            logger.error("❌ ReportLab не установлен")
            return 'Helvetica'

    def _create_pdf_document(self, title: str) -> tuple:
        """
        Создать базовый PDF документ с настройками

        Args:
            title: Заголовок документа

        Returns:
            Tuple[SimpleDocTemplate, BytesIO, styles]
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.lib.units import cm

        # Буфер для PDF
        buffer = io.BytesIO()

        # Документ
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Стили
        styles = getSampleStyleSheet()

        # Кастомные стили
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=12
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=self.font_name,
            fontSize=14,
            spaceAfter=6
        )

        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontName=self.font_name,
            fontSize=12,
            spaceAfter=4
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=6
        )

        bold_style = ParagraphStyle(
            'CustomBold',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=4
        )

        small_style = ParagraphStyle(
            'CustomSmall',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=8,
            spaceAfter=3
        )

        custom_styles = {
            'title': title_style,
            'heading': heading_style,
            'subheading': subheading_style,
            'normal': normal_style,
            'bold': bold_style,
            'small': small_style
        }

        return doc, buffer, custom_styles

    def _add_footer(self, story: List, styles: Dict):
        """
        Добавить футер к PDF

        Args:
            story: Список элементов PDF
            styles: Словарь стилей
        """
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import cm

        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"Документ создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['small']
        ))
        story.append(Paragraph(
            "GrantService - AI-Powered Grant Application System",
            styles['small']
        ))

    def generate_interview_pdf(self, anketa_data: Dict[str, Any]) -> bytes:
        """
        Генерация PDF с анкетой пользователя (24 Q&A)

        Args:
            anketa_data: Данные анкеты
                {
                    'anketa_id': str,
                    'username': str,
                    'first_name': str,
                    'last_name': str,
                    'telegram_id': int,
                    'created_at': str,
                    'questions_answers': [
                        {'question_id': int, 'question_text': str, 'answer': str},
                        ...
                    ]
                }

        Returns:
            Байты PDF документа
        """
        try:
            from reportlab.platypus import Paragraph, Spacer, PageBreak
            from reportlab.lib.units import cm

            # Создание документа
            doc, buffer, styles = self._create_pdf_document("АНКЕТА ПОЛЬЗОВАТЕЛЯ")

            # Контент
            story = []

            # Заголовок
            story.append(Paragraph("📝 АНКЕТА ПОЛЬЗОВАТЕЛЯ", styles['title']))
            story.append(Spacer(1, 0.5*cm))

            # Metadata
            anketa_id = anketa_data.get('anketa_id', 'N/A')
            username = anketa_data.get('username', 'Unknown')
            first_name = anketa_data.get('first_name', '')
            last_name = anketa_data.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip() or "Unknown"
            telegram_id = anketa_data.get('telegram_id', 'N/A')
            created_at = anketa_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            story.append(Paragraph(f"<b>ID Анкеты:</b> {anketa_id}", styles['normal']))
            story.append(Paragraph(f"<b>Пользователь:</b> {full_name} (@{username})", styles['normal']))
            story.append(Paragraph(f"<b>Telegram ID:</b> {telegram_id}", styles['normal']))
            story.append(Paragraph(f"<b>Дата заполнения:</b> {created_at}", styles['normal']))
            story.append(Spacer(1, 1*cm))

            # Вопросы и ответы
            story.append(Paragraph("ОТВЕТЫ НА ВОПРОСЫ", styles['heading']))
            story.append(Spacer(1, 0.3*cm))

            questions_answers = anketa_data.get('questions_answers', [])
            for qa in questions_answers:
                question_id = qa.get('question_id', '?')
                question_text = qa.get('question_text', '')
                answer = qa.get('answer', 'Нет ответа')

                story.append(Paragraph(f"<b>Вопрос {question_id}:</b> {question_text}", styles['bold']))
                story.append(Paragraph(f"<b>Ответ:</b> {answer}", styles['normal']))
                story.append(Spacer(1, 0.5*cm))

            # Футер
            self._add_footer(story, styles)

            # Генерация PDF
            doc.build(story)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"✅ Interview PDF создан: {len(pdf_bytes)} байт")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации Interview PDF: {e}")
            return self._generate_fallback_text(anketa_data, "АНКЕТА").encode('utf-8')

    def generate_audit_pdf(self, audit_data: Dict[str, Any]) -> bytes:
        """
        Генерация PDF с результатами аудита (детальный отчёт)

        Args:
            audit_data: Данные аудита
                {
                    'anketa_id': str,
                    'average_score': float,  # средний балл
                    'approval_status': str,  # approved/rejected
                    'completeness_score': int,
                    'clarity_score': int,
                    'feasibility_score': int,
                    'innovation_score': int,
                    'quality_score': int,
                    'strengths': list,  # сильные стороны
                    'improvements': list,  # рекомендации
                    'completed_at': str
                }

        Returns:
            Байты PDF документа
        """
        try:
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.units import cm

            doc, buffer, styles = self._create_pdf_document("ОТЧЁТ АУДИТА ПРОЕКТНОЙ ЗАЯВКИ")
            story = []

            # Заголовок
            story.append(Paragraph("Отчёт аудита проектной заявки", styles['title']))
            story.append(Spacer(1, 0.5*cm))

            # Metadata
            anketa_id = audit_data.get('anketa_id', 'N/A')
            avg_score = audit_data.get('average_score', 0)
            status = audit_data.get('approval_status', 'N/A')
            completed_at = audit_data.get('completed_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            status_emoji = "✅ ОДОБРЕНО" if status == 'approved' else "⚠️ ТРЕБУЕТ ДОРАБОТКИ"

            story.append(Paragraph(f"<b>Анкета:</b> {anketa_id}", styles['normal']))
            story.append(Paragraph(f"<b>Дата аудита:</b> {completed_at}", styles['normal']))
            story.append(Paragraph(f"<b>Статус:</b> {status_emoji} ({status})", styles['normal']))
            story.append(Spacer(1, 0.5*cm))

            # Общая оценка
            story.append(Paragraph("Общая оценка", styles['heading']))
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(f"<b>Средний балл:</b> {avg_score:.2f} / 10.00", styles['normal']))

            conclusion = "Проект получил высокую оценку и рекомендован к реализации." if status == 'approved' else "Проект требует доработки перед реализацией."
            story.append(Paragraph(conclusion, styles['normal']))
            story.append(Spacer(1, 0.5*cm))

            # Детальные оценки
            story.append(Paragraph("Детальные оценки", styles['heading']))
            story.append(Spacer(1, 0.3*cm))

            criteria = [
                ('Полнота заявки (Completeness)', audit_data.get('completeness_score', 0), 'Заявка содержит все необходимые компоненты для оценки проекта.'),
                ('Ясность изложения (Clarity)', audit_data.get('clarity_score', 0), 'Цели, задачи и методы реализации проекта изложены четко и понятно.'),
                ('Реалистичность (Feasibility)', audit_data.get('feasibility_score', 0), 'Проект реалистичен для реализации с учетом имеющихся ресурсов и сроков.'),
                ('Инновационность (Innovation)', audit_data.get('innovation_score', 0), 'Проект демонстрирует оригинальный подход и инновационные решения.'),
                ('Качество проработки (Quality)', audit_data.get('quality_score', 0), 'Высокое качество проработки всех аспектов проекта.')
            ]

            for i, (name, score, comment) in enumerate(criteria, 1):
                story.append(Paragraph(f"<b>{i}. {name}</b>", styles['subheading']))
                story.append(Paragraph(f"<b>Оценка:</b> {score} / 10", styles['normal']))
                story.append(Paragraph(comment, styles['normal']))
                story.append(Spacer(1, 0.3*cm))

            # Сильные стороны
            strengths = audit_data.get('strengths', [])
            if strengths:
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph("Сильные стороны проекта", styles['heading']))
                story.append(Spacer(1, 0.3*cm))

                for i, strength in enumerate(strengths, 1):
                    if isinstance(strength, dict):
                        title = strength.get('title', f'Пункт {i}')
                        text = strength.get('text', '')
                    else:
                        # Если это строка, пытаемся разделить на заголовок и текст
                        parts = str(strength).split('\n', 1)
                        title = parts[0] if len(parts) > 0 else f'Пункт {i}'
                        text = parts[1] if len(parts) > 1 else ''

                    story.append(Paragraph(f"<b>{i}. {title}</b>", styles['bold']))
                    if text:
                        story.append(Paragraph(f"   {text}", styles['normal']))
                    story.append(Spacer(1, 0.2*cm))

            # Рекомендации по улучшению
            improvements = audit_data.get('improvements', [])
            if improvements:
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph("Рекомендации по улучшению", styles['heading']))
                story.append(Spacer(1, 0.3*cm))

                for i, improvement in enumerate(improvements, 1):
                    if isinstance(improvement, dict):
                        title = improvement.get('title', f'Рекомендация {i}')
                        text = improvement.get('text', '')
                    else:
                        parts = str(improvement).split('\n', 1)
                        title = parts[0] if len(parts) > 0 else f'Рекомендация {i}'
                        text = parts[1] if len(parts) > 1 else ''

                    story.append(Paragraph(f"<b>{i}. {title}</b>", styles['bold']))
                    if text:
                        story.append(Paragraph(f"   {text}", styles['normal']))
                    story.append(Spacer(1, 0.2*cm))

            # Заключение
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("Заключение", styles['heading']))
            story.append(Spacer(1, 0.3*cm))

            final_status = "ОДОБРЕН" if status == 'approved' else "ТРЕБУЕТ ДОРАБОТКИ"
            story.append(Paragraph(f"Проект <b>{final_status}</b> к реализации.", styles['normal']))
            story.append(Spacer(1, 0.2*cm))

            quality_text = "высоком качестве" if avg_score >= 8 else "удовлетворительном качестве" if avg_score >= 6 else "недостаточном качестве"
            story.append(Paragraph(f"Средний балл <b>{avg_score:.2f}</b> свидетельствует о {quality_text} заявки.", styles['normal']))

            if status == 'approved':
                story.append(Paragraph("Рекомендуется учесть предложенные замечания для повышения эффективности проекта.", styles['normal']))

            # Футер с метаданными
            story.append(Spacer(1, 1*cm))
            story.append(Paragraph(f"<b>Аудитор:</b> GigaChat AI", styles['small']))
            story.append(Paragraph(f"<b>Дата формирования отчёта:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['small']))
            story.append(Paragraph(f"<b>ID отчёта:</b> AUDIT-{audit_data.get('audit_id', 'N/A')}", styles['small']))
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("<i>Сгенерировано системой GrantService</i>", styles['small']))
            story.append(Paragraph("<i>Automated Grant Application Analysis</i>", styles['small']))

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"✅ Audit PDF создан: {len(pdf_bytes)} байт")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации Audit PDF: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_text(audit_data, "АУДИТ").encode('utf-8')

    def generate_research_pdf(self, research_data: Dict[str, Any]) -> bytes:
        """
        Генерация PDF с результатами исследования (27 queries)

        Args:
            research_data: Данные исследования
                {
                    'anketa_id': str,
                    'research_id': str,
                    'queries': [
                        {
                            'query_id': int,
                            'question': str,
                            'answer': str,
                            'sources': [str]
                        },
                        ...
                    ],
                    'summary': str,
                    'key_findings': str,
                    'completed_at': str
                }

        Returns:
            Байты PDF документа
        """
        try:
            from reportlab.platypus import Paragraph, Spacer, PageBreak
            from reportlab.lib.units import cm

            doc, buffer, styles = self._create_pdf_document("ИССЛЕДОВАНИЕ ПРОЕКТА")
            story = []

            # Заголовок
            story.append(Paragraph("📊 ИССЛЕДОВАНИЕ ПРОЕКТА", styles['title']))
            story.append(Spacer(1, 0.5*cm))

            # Metadata
            anketa_id = research_data.get('anketa_id', 'N/A')
            research_id = research_data.get('research_id', 'N/A')
            completed_at = research_data.get('completed_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            story.append(Paragraph(f"<b>ID Анкеты:</b> {anketa_id}", styles['normal']))
            story.append(Paragraph(f"<b>ID Исследования:</b> {research_id}", styles['normal']))
            story.append(Paragraph(f"<b>Дата завершения:</b> {completed_at}", styles['normal']))
            story.append(Spacer(1, 1*cm))

            # Queries
            queries = research_data.get('queries', [])
            story.append(Paragraph(f"РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ ({len(queries)} запросов)", styles['heading']))
            story.append(Spacer(1, 0.3*cm))

            for query in queries:
                query_id = query.get('query_id', '?')
                question = query.get('question', '')
                answer = query.get('answer', 'Нет ответа')
                sources = query.get('sources', [])

                # ЗАПРОС - крупным шрифтом, как заголовок
                story.append(Paragraph(f"ЗАПРОС {query_id}", styles['subheading']))
                story.append(Spacer(1, 0.2*cm))

                # Вопрос - жирным шрифтом
                story.append(Paragraph(f"<b>Вопрос:</b> {question}", styles['bold']))
                story.append(Spacer(1, 0.3*cm))

                # Ответ - обычным шрифтом с отступом
                story.append(Paragraph(f"<b>Ответ:</b>", styles['bold']))
                story.append(Spacer(1, 0.1*cm))
                story.append(Paragraph(answer, styles['normal']))
                story.append(Spacer(1, 0.3*cm))

                # Источники
                if sources:
                    story.append(Paragraph(f"<b>Источники ({len(sources)}):</b>", styles['bold']))
                    story.append(Spacer(1, 0.1*cm))
                    for i, source in enumerate(sources[:5], 1):  # Макс 5 источников
                        story.append(Paragraph(f"{i}. {source}", styles['small']))
                    story.append(Spacer(1, 0.3*cm))

                # Разделитель между запросами
                story.append(Spacer(1, 0.5*cm))

                # Page break каждые 5 queries
                if query_id % 5 == 0 and query_id < len(queries):
                    story.append(PageBreak())

            # Сводный анализ
            if research_data.get('summary'):
                story.append(PageBreak())
                story.append(Paragraph("СВОДНЫЙ АНАЛИЗ", styles['heading']))
                story.append(Paragraph(research_data['summary'], styles['normal']))
                story.append(Spacer(1, 0.5*cm))

            # Ключевые находки
            if research_data.get('key_findings'):
                story.append(Paragraph("КЛЮЧЕВЫЕ НАХОДКИ", styles['heading']))
                story.append(Paragraph(research_data['key_findings'], styles['normal']))
                story.append(Spacer(1, 0.5*cm))

            # Футер
            self._add_footer(story, styles)

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"✅ Research PDF создан: {len(pdf_bytes)} байт")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации Research PDF: {e}")
            return self._generate_fallback_text(research_data, "ИССЛЕДОВАНИЕ").encode('utf-8')

    def generate_grant_pdf(self, grant_data: Dict[str, Any]) -> bytes:
        """
        Генерация PDF с финальной грантовой заявкой

        Args:
            grant_data: Данные гранта
                {
                    'anketa_id': str,
                    'grant_id': str,
                    'title': str,
                    'quality_score': int,
                    'sections': [
                        {'title': str, 'content': str},
                        ...
                    ],
                    'full_text': str,
                    'completed_at': str
                }

        Returns:
            Байты PDF документа
        """
        try:
            from reportlab.platypus import Paragraph, Spacer, PageBreak
            from reportlab.lib.units import cm

            doc, buffer, styles = self._create_pdf_document("ГРАНТОВАЯ ЗАЯВКА")
            story = []

            # Заголовок
            story.append(Paragraph("✍️ ГРАНТОВАЯ ЗАЯВКА", styles['title']))
            story.append(Spacer(1, 0.5*cm))

            # Metadata
            anketa_id = grant_data.get('anketa_id', 'N/A')
            grant_id = grant_data.get('grant_id', 'N/A')
            title = grant_data.get('title', 'Без названия')
            quality_score = grant_data.get('quality_score', 0)
            completed_at = grant_data.get('completed_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            story.append(Paragraph(f"<b>ID Анкеты:</b> {anketa_id}", styles['normal']))
            story.append(Paragraph(f"<b>ID Гранта:</b> {grant_id}", styles['normal']))
            story.append(Paragraph(f"<b>Название проекта:</b> {title}", styles['heading']))
            story.append(Paragraph(f"<b>Оценка качества:</b> {quality_score}/10", styles['normal']))
            story.append(Paragraph(f"<b>Дата завершения:</b> {completed_at}", styles['normal']))
            story.append(Spacer(1, 1*cm))

            # Секции гранта
            sections = grant_data.get('sections', [])
            if sections:
                story.append(Paragraph("СОДЕРЖАНИЕ ГРАНТОВОЙ ЗАЯВКИ", styles['heading']))
                story.append(Spacer(1, 0.5*cm))

                for section in sections:
                    section_title = section.get('title', 'Без названия')
                    section_content = section.get('content', '')

                    story.append(Paragraph(section_title, styles['subheading']))
                    story.append(Paragraph(section_content, styles['normal']))
                    story.append(Spacer(1, 0.5*cm))

            # Полный текст
            if grant_data.get('full_text'):
                story.append(PageBreak())
                story.append(Paragraph("ПОЛНЫЙ ТЕКСТ ЗАЯВКИ", styles['heading']))
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(grant_data['full_text'], styles['normal']))

            # Футер
            self._add_footer(story, styles)

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"✅ Grant PDF создан: {len(pdf_bytes)} байт")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации Grant PDF: {e}")
            return self._generate_fallback_text(grant_data, "ГРАНТ").encode('utf-8')

    def generate_review_pdf(self, review_data: Dict[str, Any]) -> bytes:
        """
        Генерация PDF с заключением ревьювера

        Args:
            review_data: Данные ревью
                {
                    'anketa_id': str,
                    'grant_id': str,
                    'quality_score': int,
                    'strengths': str,
                    'weaknesses': str,
                    'recommendations': str,
                    'verdict': str,  # 'approved' / 'needs_revision'
                    'completed_at': str
                }

        Returns:
            Байты PDF документа
        """
        try:
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.units import cm

            doc, buffer, styles = self._create_pdf_document("ЗАКЛЮЧЕНИЕ РЕВЬЮВЕРА")
            story = []

            # Заголовок
            story.append(Paragraph("👁️ ЗАКЛЮЧЕНИЕ РЕВЬЮВЕРА", styles['title']))
            story.append(Spacer(1, 0.5*cm))

            # Metadata
            anketa_id = review_data.get('anketa_id', 'N/A')
            grant_id = review_data.get('grant_id', 'N/A')
            quality_score = review_data.get('quality_score', 0)
            verdict = review_data.get('verdict', 'unknown')
            completed_at = review_data.get('completed_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            verdict_text = "✅ ОДОБРЕН" if verdict == 'approved' else "⚠️ ТРЕБУЕТ ДОРАБОТКИ"

            story.append(Paragraph(f"<b>ID Анкеты:</b> {anketa_id}", styles['normal']))
            story.append(Paragraph(f"<b>ID Гранта:</b> {grant_id}", styles['normal']))
            story.append(Paragraph(f"<b>Дата ревью:</b> {completed_at}", styles['normal']))
            story.append(Paragraph(f"<b>Оценка качества:</b> {quality_score}/10", styles['normal']))
            story.append(Paragraph(f"<b>Результат:</b> {verdict_text}", styles['heading']))
            story.append(Spacer(1, 1*cm))

            # Сильные стороны
            if review_data.get('strengths'):
                story.append(Paragraph("СИЛЬНЫЕ СТОРОНЫ", styles['heading']))
                story.append(Paragraph(review_data['strengths'], styles['normal']))
                story.append(Spacer(1, 0.5*cm))

            # Слабые стороны
            if review_data.get('weaknesses'):
                story.append(Paragraph("СЛАБЫЕ СТОРОНЫ", styles['heading']))
                story.append(Paragraph(review_data['weaknesses'], styles['normal']))
                story.append(Spacer(1, 0.5*cm))

            # Рекомендации
            if review_data.get('recommendations'):
                story.append(Paragraph("РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ", styles['heading']))
                story.append(Paragraph(review_data['recommendations'], styles['normal']))
                story.append(Spacer(1, 0.5*cm))

            # Футер
            self._add_footer(story, styles)

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"✅ Review PDF создан: {len(pdf_bytes)} байт")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации Review PDF: {e}")
            return self._generate_fallback_text(review_data, "РЕВЬЮ").encode('utf-8')

    def _generate_fallback_text(self, data: Dict[str, Any], stage_name: str) -> str:
        """
        Генерация текстового fallback если PDF не удалось создать

        Args:
            data: Данные этапа
            stage_name: Название этапа

        Returns:
            Текстовое представление данных
        """
        lines = [
            f"={stage_name}=".center(80, '='),
            "",
            f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        for key, value in data.items():
            if isinstance(value, (str, int, float)):
                lines.append(f"{key}: {value}")
            elif isinstance(value, list):
                lines.append(f"{key}: {len(value)} items")
            elif isinstance(value, dict):
                lines.append(f"{key}: {len(value)} fields")

        lines.append("")
        lines.append("=" * 80)
        lines.append("GrantService - AI-Powered Grant Application System")

        return "\n".join(lines)


# Вспомогательная функция для быстрого создания PDF
def generate_stage_pdf(stage: str, data: Dict[str, Any]) -> bytes:
    """
    Быстрая генерация PDF для этапа

    Args:
        stage: Название этапа ('interview', 'audit', 'research', 'grant', 'review')
        data: Данные этапа

    Returns:
        Байты PDF документа

    Example:
        >>> pdf_bytes = generate_stage_pdf('interview', anketa_data)
        >>> pdf_bytes = generate_stage_pdf('audit', audit_data)
    """
    generator = StageReportGenerator()

    stage_methods = {
        'interview': generator.generate_interview_pdf,
        'audit': generator.generate_audit_pdf,
        'research': generator.generate_research_pdf,
        'grant': generator.generate_grant_pdf,
        'review': generator.generate_review_pdf
    }

    method = stage_methods.get(stage.lower())
    if not method:
        raise ValueError(f"Unknown stage: {stage}. Must be one of: {list(stage_methods.keys())}")

    return method(data)


if __name__ == "__main__":
    # Тестирование генератора
    logger.info("🧪 Тестирование StageReportGenerator")

    # Тестовые данные
    test_anketa = {
        'anketa_id': '#AN-20251012-test_user-001',
        'username': 'test_user',
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'telegram_id': 123456789,
        'created_at': '2025-10-12 15:30:00',
        'questions_answers': [
            {'question_id': 1, 'question_text': 'Название проекта?', 'answer': 'Тестовый проект'},
            {'question_id': 2, 'question_text': 'Описание проекта?', 'answer': 'Это тестовое описание проекта'}
        ]
    }

    # Генерация тестового PDF
    pdf_bytes = generate_stage_pdf('interview', test_anketa)
    logger.info(f"✅ Тестовый PDF создан: {len(pdf_bytes)} байт")
