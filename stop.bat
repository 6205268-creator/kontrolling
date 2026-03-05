@echo off
chcp 65001 >nul
setlocal

title Controlling — Остановка (Stop)

REM Путь к проекту — тот же, что в start.bat
set "PROJECT_ROOT=e:\PROGECTS\kontrolling"
cd /d "%PROJECT_ROOT%"

echo ============================================
echo   Controlling — ОСТАНОВКА (Stop)
echo   Папка: %PROJECT_ROOT%
echo ============================================
echo.

if not exist docker-compose.yml (
    echo [ОШИБКА] Файл docker-compose.yml не найден.
    echo Ожидался путь: %PROJECT_ROOT%
    echo.
    pause
    exit /b 1
)

echo Сейчас запущены такие контейнеры:
echo --------------------------------------------
docker compose ps
echo.

echo Останавливаем и удаляем контейнеры...
echo --------------------------------------------
docker compose down

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ОШИБКА] Команда остановки завершилась с ошибкой.
    echo.
    pause
    exit /b 1
)

echo.
echo Проверка: контейнеров проекта больше не должно быть:
echo --------------------------------------------
docker compose ps
echo.

echo ============================================
echo   ПРОЕКТ ОСТАНОВЛЕН И ВЫГРУЖЕН
echo ============================================
echo   Контейнеры остановлены и удалены.
echo   Данные БД сохранены в volume (при следующем start.bat поднимутся с теми же данными).
echo   Полная очистка с удалением БД: docker compose down -v
echo ============================================
echo.
echo Нажмите любую клавишу, чтобы закрыть окно.
echo.
pause
