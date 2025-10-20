# -*- coding: utf-8 -*-
"""
Создание полноценной базы знаний в Markdown для агентов GrantService
"""
from pathlib import Path
import json

def create_knowledge_base_markdown():
    """Создать структурированную базу знаний в Markdown"""

    docs_dir = Path(__file__).parent
    texts_dir = docs_dir / 'extracted_texts'

    # Загрузить метаданные
    with open(docs_dir / 'knowledge_metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Создать главный файл базы знаний
    kb_content = [
        "# База знаний: Грантовые заявки ФПГ",
        "",
        "**Версия:** 1.0",
        "**Источник:** Фонд президентских грантов",
        "**URL:** https://президентскиегранты.рф",
        "**Дата создания:** 2025-10-17",
        "",
        "## О базе знаний",
        "",
        "Эта база знаний содержит полную информацию о требованиях к заполнению заявок на грант Фонда президентских грантов.",
        "Предназначена для использования агентами: writer (писатель заявок), researcher (исследователь), reviewer (ревьювер).",
        "",
        f"**Всего документов:** {sum(len(docs) for docs in metadata['categories'].values())}",
        f"**Категорий:** {len(metadata['categories'])}",
        "",
        "## Содержание",
        ""
    ]

    # Добавить оглавление
    for i, category in enumerate(metadata['categories'].keys(), 1):
        kb_content.append(f"{i}. [{category}](#{category.lower().replace(' ', '-')})")

    kb_content.extend(["", "---", ""])

    # Создать разделы для каждой категории
    for category, docs in metadata['categories'].items():
        kb_content.extend([
            f"# {category}",
            ""
        ])

        for doc in docs:
            filename = doc['filename']
            text_file = texts_dir / f"{Path(filename).stem}.txt"

            if not text_file.exists():
                continue

            # Прочитать текст
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()

            kb_content.extend([
                f"## {doc['title']}",
                "",
                f"**Источник:** [{doc['url']}]({doc['url']})",
                f"**Размер:** {doc['text_length']} символов",
                ""
            ])

            # Добавить информацию об ограничениях
            if doc['character_limits']:
                kb_content.extend([
                    "### Ограничения по символам",
                    ""
                ])
                for limit in doc['character_limits']:
                    kb_content.append(f"- **{limit['limit']} символов:** {limit['context'][:200]}...")
                    kb_content.append("")

            kb_content.extend([
                "### Полный текст",
                "",
                text,
                "",
                "---",
                ""
            ])

    # Сохранить базу знаний
    kb_file = docs_dir / 'KNOWLEDGE_BASE.md'
    with open(kb_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(kb_content))

    print(f"[+] База знаний создана: {kb_file}")
    print(f"[INFO] Размер: {kb_file.stat().st_size / 1024:.1f} KB")

    # Создать индексный файл README
    create_readme(docs_dir, metadata)

    return kb_file

def create_readme(docs_dir, metadata):
    """Создать README для быстрого поиска"""

    readme_content = [
        "# База знаний ФПГ - Индекс",
        "",
        "## Быстрый поиск",
        "",
        "### По категориям",
        ""
    ]

    for category, docs in metadata['categories'].items():
        readme_content.extend([
            f"#### {category}",
            ""
        ])
        for doc in docs:
            readme_content.append(f"- **{doc['title']}** ([источник]({doc['url']}))")
            readme_content.append(f"  - Файл: `extracted_texts/{Path(doc['filename']).stem}.txt`")
            readme_content.append(f"  - Размер: {doc['text_length']} символов")
            if doc['character_limits']:
                readme_content.append(f"  - Ограничений найдено: {len(doc['character_limits'])}")
            readme_content.append("")

    readme_content.extend([
        "## Ключевые ограничения по символам",
        "",
        "### Раздел \"О проекте\""
    ])

    # Добавить все найденные ограничения
    for limit in metadata['all_limits']:
        readme_content.append(f"- **{limit['limit']} символов:** {limit['context'][:150]}...")

    readme_content.extend([
        "",
        "## Структура директории",
        "",
        "```",
        "fpg_docs_2025/",
        "├── KNOWLEDGE_BASE.md          # Полная база знаний",
        "├── README.md                  # Этот файл (индекс)",
        "├── knowledge_metadata.json    # Метаданные",
        "├── extract_knowledge.py       # Скрипт извлечения",
        "├── extracted_texts/           # Извлеченные тексты",
        "│   ├── art83_obshie_trebovaniya.txt",
        "│   ├── art84_o_proekte.txt",
        "│   └── ...",
        "└── *.html                     # Исходные HTML файлы",
        "```",
        "",
        "## Использование агентами",
        "",
        "### Для Writer (писатель заявок)",
        "Используйте `KNOWLEDGE_BASE.md` для получения требований к каждому разделу заявки.",
        "",
        "### Для Researcher (исследователь)",
        "Используйте `extracted_texts/` для поиска конкретной информации.",
        "",
        "### Для Reviewer (ревьювер)",
        "Используйте `knowledge_metadata.json` для проверки соответствия требованиям.",
        ""
    ])

    readme_file = docs_dir / 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(readme_content))

    print(f"[+] README создан: {readme_file}")

if __name__ == '__main__':
    kb_file = create_knowledge_base_markdown()
    print(f"\n[SUCCESS] База знаний готова!")
    print(f"[INFO] Используйте {kb_file.name} для работы с агентами")
