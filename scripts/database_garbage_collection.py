"""
Database Garbage Collection Script
===================================
Очистка базы данных от пустых и тестовых записей

Что удаляется:
1. Пустые сессии без ответов (79 записей)
2. Тестовые пользователи (test_user_e2e, ekaterina_maximova, ai_test_user, e2e_test_user)
3. Незавершенные researcher_research с status='pending' и пустыми results
4. Grant applications без связанных grants
5. Orphaned user_answers без session_id

Что сохраняется:
- Все completed сессии с полными данными
- Все grants с content
- Real users: Otinoff, Natalia_bruzzzz, Nik_Stepanoff, theperipherals
- Завершенные researcher_research
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'grantservice',
    'user': 'postgres',
    'password': 'root'
}

def get_connection():
    """Подключение к базе данных"""
    return psycopg2.connect(**DB_CONFIG)

def print_header(title):
    """Вывод заголовка секции"""
    print("\n" + "="*80)
    print(title)
    print("="*80 + "\n")

def analyze_database():
    """Анализ базы данных - что нужно удалить"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print_header("АНАЛИЗ БАЗЫ ДАННЫХ - ПОИСК МУСОРНЫХ ДАННЫХ")

    # 1. Пустые сессии
    cur.execute("""
        SELECT COUNT(*) as count
        FROM sessions s
        WHERE s.id NOT IN (SELECT DISTINCT session_id FROM user_answers WHERE session_id IS NOT NULL)
    """)
    empty_sessions = cur.fetchone()['count']
    print(f"1. Пустые сессии (без ответов): {empty_sessions}")

    # 2. Тестовые пользователи - сессии
    test_users = ['test_user_e2e', 'ekaterina_maximova', 'ai_test_user', 'e2e_test_user', 'valeria_test']
    cur.execute("""
        SELECT
            u.username,
            COUNT(s.id) as session_count,
            COUNT(CASE WHEN s.completion_status = 'completed' THEN 1 END) as completed_count
        FROM users u
        LEFT JOIN sessions s ON u.telegram_id = s.telegram_id
        WHERE u.username = ANY(%s)
        GROUP BY u.username
        ORDER BY session_count DESC
    """, (test_users,))

    print("\n2. Тестовые пользователи:")
    test_user_sessions = cur.fetchall()
    for row in test_user_sessions:
        print(f"   - {row['username']}: {row['session_count']} сессий ({row['completed_count']} завершено)")

    # 3. Researcher_research с pending status и пустыми results
    cur.execute("""
        SELECT COUNT(*) as count
        FROM researcher_research
        WHERE status = 'pending' AND (research_results IS NULL OR research_results = 'null'::jsonb)
    """)
    pending_research = cur.fetchone()['count']
    print(f"\n3. Незавершенные исследования (pending, нет results): {pending_research}")

    # 4. Grant applications без grants
    cur.execute("""
        SELECT COUNT(*) as count
        FROM grant_applications ga
        WHERE ga.anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
    """)
    apps_without_grants = cur.fetchone()['count']
    print(f"4. Grant applications без grants: {apps_without_grants}")

    # 5. Grants с пустым content
    cur.execute("""
        SELECT COUNT(*) as count
        FROM grants
        WHERE grant_content IS NULL OR LENGTH(grant_content) < 100
    """)
    empty_grants = cur.fetchone()['count']
    print(f"5. Grants с пустым/коротким content (<100 символов): {empty_grants}")

    # 6. Orphaned user_answers
    cur.execute("""
        SELECT COUNT(*) as count
        FROM user_answers ua
        WHERE ua.session_id NOT IN (SELECT id FROM sessions WHERE id IS NOT NULL)
    """)
    orphaned_answers = cur.fetchone()['count']
    print(f"6. Orphaned user_answers (session удалена): {orphaned_answers}")

    # 7. Статистика по пользователям
    cur.execute("""
        SELECT
            u.username,
            u.role,
            COUNT(s.id) as session_count,
            COUNT(CASE WHEN s.completion_status = 'completed' THEN 1 END) as completed,
            MAX(s.started_at)::date as last_session
        FROM users u
        LEFT JOIN sessions s ON u.telegram_id = s.telegram_id
        GROUP BY u.username, u.role
        ORDER BY session_count DESC
    """)

    print("\n7. Все пользователи:")
    users = cur.fetchall()
    for row in users:
        status = "ТЕСТ" if row['username'] in test_users else "REAL"
        print(f"   [{status}] {row['username']}: {row['session_count']} сессий, {row['completed']} завершено, последняя: {row['last_session']}")

    cur.close()
    conn.close()

    print("\n" + "="*80)
    total_to_delete = empty_sessions + sum(r['session_count'] for r in test_user_sessions) + pending_research + apps_without_grants + empty_grants + orphaned_answers
    print(f"ИТОГО записей для удаления: ~{total_to_delete}")
    print("="*80 + "\n")

def cleanup_database(dry_run=True):
    """Очистка базы данных

    Args:
        dry_run: если True, только показывает что будет удалено (без реального удаления)
    """
    conn = get_connection()
    cur = conn.cursor()

    mode = "DRY RUN (БЕЗ УДАЛЕНИЯ)" if dry_run else "РЕАЛЬНОЕ УДАЛЕНИЕ"
    print_header(f"ОЧИСТКА БАЗЫ ДАННЫХ - {mode}")

    deleted_counts = {}
    test_users = ['test_user_e2e', 'ekaterina_maximova', 'ai_test_user', 'e2e_test_user', 'valeria_test']

    # ВАЖНО: Порядок удаления критичен из-за FK constraints!
    # Сначала удаляем grants (они ссылаются на sessions и researcher_research)
    # Потом grant_applications и researcher_research (они ссылаются на sessions)
    # И только в конце sessions и user_answers

    # 1. Удалить grants с пустым content (<100 символов)
    # ИЛИ grants которые ссылаются на pending researcher_research
    print("1. Udalenie grants s pustym content ili pending research...")
    query = """
        DELETE FROM grants
        WHERE grant_content IS NULL
           OR LENGTH(grant_content) < 100
           OR research_id IN (
               SELECT research_id FROM researcher_research
               WHERE status = 'pending'
               AND (research_results IS NULL OR research_results = 'null'::jsonb)
           )
    """
    if dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM grants
            WHERE grant_content IS NULL
               OR LENGTH(grant_content) < 100
               OR research_id IN (
                   SELECT research_id FROM researcher_research
                   WHERE status = 'pending'
                   AND (research_results IS NULL OR research_results = 'null'::jsonb)
               )
        """)
        count = cur.fetchone()[0]
        print(f"   Budet udaleno: {count} zapisej")
    else:
        cur.execute(query)
        count = cur.rowcount
        print(f"   Udaleno: {count} zapisej")
    deleted_counts['empty_grants'] = count

    # 2. Удалить grant_applications без grants (после удаления пустых grants)
    print("\n2. Udalenie grant_applications bez grants...")
    query = """
        DELETE FROM grant_applications
        WHERE anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
    """
    if dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM grant_applications
            WHERE anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
        """)
        count = cur.fetchone()[0]
        print(f"   Budet udaleno: {count} zapisej")
    else:
        cur.execute(query)
        count = cur.rowcount
        print(f"   Udaleno: {count} zapisej")
    deleted_counts['apps_without_grants'] = count

    # 3. Удалить незавершенные researcher_research (pending с пустыми results)
    print("\n3. Udalenie nezavershennyh issledovanij...")
    query = """
        DELETE FROM researcher_research
        WHERE status = 'pending'
        AND (research_results IS NULL OR research_results = 'null'::jsonb)
    """
    if dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM researcher_research
            WHERE status = 'pending'
            AND (research_results IS NULL OR research_results = 'null'::jsonb)
        """)
        count = cur.fetchone()[0]
        print(f"   Budet udaleno: {count} zapisej")
    else:
        cur.execute(query)
        count = cur.rowcount
        print(f"   Udaleno: {count} zapisej")
    deleted_counts['pending_research'] = count

    # 4. Удалить user_answers для пустых sessions и test users
    print("\n4. Udalenie user_answers pustykh sessij i test users...")
    query = """
        DELETE FROM user_answers
        WHERE session_id IN (
            SELECT id FROM sessions
            WHERE (
                id NOT IN (SELECT DISTINCT session_id FROM user_answers WHERE session_id IS NOT NULL)
                OR telegram_id IN (SELECT telegram_id FROM users WHERE username = ANY(%s))
            )
            AND completion_status != 'completed'
        )
        OR session_id NOT IN (SELECT id FROM sessions WHERE id IS NOT NULL)
    """
    if dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM user_answers
            WHERE session_id IN (
                SELECT id FROM sessions
                WHERE (
                    id NOT IN (SELECT DISTINCT session_id FROM user_answers WHERE session_id IS NOT NULL)
                    OR telegram_id IN (SELECT telegram_id FROM users WHERE username = ANY(%s))
                )
                AND completion_status != 'completed'
            )
            OR session_id NOT IN (SELECT id FROM sessions WHERE id IS NOT NULL)
        """, (test_users,))
        count = cur.fetchone()[0]
        print(f"   Budet udaleno: {count} zapisej")
    else:
        cur.execute(query, (test_users,))
        count = cur.rowcount
        print(f"   Udaleno: {count} zapisej")
    deleted_counts['user_answers'] = count

    # 5. Удалить пустые sessions (без ответов, не completed, НЕТ grants)
    print("\n5. Udalenie pustykh sessij (bez grants)...")
    query = """
        DELETE FROM sessions
        WHERE id NOT IN (SELECT DISTINCT session_id FROM user_answers WHERE session_id IS NOT NULL)
        AND completion_status != 'completed'
        AND anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
    """
    if dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE id NOT IN (SELECT DISTINCT session_id FROM user_answers WHERE session_id IS NOT NULL)
            AND completion_status != 'completed'
            AND anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
        """)
        count = cur.fetchone()[0]
        print(f"   Budet udaleno: {count} zapisej")
    else:
        cur.execute(query)
        count = cur.rowcount
        print(f"   Udaleno: {count} zapisej")
    deleted_counts['empty_sessions'] = count

    # 6. Удалить сессии тестовых пользователей (кроме completed, НЕТ grants)
    print("\n6. Udalenie sessij testovykh polzovatelej (bez grants)...")
    query = """
        DELETE FROM sessions
        WHERE telegram_id IN (
            SELECT telegram_id FROM users WHERE username = ANY(%s)
        )
        AND completion_status != 'completed'
        AND anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
    """
    if dry_run:
        cur.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE telegram_id IN (
                SELECT telegram_id FROM users WHERE username = ANY(%s)
            )
            AND completion_status != 'completed'
            AND anketa_id NOT IN (SELECT DISTINCT anketa_id FROM grants WHERE anketa_id IS NOT NULL)
        """, (test_users,))
        count = cur.fetchone()[0]
        print(f"   Budet udaleno: {count} sessij testovykh polzovatelej")
    else:
        cur.execute(query, (test_users,))
        count = cur.rowcount
        print(f"   Udaleno: {count} sessij testovykh polzovatelej")
    deleted_counts['test_user_sessions'] = count

    if not dry_run:
        conn.commit()
        print("\n[OK] Izmenenia sokhraneny v bazu dannyh")
    else:
        conn.rollback()
        print("\n[DRY RUN] Zaversheno - izmenenia NE sokhraneny")

    cur.close()
    conn.close()

    print("\n" + "="*80)
    print("ИТОГО УДАЛЕНО:")
    for key, value in deleted_counts.items():
        print(f"  - {key}: {value}")
    print(f"  ВСЕГО: {sum(deleted_counts.values())}")
    print("="*80 + "\n")

    return deleted_counts

def verify_cleanup():
    """Проверка результатов очистки"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print_header("ПРОВЕРКА РЕЗУЛЬТАТОВ ОЧИСТКИ")

    # 1. Оставшиеся сессии
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN completion_status = 'in_progress' THEN 1 END) as in_progress
        FROM sessions
    """)
    sessions = cur.fetchone()
    print(f"1. Сессии: {sessions['total']} (completed: {sessions['completed']}, in_progress: {sessions['in_progress']})")

    # 2. Grant applications
    cur.execute("SELECT COUNT(*) as count FROM grant_applications")
    apps = cur.fetchone()['count']
    print(f"2. Grant applications: {apps}")

    # 3. Grants
    cur.execute("""
        SELECT
            COUNT(*) as total,
            MIN(LENGTH(grant_content)) as min_len,
            MAX(LENGTH(grant_content)) as max_len,
            AVG(LENGTH(grant_content))::int as avg_len
        FROM grants
    """)
    grants = cur.fetchone()
    print(f"3. Grants: {grants['total']} (content length: min={grants['min_len']}, max={grants['max_len']}, avg={grants['avg_len']})")

    # 4. Researcher research
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
        FROM researcher_research
    """)
    research = cur.fetchone()
    print(f"4. Researcher research: {research['total']} (completed: {research['completed']}, pending: {research['pending']})")

    # 5. User answers
    cur.execute("SELECT COUNT(*) as count FROM user_answers")
    answers = cur.fetchone()['count']
    print(f"5. User answers: {answers}")

    # 6. Полные заявки (с всеми артефактами)
    cur.execute("""
        SELECT
            s.anketa_id,
            u.username,
            s.completion_status,
            COUNT(ua.id) as answers_count,
            ga.id as grant_app_id,
            g.id as grant_id,
            rr.id as research_id
        FROM sessions s
        JOIN users u ON s.telegram_id = u.telegram_id
        LEFT JOIN user_answers ua ON ua.session_id = s.id
        LEFT JOIN grant_applications ga ON ga.session_id = s.id
        LEFT JOIN grants g ON g.anketa_id = s.anketa_id
        LEFT JOIN researcher_research rr ON rr.anketa_id = s.anketa_id
        WHERE s.completion_status = 'completed'
        GROUP BY s.anketa_id, u.username, s.completion_status, ga.id, g.id, rr.id
        ORDER BY s.anketa_id
    """)

    print("\n6. Polnye completed zaiavki s artefaktami:")
    completed = cur.fetchall()
    for row in completed:
        has_all = "[OK]" if row['answers_count'] > 0 and row['grant_app_id'] and row['grant_id'] and row['research_id'] else "[NO]"
        print(f"   {has_all} {row['anketa_id']} ({row['username']}): answers={row['answers_count']}, app={row['grant_app_id']}, grant={row['grant_id']}, research={row['research_id']}")

    cur.close()
    conn.close()

    print("\n" + "="*80 + "\n")

def main():
    """Главная функция"""
    print("\n" + "="*80)
    print("DATABASE GARBAGE COLLECTION")
    print("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)

    # Шаг 1: Анализ
    analyze_database()

    # Шаг 2: DRY RUN
    print("\n" + "="*80)
    print("Запустить DRY RUN? (только показать что будет удалено)")
    print("="*80)
    response = input("Нажмите Enter для продолжения или Ctrl+C для отмены: ")
    cleanup_database(dry_run=True)

    # Шаг 3: Реальное удаление
    print("\n" + "="*80)
    print("ВНИМАНИЕ! Сейчас будет выполнено РЕАЛЬНОЕ УДАЛЕНИЕ!")
    print("="*80)
    response = input("Введите 'DELETE' для подтверждения: ")

    if response.strip() == 'DELETE':
        cleanup_database(dry_run=False)

        # Шаг 4: Проверка
        verify_cleanup()

        print("\n[SUCCESS] OCHISTKA ZAVERSHENA USPESHNO!\n")
    else:
        print("\n[CANCEL] Otmeneno polzovatelem\n")

if __name__ == '__main__':
    main()
