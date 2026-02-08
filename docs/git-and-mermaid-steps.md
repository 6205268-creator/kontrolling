# Пошаговая инструкция: .gitignore, коммит архитектуры, GitHub, пуш, проверка Mermaid

## 1. Создать .gitignore для Python + Mermaid

**Файл:** `.gitignore` в корне проекта.

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
.env
*.egg-info/
.eggs/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# Mermaid / IDE
*.log
.DS_Store
Thumbs.db
```

Команда (PowerShell, из корня проекта):

```powershell
cd e:\PROGECTS\kontrolling
```

Создать файл вручную или через редактор и сохранить как `.gitignore`.

---

## 2. Закоммитить все файлы архитектуры

```powershell
git add .gitignore docs/ domains/ .cursor/
git status
git commit -m "Add .gitignore, docs architecture, domains, Cursor rules"
```

---

## 3. Привязать удалённый репозиторий GitHub

Если remote ещё не задан:

```powershell
git remote add origin https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПОЗИТОРИЙ.git
```

Если `origin` уже есть и нужно сменить URL:

```powershell
git remote set-url origin https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПОЗИТОРИЙ.git
git remote -v
```

---

## 4. Пуш в main

```powershell
git push -u origin main
```

---

## 5. Проверить рендеринг Mermaid на GitHub

1. Открыть в браузере: `https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПОЗИТОРИЙ`
2. Перейти в файл с Mermaid (например `docs/architecture/common/system-context-l1.mmd` или любой `.md` с блоком ` ```mermaid `).
3. GitHub рендерит Mermaid в `.md`; для `.mmd` показывается исходный код — для проверки рендера открыть соответствующий `.md` или скопировать блок из `.mmd` в новый `.md` и открыть его на GitHub.

---

## План (сводка)

| Шаг | Действие |
|-----|----------|
| 1 | Создать `.gitignore` (Python + Mermaid), сохранить в корне |
| 2 | `git add .gitignore docs/ domains/ .cursor/` → `git commit -m "..."` |
| 3 | `git remote add origin <URL>` или `git remote set-url origin <URL>` |
| 4 | `git push -u origin main` |
| 5 | Открыть репозиторий на GitHub → открыть файл с Mermaid в `.md` → проверить отображение диаграммы |
