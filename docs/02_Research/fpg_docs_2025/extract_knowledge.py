# -*- coding: utf-8 -*-
"""
Извлечение знаний из HTML файлов ФПГ для создания базы знаний
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json

# Маппинг файлов к названиям разделов
FILE_MAPPING = {
    'art83_obshie_trebovaniya.html': {
        'title': 'Общие требования к заполнению заявки',
        'category': 'Общие правила',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=83'
    },
    'art84_o_proekte.html': {
        'title': 'Как заполнить раздел "О проекте"',
        'category': 'Разделы заявки',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=84'
    },
    'art79_rukovoditel.html': {
        'title': 'Как заполнить раздел "Руководитель проекта"',
        'category': 'Разделы заявки',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=79'
    },
    'art85_komanda.html': {
        'title': 'Как заполнить раздел "Команда проекта"',
        'category': 'Разделы заявки',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=85'
    },
    'art86_organizaciya.html': {
        'title': 'Как заполнить раздел "Организация-заявитель"',
        'category': 'Разделы заявки',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=86'
    },
    'art87_kalendarnyj_plan.html': {
        'title': 'Как заполнить раздел "Календарный план"',
        'category': 'Разделы заявки',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=87'
    },
    'art122_budget.html': {
        'title': 'Как заполнить раздел "Бюджет проекта"',
        'category': 'Разделы заявки',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=122'
    },
    'art88_budget_principles.html': {
        'title': 'Общие принципы формирования бюджета проекта',
        'category': 'Бюджет',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=88'
    },
    'art113_nelzya.html': {
        'title': 'На что НЕЛЬЗЯ запрашивать и тратить средства гранта',
        'category': 'Бюджет',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=113'
    },
    'art89_ne_rekomenduetsya.html': {
        'title': 'На что НЕ РЕКОМЕНДУЕТСЯ запрашивать и тратить средства',
        'category': 'Бюджет',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=89'
    },
    'art69_budget_comments.html': {
        'title': 'Комментарии по отдельным статьям бюджета',
        'category': 'Бюджет',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=69'
    },
    'art65_razrabotat_proekt.html': {
        'title': 'Как разработать социальный проект',
        'category': 'Подготовка',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=65'
    },
    'art64_zachem_proekt.html': {
        'title': 'Почему нет смысла подавать заявку, не имея проекта',
        'category': 'Подготовка',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=64'
    },
    'art24_kto_mozhet.html': {
        'title': 'Кто может участвовать в конкурсе',
        'category': 'О конкурсе',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=24'
    },
    'art43_napravleniya.html': {
        'title': 'Грантовые направления и примерные тематики',
        'category': 'О конкурсе',
        'url': 'https://поддержка.президентскиегранты.рф/Article/?id=43'
    },
}

def extract_text_from_html(html_path):
    """Извлечь текст из HTML файла"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # Найти основной контент (внутри div.content-article)
        content_div = soup.find('div', class_='content-article')
        if not content_div:
            content_div = soup.find('div', class_='wrapper-content-article')

        if not content_div:
            print(f"Не найден контент в {html_path}")
            return ""

        # Извлечь текст с сохранением структуры
        text_parts = []

        for element in content_div.find_all(['p', 'li', 'h2', 'h3', 'strong', 'span']):
            text = element.get_text(strip=True)
            if text and len(text) > 5:  # Пропускаем пустые элементы
                # Определяем тип элемента
                if element.name in ['h2', 'h3']:
                    text_parts.append(f"\n## {text}\n")
                elif element.name == 'li':
                    text_parts.append(f"- {text}")
                else:
                    text_parts.append(text)

        return '\n\n'.join(text_parts)

    except Exception as e:
        print(f"Ошибка при обработке {html_path}: {e}")
        return ""

def extract_character_limits(text):
    """Извлечь информацию об ограничениях по символам"""
    limits = []

    # Паттерны для поиска ограничений
    patterns = [
        r'(\d+)\s*символ[а-я]*\s*(вместе с пробелами)?',
        r'не более\s*(\d+)\s*символ',
        r'не менее\s*(\d+)\s*символ',
        r'максимальн[а-я]*\s*длин[а-я]*\s*[—\-]\s*(\d+)\s*символ',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            limits.append({
                'limit': match.group(1) if match.groups() else match.group(0),
                'context': context.strip()
            })

    return limits

def create_knowledge_base():
    """Создать базу знаний из всех HTML файлов"""
    docs_dir = Path(__file__).parent
    knowledge = {
        'metadata': {
            'version': '1.0',
            'source': 'Фонд президентских грантов',
            'url': 'https://президентскиегранты.рф',
            'date_created': '2025-10-17'
        },
        'categories': {},
        'all_limits': [],
        'full_texts': {}
    }

    print("Извлекаем знания из HTML файлов...\n")

    for filename, info in FILE_MAPPING.items():
        file_path = docs_dir / filename

        if not file_path.exists():
            print(f"[!] Файл не найден: {filename}")
            continue

        print(f"[*] Обрабатываю: {info['title']}")

        # Извлечь текст
        text = extract_text_from_html(file_path)

        if not text:
            print(f"    [X] Не удалось извлечь текст")
            continue

        # Извлечь ограничения по символам
        limits = extract_character_limits(text)

        # Сохранить в базу знаний
        category = info['category']
        if category not in knowledge['categories']:
            knowledge['categories'][category] = []

        doc_entry = {
            'title': info['title'],
            'url': info['url'],
            'text_length': len(text),
            'character_limits': limits,
            'filename': filename
        }

        knowledge['categories'][category].append(doc_entry)
        knowledge['full_texts'][filename] = text
        knowledge['all_limits'].extend(limits)

        print(f"    [+] Извлечено: {len(text)} символов, {len(limits)} ограничений")

    return knowledge

# Запустить извлечение
if __name__ == '__main__':
    kb = create_knowledge_base()

    # Сохранить метаданные
    metadata_file = Path(__file__).parent / 'knowledge_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        # Сохраняем только метаданные без полных текстов
        metadata = {k: v for k, v in kb.items() if k != 'full_texts'}
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Метаданные сохранены в {metadata_file}")
    print(f"[INFO] Обработано категорий: {len(kb['categories'])}")
    print(f"[INFO] Всего документов: {sum(len(docs) for docs in kb['categories'].values())}")
    print(f"[INFO] Найдено ограничений: {len(kb['all_limits'])}")

    # Сохранить полные тексты отдельно
    for filename, text in kb['full_texts'].items():
        text_file = Path(__file__).parent / 'extracted_texts' / f"{Path(filename).stem}.txt"
        text_file.parent.mkdir(exist_ok=True)
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)

    print(f"[INFO] Тексты сохранены в директорию extracted_texts/")
