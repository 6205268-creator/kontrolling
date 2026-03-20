# GitHub: готовые команды (копируй в терминал)

Все команды для **PowerShell** на Windows. Репозиторий: `e:\PROGECTS\kontrolling`. Удалённый репозиторий обычно называется `origin`.

Если путь к проекту у тебя другой — замени только первую строку `Set-Location`.

---

## 1. Зайти в проект и проверить ветку

```powershell
Set-Location "e:\PROGECTS\kontrolling"
git status
git branch
```

---

## 2. Выложить ветку сценария на GitHub (если ещё не пушили)

Ветка с документами сценария: `docs/scenario-life-year-matrix`.

```powershell
Set-Location "e:\PROGECTS\kontrolling"
git checkout docs/scenario-life-year-matrix
git push -u origin docs/scenario-life-year-matrix
```

После этого на GitHub появится ветка; можно открыть **Compare & pull request** в веб-интерфейсе.

---

## 3. Создать НОВУЮ ветку от актуального main и сразу запушить на GitHub

Имя ветки замени при необходимости (латиница, без пробелов). Пример: `feature/scenario-runner-smoke`.

```powershell
Set-Location "e:\PROGECTS\kontrolling"
git fetch origin
git checkout main
git pull origin main
git checkout -b feature/scenario-runner-smoke
git push -u origin feature/scenario-runner-smoke
```

---

## 4. Только создать новую ветку локально (без push)

```powershell
Set-Location "e:\PROGECTS\kontrolling"
git fetch origin
git checkout main
git pull origin main
git checkout -b имя-новой-ветки
```

Потом, когда будут коммиты:

```powershell
git push -u origin имя-новой-ветки
```

---

## 5. Если установлен GitHub CLI (`gh`): создать PR из ветки сценария в main

Сначала ветка должна быть на GitHub (п. 2). Затем:

```powershell
Set-Location "e:\PROGECTS\kontrolling"
gh pr create --base main --head docs/scenario-life-year-matrix --title "docs: сценарий жизни СТ (матрица + ТЗ)" --body "Матрица EVT-001-024, ТЗ раннера, промпт, пример выписки. См. docs/scenario/README.md"
```

Если `gh` не установлен — создай PR вручную на сайте GitHub: **Pull requests → New pull request**, base `main`, compare `docs/scenario-life-year-matrix`.

---

## 6. Первый раз настроить `origin` (если клона ещё не было с GitHub)

Подставь свой URL репозитория:

```powershell
Set-Location "e:\PROGECTS\kontrolling"
git remote -v
```

Если пусто или не тот URL:

```powershell
git remote add origin https://github.com/ВАШ_ЛОГИН/kontrolling.git
```

или SSH:

```powershell
git remote add origin git@github.com:ВАШ_ЛОГИН/kontrolling.git
```

---

*Файл для копирования без правок руками; при смене пути проекта достаточно поправить одну строку `Set-Location`.*
