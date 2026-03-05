@echo off
chcp 65001 >nul
setlocal

title Controlling — Запуск (Launch)

REM Путь к проекту — можно запускать start.bat откуда угодно (рабочий стол, ярлык)
set "PROJECT_ROOT=e:\PROGECTS\kontrolling"
cd /d "%PROJECT_ROOT%"

echo ============================================
echo   Controlling — ЗАПУСК (Launch)
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

echo Проверка Docker...
docker info >nul 2>&1
if %ERRORLEVEL% equ 0 goto docker_ready

echo Docker не запущен. Запускаем Docker Desktop...
set "DOCKER_DESKTOP=C:\Program Files\Docker\Docker\Docker Desktop.exe"
if not exist "%DOCKER_DESKTOP%" set "DOCKER_DESKTOP=C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe"
if exist "%DOCKER_DESKTOP%" (
    start "" "%DOCKER_DESKTOP%"
) else (
    echo [ОШИБКА] Docker Desktop не найден по пути:
    echo   C:\Program Files\Docker\Docker\Docker Desktop.exe
    echo Установите Docker Desktop или укажите путь в start.bat.
    echo.
    pause
    exit /b 1
)

echo Ожидание готовности Docker (до 90 сек)...
set WAIT=0
:wait_loop
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if %ERRORLEVEL% equ 0 goto docker_ready
set /a WAIT+=5
if %WAIT% geq 90 (
    echo.
    echo [ОШИБКА] Docker не ответил за 90 сек. Запустите Docker Desktop вручную и повторите start.bat.
    echo.
    pause
    exit /b 1
)
echo   ожидание... %WAIT% сек
goto wait_loop

:docker_ready
echo Docker доступен.
echo.

echo Сборка образов и запуск контейнеров: db, backend...
echo Подождите, это может занять 1–3 минуты при первом запуске.
echo.
docker compose up --build -d

if %ERRORLEVEL% neq 0 (
    echo.
    echo --------------------------------------------
    echo [ОШИБКА] Запуск не удался.
    echo Проверьте: Docker Desktop запущен и не занят другими задачами.
    echo --------------------------------------------
    echo.
    pause
    exit /b 1
)

echo.
echo --------------------------------------------
echo Статус контейнеров (должны быть Up):
echo --------------------------------------------
docker compose ps
echo.

echo --------------------------------------------
echo Последние строки логов (проверка, что сервисы стартовали):
echo --------------------------------------------
docker compose logs --tail=20
echo.

echo ============================================
echo   БАЗА И API ЗАПУЩЕНЫ
echo ============================================
echo   Backend API:  http://localhost:8000
echo   Swagger/docs: http://localhost:8000/docs
echo.
echo   Фронтенд (единственная версия приложения):
echo   Запустите в отдельном окне из корня проекта:
echo     npm run dev
echo   Затем откройте в браузере: http://localhost:5173
echo ============================================
echo.
echo Остановить контейнеры: запустите stop.bat
echo Смотреть логи: docker compose logs -f
echo.
echo Нажмите любую клавишу, чтобы закрыть это окно.
echo Контейнеры продолжат работать в фоне.
echo.
pause
