#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2
import json

conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='root', database='grantservice')
cur = conn.cursor()
cur.execute("SELECT anketa_id, interview_data FROM sessions WHERE telegram_id=999999997 AND status='completed' ORDER BY id DESC LIMIT 1")
row = cur.fetchone()
data = json.loads(row[1]) if isinstance(row[1], str) else row[1]
with open('sample_anketa_iter41.json', 'w', encoding='utf-8') as f:
    json.dump({'anketa_id': row[0], 'interview_data': data}, f, ensure_ascii=False, indent=2)
print('Saved to sample_anketa_iter41.json')
conn.close()
