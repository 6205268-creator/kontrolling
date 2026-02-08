# Руководство по синхронизации с репозиторием

## Где вводить команды

Все команды ниже вводятся в **терминале**:

- **В Cursor:** меню **Terminal → New Terminal** (или **Ctrl+`**). Внизу откроется панель — вводите команды туда.
- **Вне Cursor:** откройте **PowerShell** или **Командную строку** Windows, перейдите в папку проекта: `cd e:\PROGECTS\kontrolling`, затем вводите команды.

Каждую команду вводите и нажимайте **Enter**.

---

## Текущее состояние

- Репозиторий: Git, ветка `main`, remote `origin`.
- Локальные папки: `docs/`, `domains/`, `.cursor/` — должны быть под версионированием (кроме исключённых в `.gitignore`).

## Ежедневная синхронизация

### 1. Перед началом работы

```powershell
cd e:\PROGECTS\kontrolling
git pull origin main
```

### 2. После изменений (добавлены/изменены файлы)

```powershell
git status
git add <файлы или папки>
git commit -m "Краткое описание изменений"
git push origin main
```

### 3. Добавление новых папок в репозиторий

```powershell
git add docs/
git add domains/
git add .cursor/
git status
git commit -m "Добавлены docs, domains, правила Cursor"
git push origin main
```

## Что коммитить

| Папка / файл      | Коммитить |
|-------------------|-----------|
| `docs/architecture/` | Да |
| `domains/`        | Да |
| `.cursor/rules/*.mdc` | Да (правила проекта) |
| Локальные секреты, кэш, venv | Нет (должны быть в `.gitignore`) |

## Восстановление удалённых файлов (если нужно вернуть из Git)

```powershell
# Вернуть один файл
git restore --source=HEAD -- path/to/file

# Вернуть все удалённые файлы из последнего коммита
git restore .
```

## Конфликты при pull

Если при `git pull` есть конфликты:

```powershell
# После разрешения конфликтов в файлах
git add .
git commit -m "Разрешены конфликты после pull"
git push origin main
```

## Рекомендация

- Делать коммиты по логическим изменениям (одна задача — один коммит).
- Перед большими изменениями создавать ветку: `git checkout -b feature/название`, затем merge в `main` через PR или `git merge`.
