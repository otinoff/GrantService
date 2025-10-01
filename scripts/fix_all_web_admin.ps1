# PowerShell скрипт для исправления всех импортов в web-admin/pages
# Работает с файлами, содержащими эмодзи

$ErrorActionPreference = "Continue"
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host "PowerShell Import Fixer for web-admin/pages" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

$pagesDir = "C:\SnowWhiteAI\GrantService\web-admin\pages"
$fixedCount = 0

# Получаем все Python файлы
$files = Get-ChildItem -Path $pagesDir -Filter "*.py"
Write-Host "`nFound $($files.Count) Python files" -ForegroundColor Green

foreach ($file in $files) {
    # Пропускаем уже исправленные файлы
    if ($file.Name -eq "__init__.py" -or $file.Name -eq "👥_Пользователи.py") {
        Write-Host "  [SKIP] $($file.Name) - already fixed" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "  Processing: $($file.Name)" -ForegroundColor Gray
    
    # Читаем содержимое файла
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $originalContent = $content
    
    # Замена импортов
    $content = $content -replace 'from web_admin\.utils\.auth import is_user_authorized', 'from utils.auth import is_user_authorized'
    
    # Замена Linux путей
    $pathReplacement = @"
# Добавляем пути кроссплатформенно
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # web-admin
grandparent_dir = os.path.dirname(parent_dir)  # GrantService
sys.path.insert(0, grandparent_dir)  # Для импорта config и data
sys.path.insert(0, parent_dir)  # Для импорта utils
"@
    
    $content = $content -replace "sys\.path\.append\('/var/GrantService'\)", $pathReplacement
    
    # Замена путей к странице входа
    $content = $content -replace '"/var/GrantService/web-admin/pages/🔐_Вход\.py"', 'os.path.join(current_dir, "🔐_Вход.py")'
    
    # Если содержимое изменилось, сохраняем
    if ($content -ne $originalContent) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
        Write-Host "  [FIXED] $($file.Name)" -ForegroundColor Green
        $fixedCount++
    } else {
        Write-Host "  [OK] $($file.Name)" -ForegroundColor Blue
    }
}

Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
Write-Host "Fixed $fixedCount files" -ForegroundColor Green
Write-Host "Done!" -ForegroundColor Cyan