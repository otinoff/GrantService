#!/bin/bash

echo "========================================"
echo "  GrantService Streamlit Test"
echo "  Testing Authorization System"
echo "========================================"
echo ""
echo "Starting Streamlit on http://localhost:8501"
echo ""
echo "Test credentials:"
echo "  Admin: ID=123456789, Token=admin_token"
echo "  Editor: ID=987654321, Token=editor_token"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Запускаем Streamlit
streamlit run test_streamlit_auth.py --server.port 8501