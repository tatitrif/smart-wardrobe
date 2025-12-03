# Smart wardrobe

## Описание

Проект Умный гардероб.

## Технологии

- **Backend**: FastAPI, SQLAlchemy 2.0+, async
- **Зависимости**: uv, pydantic, orjson, python-json-logger
- **Логирование**: структурированное (JSON), trace_id для трейсинга
- **Безопасность**: маскировка токенов, soft-delete

## Структура проекта

- `smart-wardrobe/`
  - `backend/` - Fastapi-приложение (API)
  - `.gitignore` - определяет игнорируемые файлы и каталоги для Git
  - `.pre-commit-config.yaml` - Конфигурация хуков
  - `pyproject.toml` - Конфигурация проекта
  - `README.md` - информация о проекте

## Pre-commit

Проект использует фреймворк .pre-commit-config.yaml для автоматической проверки кода, например, линтинг, форматирование или запуск тестов, перед отправкой изменений в репозиторий.

```bash

# установить pre-commit
pip install pre-commit==3.8.0

# активировать pre-commit в репозиторий
pre-commit install

# запустить pre-commit без коммита
pre-commit run --all-files

# сделать коммит, пропустив хуки (только в исключительных случаях)
git commit --no-verify -m "<message>"

```
