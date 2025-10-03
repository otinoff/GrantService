#!/bin/bash
# Quick pages check without headless browser
# Uses curl to verify all pages return 200
# Author: Deployment Manager Agent
# Version: 1.0.0

set -e

BASE_URL="https://grantservice.onff.ru"

echo "========================================="
echo "Quick Pages Check - GrantService Admin"
echo "========================================="
echo ""

declare -a PAGES=(
    ""  # Dashboard
    "📄_Гранты"
    "👥_Пользователи"
    "📊_Аналитика"
    "🤖_Агенты"
    "⚙️_Настройки"
)

declare -a PAGE_NAMES=(
    "Dashboard"
    "Grants"
    "Users"
    "Analytics"
    "Agents"
    "Settings"
)

TOTAL=0
PASSED=0
FAILED=0

for i in "${!PAGES[@]}"; do
    PAGE="${PAGES[$i]}"
    NAME="${PAGE_NAMES[$i]}"
    URL="${BASE_URL}/${PAGE}"

    # Get HTTP status
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL" --max-time 15)

    TOTAL=$((TOTAL + 1))

    if [ "$STATUS" = "200" ]; then
        echo "✅ [$STATUS] $NAME"
        PASSED=$((PASSED + 1))
    else
        echo "❌ [$STATUS] $NAME"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "========================================="
echo "Results: $PASSED/$TOTAL passed, $FAILED failed"

if [ $FAILED -eq 0 ]; then
    echo "✅ All pages responding!"
    echo "========================================="
    exit 0
else
    echo "❌ Some pages failed!"
    echo "========================================="
    exit 1
fi
