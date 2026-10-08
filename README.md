# WikiViz

Веб-сервис для автоматического преобразования статей Wikipedia в интерактивное визуальное представление: URL статьи → MediaWiki API → извлечение структурированных данных → единая модель → подбор виджетов → страница результата.

## Статус

**Phase 0–6 из Roadmap закрыты** (октябрь 2026). Готово:
- извлечение разделов, инфобокса, таблиц, координат, изображений, дат и чисел (en и ru);
- семь виджетов: таблица, галерея, карта, оглавление, временная шкала, карточка инфобокса, столбчатая диаграмма.

Пользовательской страницы пока нет: виджеты видны только на служебной странице `/dev/widgets` на пяти заранее выгруженных статьях. Следующие шаги — в `docs/PLAN.md`.

## Документы

| Файл | Что внутри |
|---|---|
| `docs/PROGRESS.md` | текущее состояние, решения, техдолг — начинать с него |
| `docs/PLAN.md` | план следующих сессий |
| `docs/WikiViz - Техническое задание (ТЗ).md` | ТЗ v3.1 |
| `docs/WikiViz 3.1 RoadMap.md` | Roadmap v3.1 |
| `docs/PHASE6_REPORT.md` | итоговый отчёт Phase 6 |

## Структура

```
backend/    Python 3.13, FastAPI: клиент Wikipedia, extractors, модели (Pydantic), тесты (pytest)
frontend/   Next.js 16, React, TypeScript: типы модели, виджеты, dev-страницы, тесты (Jest)
docs/       ТЗ, Roadmap, ход работы
```

## Запуск для разработки

### Backend

Windows (PowerShell):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload      # http://localhost:8000/health
```

Linux / macOS:
```bash
cd backend
python3.13 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m pytest
./venv/bin/uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run build        # на свежей копии — до tsc: сборка создаёт типы Next.js
npx tsc --noEmit
npm test
npm run dev          # http://localhost:3000/dev/widgets
```

### Проверки перед слиянием в `main`

`pytest` (backend), `npm run build`, `npx tsc --noEmit`, `npm test` (frontend) — все должны быть чистыми. Jest не проверяет типы, поэтому `tsc` обязателен.

### Фикстуры (реальные статьи)

Пять статей с закреплёнными ревизиями — `frontend/tests/fixtures/real/manifest.json`. Выгрузка (нужна сеть, из папки `backend` с активным venv):

```bash
python -m scripts.export_fixtures            # по закреплённым ревизиям
python -m scripts.export_fixtures --update   # взять текущие версии и обновить манифест
```

После изменения extractor'а фикстуры перевыгружаются; повторный запуск не должен менять `git diff`.

### Docker

`docker-compose.yml` описывает frontend, backend и Redis. В Phase 6 сборка через Docker не проверялась; полноценный запуск в Docker — часть Phase 14 (MVP).
