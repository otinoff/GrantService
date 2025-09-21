# План добавления вопроса с выбором грантового направления

## 1. Структура вопроса в БД

### Поля в таблице interview_questions:
- `question_type`: 'select' (вместо 'text')
- `options`: JSON массив с вариантами ответов
- `question_text`: "Выберите грантовое направление для вашего проекта"
- `hint_text`: "При заполнении заявки нужно выбрать только одно грантовое направление, которому более всего соответствует тема проекта"

## 2. Варианты ответов

```json
[
  {
    "value": "science_education",
    "text": "Поддержка проектов в области науки, образования, просвещения",
    "description": "включает стандартный и долгосрочный срок реализации"
  },
  {
    "value": "civil_society",
    "text": "Развитие институтов гражданского общества",
    "description": "включает стандартный и долгосрочный срок реализации"
  },
  {
    "value": "public_diplomacy",
    "text": "Развитие общественной дипломатии и поддержка соотечественников",
    "description": ""
  },
  {
    "value": "social_initiatives",
    "text": "Поддержка социально значимых инициатив и проектов",
    "description": ""
  },
  {
    "value": "culture_art",
    "text": "Развитие культуры и искусства",
    "description": ""
  },
  {
    "value": "charity_support",
    "text": "Поддержка проектов в сфере благотворительности и поддержки уязвимых групп",
    "description": ""
  },
  {
    "value": "environment",
    "text": "Поддержка проектов в области охраны окружающей среды и устойчивого развития",
    "description": ""
  },
  {
    "value": "youth_initiatives",
    "text": "Развитие молодежных инициатив и проектов",
    "description": ""
  },
  {
    "value": "sport_physical",
    "text": "Поддержка и развитие спорта и массового физкультурного движения",
    "description": ""
  },
  {
    "value": "innovation_tech",
    "text": "Поддержка инновационных и технологических проектов в общественной сфере",
    "description": ""
  },
  {
    "value": "regional_initiatives",
    "text": "Развитие региональных инициатив и проектов",
    "description": ""
  }
]
```

## 3. Изменения в боте

### А. Обновление обработки вопросов
В методе `show_question_navigation` нужно:
1. Проверить тип вопроса
2. Если `question_type == 'select'`, показать кнопки выбора
3. Создать InlineKeyboard с вариантами ответов

### Б. Обработка выбора
В методе `handle_menu_callback` добавить:
1. Обработку callback_data для вариантов ответа
2. Сохранение выбранного значения
3. Переход к следующему вопросу

## 4. SQL для добавления вопроса

```sql
INSERT INTO interview_questions (
    question_number,
    question_text,
    field_name,
    question_type,
    options,
    hint_text,
    is_required,
    is_active
) VALUES (
    25,  -- или другой номер в зависимости от позиции
    'Выберите грантовое направление для вашего проекта',
    'grant_direction',
    'select',
    '[{"value":"science_education","text":"Поддержка проектов в области науки, образования, просвещения","description":"включает стандартный и долгосрочный срок реализации"},{"value":"civil_society","text":"Развитие институтов гражданского общества","description":"включает стандартный и долгосрочный срок реализации"},{"value":"public_diplomacy","text":"Развитие общественной дипломатии и поддержка соотечественников","description":""},{"value":"social_initiatives","text":"Поддержка социально значимых инициатив и проектов","description":""},{"value":"culture_art","text":"Развитие культуры и искусства","description":""},{"value":"charity_support","text":"Поддержка проектов в сфере благотворительности и поддержки уязвимых групп","description":""},{"value":"environment","text":"Поддержка проектов в области охраны окружающей среды и устойчивого развития","description":""},{"value":"youth_initiatives","text":"Развитие молодежных инициатив и проектов","description":""},{"value":"sport_physical","text":"Поддержка и развитие спорта и массового физкультурного движения","description":""},{"value":"innovation_tech","text":"Поддержка инновационных и технологических проектов в общественной сфере","description":""},{"value":"regional_initiatives","text":"Развитие региональных инициатив и проектов","description":""}]',
    'При заполнении заявки нужно выбрать только одно грантовое направление, которому более всего соответствует тема проекта и основная часть мероприятий. Также в заявке нужно выбрать тематическое направление внутри выбранного грантового направления. Источник: методические рекомендации Фонда президентских грантов 2025 года.',
    1,
    1
);
```

## 5. Обновление main.py для поддержки select вопросов

### Изменения в методе show_question_navigation:

```python
async def show_question_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_number: int = 1):
    # ... существующий код ...
    
    # Получаем вопрос
    question = self.get_question_by_number(question_number)
    if not question:
        await self.show_error(update, context, "Вопрос не найден")
        return
    
    # Проверяем тип вопроса
    if question.get('question_type') == 'select' and question.get('options'):
        # Парсим опции из JSON
        try:
            options = json.loads(question['options'])
            
            # Создаем клавиатуру с вариантами ответов
            keyboard = []
            for option in options:
                # Создаем кнопку для каждого варианта
                # Сокращаем текст если слишком длинный
                button_text = option['text'][:60] + '...' if len(option['text']) > 60 else option['text']
                callback_data = f"select_{question_number}_{option['value']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Добавляем навигационные кнопки
            nav_buttons = []
            if question_number > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_question_{question_number-1}"))
            keyboard.append(nav_buttons) if nav_buttons else None
            
            # Кнопка возврата в меню
            keyboard.append([InlineKeyboardButton("🏠 Вернуться в меню", callback_data="main_menu")])
            
        except Exception as e:
            logger.error(f"Ошибка парсинга опций вопроса: {e}")
            # Fallback на обычный текстовый вопрос
            # ... продолжаем как обычный вопрос ...
    
    # ... остальной код для обычных вопросов ...
```

### Изменения в методе handle_menu_callback:

```python
async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... существующий код ...
    
    elif callback_data.startswith("select_"):
        # Обработка выбора варианта ответа
        parts = callback_data.split("_", 2)
        if len(parts) == 3:
            question_number = int(parts[1])
            selected_value = parts[2]
            
            # Сохраняем ответ
            user_id = query.from_user.id
            session = self.get_user_session(user_id)
            
            # Получаем field_name для вопроса
            question_info = self.get_question_by_number(question_number)
            if question_info:
                field_name = question_info.get('field_name', str(question_number))
                
                # Сохраняем выбранное значение
                session['answers'][field_name] = selected_value
                
                # Сохраняем в БД
                # ... код сохранения в БД ...
                
                # Переходим к следующему вопросу
                if question_number < session['total_questions']:
                    await self.show_question_navigation(update, context, question_number + 1)
                else:
                    # Последний вопрос - автосохранение
                    anketa_id = await self.auto_save_anketa(update, context, user_id)
                    if anketa_id:
                        await self.show_completion_screen(update, context, anketa_id)
                    else:
                        await self.show_review_screen(update, context)
```

## 6. Тестирование

1. Добавить вопрос в БД
2. Перезапустить бота
3. Протестировать:
   - Отображение вопроса с кнопками
   - Выбор варианта
   - Сохранение ответа
   - Переход к следующему вопросу

## 7. Дополнительные улучшения

### А. Многоколоночное отображение
Для компактности можно отображать короткие варианты в 2 колонки:
```python
# Группируем кнопки по 2 в ряд для коротких вариантов
row = []
for i, option in enumerate(options):
    button_text = option['text'][:30] + '...' if len(option['text']) > 30 else option['text']
    callback_data = f"select_{question_number}_{option['value']}"
    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    if len(row) == 2 or i == len(options) - 1:
        keyboard.append(row)
        row = []
```

### Б. Отображение выбранного значения
После выбора показывать пользователю что он выбрал:
```python
# В обработчике callback
await query.answer(f"Выбрано: {option_text}", show_alert=False)
```

### В. Валидация
Добавить проверку обязательности ответа для select вопросов.

## 8. Расширение функционала

В будущем можно добавить:
- Множественный выбор (multiselect)
- Радио-кнопки для взаимоисключающих вариантов
- Условная логика (показывать вопросы в зависимости от предыдущих ответов)
- Группировка вариантов по категориям