# WikiViz — контекст проекта (на 2026-09-23, Phase 6 в процессе)

> Документ для передачи контекста другому AI-агенту или в новый диалог. Содержит: назначение проекта, архитектурные принципы, стек, состояние репозитория, принятые решения и план оставшейся части Phase 6. Подробности сегодняшней сессии (баги, инциденты, точные команды) — в отдельном файле `WikiViz — Сессия 20260923.md`.

---

## 1. Что такое WikiViz

Веб-сервис, преобразующий статьи Wikipedia в интерактивное визуальное представление. URL статьи → MediaWiki API → извлечение структурированных элементов → единая внутренняя модель → подбор виджетов → страница результата с уникальным URL.

Тип проекта: учебный/исследовательский. Один разработчик (доктор философии, преподаёт в вузе, не программист по основной профессии, работает с NLP-терминологией) при постоянном менторстве AI-агента. Обязательны пошаговые объяснения «зачем», инструкции под Windows/PowerShell.

Спецификация: ТЗ v3.1 (собрано и частично восстановлено, §22–35 и §38 отсутствуют) и Roadmap v3.1 (4 уровня: Foundation → Wikipedia MVP → Intelligent WikiViz → Universal Text Analysis Platform).

Долгосрочная перспектива: платформа, где Wikipedia — один из источников (`SourceAdapter`) поверх общего `NormalizedDocument`. Все extractors принимают простую строку HTML, а не Wikipedia-специфичный объект.

---

## 2. Архитектурные принципы

```
Extraction ≠ Transformation ≠ Visualization
Wikipedia → Extractor → Normalized Data → Transformer/Selector → Widget
```

Критерий качества (§40 ТЗ): после MVP можно добавить `PersonExtractor` или `EntityGraph`, не трогая `MapWidget`, `TableWidget`, `TimelineWidget`, Redis, контракт API и `ResultPage`.

Ключевые правила Roadmap:

- Rule 3: Wikipedia HTML не является внутренним API-контрактом (`Section` без html).
- Rule 4: не создавать отдельную модель данных для каждого widget.
- Rule 5: все новые данные сначала попадают в Normalized Data Model.
- Rule 6: все визуализации подключаются через WidgetRegistry — подтверждено на практике трижды (Phase 6): `TableWidget`, `GalleryWidget`, `MapWidget` подключены каждый одной строкой в `lib/widgets/setup.ts`, без единой правки `registry.ts`/`selector.ts`.

---

## 3. Технологический стек

|Слой|Технологии|
|---|---|
|Frontend|Next.js 16 (App Router, Turbopack), React, TypeScript, Tailwind CSS|
|Карта|**react-leaflet** + `leaflet` (архитектурное решение Phase 6 — см. §9.3; НЕ сырой Leaflet)|
|Frontend testing|Jest + `next/jest`, Testing Library|
|Backend|Python 3.x, FastAPI, Pydantic, httpx, BeautifulSoup4, pytest|
|Storage|Redis (результаты + cache, TTL)|
|Infrastructure|Docker, Docker Compose, Git|

Frontend никогда не обращается к Wikipedia напрямую, только через backend.

**Важная техническая заметка окружения (Windows/PowerShell):** консоль по умолчанию использовала устаревшую кодировку `cp866`, из-за чего кириллица при записи файлов через `[System.IO.File]::WriteAllText` могла испортиться. В начале **каждой** новой PowerShell-сессии на этом проекте выполнять:

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

Отдельно: `Get-Content` в Windows PowerShell 5.1 не читает UTF-8 по умолчанию даже после этого фикса — всегда использовать `Get-Content -Encoding utf8` для файлов с кириллицей. `Select-String` с латинским паттерном поиска — надёжный способ проверить содержимое файла независимо от того, как консоль отображает кириллицу.

---

## 4. Нормализованная модель (контракт backend ↔ frontend)

Pydantic (`backend/app/models/`) и TypeScript (`frontend/types/`) синхронизируются вручную.

Поля `NormalizedArticleModel`: `article`, `sections`, `infobox`, `tables`, `locations`, `events`, `numbers`, `people`, `organizations`, `works`, `relations`, `images`, `links`, `metadata`.

Статус заполнения:

- Реальные данные: `article`, `sections`, `tables`, `locations`, `images`, `events`, `numbers`.
- Пустые заглушки: `infobox`, `people`, `organizations`, `works`, `relations`, `links`, `metadata`.
- `article.description` и `article.summary` пока `None`.

**Уточнения по контрактам полей, подтверждённые на практике в Phase 6** (важно при работе с этими типами — не угадывать, проверять `types/*.ts`):

- `Table.source: SourceType` — обязательное поле, легко забыть в тестовых фикстурах (`tsc` ловит, `npm test` — нет).
- `Image.thumbnail_url: string | null` — может быть `null`, тогда используется `url` (полноразмерная версия) как fallback. `Image.caption` и `Image.alt` — независимые `string | null`, оба нередко пусты одновременно.
- `Location.description: string | null` — в реальных данных пока всегда `null`, ни один extractor его не заполняет. `Location.name` может **дублироваться** у разных точек одной статьи (France: два маркера с `name="France"`, разные координаты) — нельзя использовать как единственный различитель, нужна дизамбигуация (например, координатами).

На границе API значения из `fetch().json()` не являются enum автоматически, потребуется явное приведение (`as NormalizedArticleModel`).

---

## 5. Backend (Phases 2–4, завершены; Phase 6 внесла один фикс)

`app/wikipedia/`: без изменений с Phase 2.

`app/extractors/`: `section_extractor`, `section_normalizer`, `table_extractor`, `coordinate_extractor`, `image_extractor`, `date_extractor`, `text_date_extractor`, `number_extractor`, `article_normalizer`.

**Исправление в Phase 6 (`table_extractor.py`):** MediaWiki вставляет в ячейки таблиц скрытые sort-key spans (`style="display:none"`) для корректной сортировки на самой Wikipedia — старая реализация `_cell_text()` (через `stripped_strings`) не отличала их от видимого текста, портя числовые данные (`"3 699 428"` → `"&&&&&&&&03699428.&&&&00 3 699 428"`). Исправлено: фильтрация по цепочке предков на `display:none` перед склейкой. 3 regression-теста. Подробности диагностики — в `WikiViz — Сессия 20260923.md`.

**Осознанно оставленные ограничения (не баги):**

- Текст ошибок Scribunto/Lua-шаблонов не фильтруется в таблицах (нет структурного признака).
- `colspan`/`rowspan` не обрабатываются (ТЗ §12.4).

Тесты: **123**, все offline (было 120). Интеграционные скрипты с реальной сетью: `backend/scripts/` (включая новый разведочный `inspect_table_html.py`).

API (`/api/analyze`, `/api/result/{uuid}`) не реализован.

---

## 6. Frontend: Phase 5 — Widget Framework (завершена)

Контракт `Widget` (`id`, `name`, `version`, `description`, `supports`, `render` как React-компонент), `WidgetRegistry` (класс + глобальный `widgetRegistry`), `selectWidgets` (перебор реестра, устойчив к падению `supports()` одного виджета). Подробности — в предыдущей версии контекст-документа (20260919).

---

## 7. Frontend: Phase 6 — Первые Widgets (В ПРОЦЕССЕ)

### 7.1. Готово: три виджета, зарегистрированы и работают

**`TableWidget`** (`lib/widgets/tableWidget.tsx` + `components/widgets/TableWidgetView.tsx`):

- Просмотр, сортировка (клик по заголовку, `localeCompare`, **строковая, не числовая** — осознанное ограничение MVP, явно согласовано с пользователем), текстовый поиск (регистронезависимый), пагинация (`PAGE_SIZE=10`, порядок `filter→sort→paginate`, сброс страницы при смене фильтра/сортировки).
- `supports = data.tables.length > 0`. Рендерит все таблицы статьи (может быть несколько).

**`GalleryWidget`** (`lib/widgets/galleryWidget.tsx` + `components/widgets/GalleryWidgetView.tsx`):

- Сетка превью (`thumbnail_url ?? url`, `alt ?? caption ?? ''`), lightbox (открытие/закрытие/Escape/навигация с зацикливанием/клавиатура), доступность через `aria-label` на кнопках превью (не полагаться на accessible name из `alt` — конфликтует, когда `alt` заполнен).
- `supports = data.images.length > 0`.

**`MapWidget`** (`lib/widgets/mapWidget.tsx` + `components/widgets/MapWidgetView.tsx` + `lib/widgets/mapGeometry.ts`):

- Библиотека: **react-leaflet** (осознанный выбор, не сырой Leaflet — см. §9.3 старой версии документа / Сессия 20260923).
- Геометрия карты (`computeMapView`: null/single-point/bounds) и текст попапа (`formatPopupText`, всегда включает координаты — из-за дублирующихся `name`) вынесены в чистые, протестированные функции `lib/widgets/mapGeometry.ts`.
- **Сам рендер Leaflet НЕ покрыт юнит-тестами** — ненадёжен в jsdom. Визуальная проверка через служебную dev-страницу `app/dev/map/page.tsx` (Server Component, читает фикстуры) + `components/dev/MapDevClient.tsx` (Client Component, `dynamic(...,{ssr:false})`). Подтверждено пользователем вручную в браузере.
- **Технический урок App Router**: `next/dynamic(...,{ssr:false})` запрещён напрямую в Server Component (`page.tsx` без `'use client'`) — обязательно оборачивать в отдельный Client Component. Тот же паттерн в `mapWidget.tsx` (`MapWidgetRoot`).
- Известная ловушка Leaflet+бандлеры: иконки маркеров по умолчанию ломаются при сборке — исправлено явным `L.icon()` с CDN-ссылками на изображения.
- `scrollWheelZoom={false}` — осознанно, чтобы не мешать прокрутке страницы результата.
- `supports = data.locations.length > 0`.

Точка сборки: `lib/widgets/setup.ts`, импортируется побочным эффектом через `app/layout.tsx` (`import "../lib/widgets/setup"`).

### 7.2. Осталось в Phase 6

- **`SectionNavigator`** — данные (`sections`) полностью готовы, дерево `id`/`title`/`level`/`children`. Простейший из оставшихся, без внешних библиотек. Рекомендуемый следующий шаг.
- **`StatisticsChart`** — данные (`numbers`) готовы. Потребует решения о библиотеке графиков — аналогичная архитектурная развилка, что была с картой (обсудить явно, не выбирать молча).
- **`InfoBoxWidget`** — заблокирован: `infobox` пуст в `NormalizedArticleModel`, `infobox_extractor.py` на backend не создан (ТЗ §11 — сейчас поля инфобокса извлекаются только внутри `date_extractor.py`, для дат; для произвольных полей infobox нужен отдельный extractor). Не начинать, пока backend не готов.

### 7.3. Установленные зависимости Phase 6

```
npm install leaflet react-leaflet
npm install --save-dev @types/leaflet
```

### 7.4. Известный техдолг (не блокирует, но не забыть)

- `types/common.ts` — комментарий над `SourceType.Nlp`/`Wikidata` испорчен кракозябрами (записан до фикса кодировки консоли), не мешает работе, почистить при следующей правке файла.
- Служебные dev-страницы (`app/dev/map/`) не защищены и не исключены из сборки — актуально к моменту деплоя (Phase 10, Security).
- `npm audit`: 3 уязвимости (2 high, 1 critical), разбор отложен до Phase 10, `npm audit fix --force` не применять (риск сломать Next.js).
- `app/layout.tsx`: заголовок/описание всё ещё дефолтные («Create Next App»).

---

## 8. Прогресс по Roadmap

- [x] Phase 0 — Foundation
- [x] Phase 1 — Architecture Contracts
- [x] Phase 2 — Wikipedia Client
- [x] Phase 3 — Article Normalization
- [x] Phase 4 — Basic Extractors (+ фикс `table_extractor.py` в Phase 6)
- [x] Phase 5 — Widget Framework
- [ ] **Phase 6 — Первые Widgets** ← в процессе: `TableWidget`/`GalleryWidget`/`MapWidget` готовы, `SectionNavigator`/`StatisticsChart`/`InfoBoxWidget` — нет
- [ ] Phase 7 — Widget Selector (rule engine)
- [ ] Phase 8+ — Result System, Cache, Security, Error Handling, Test Corpus, Automated Testing, Phase 14 — MVP

---

## 9. Инструменты окружения

- Windows (2 компьютера), VS Code, WSL2 + Ubuntu, Docker Desktop.
- **VPN-прокси** ломает `pip`, `wsl`, httpx и `npm install`; первое действие при сетевой аномалии — проверить VPN.
- **Кодировка консоли** — см. отдельный блок в §3 выше, выполнять в начале каждой сессии.
- Python 3.14.7 / 3.13.7; Node v24 / v22 (в Docker: `python:3.13-slim`, `node:22-alpine`).
- `Out-File -Encoding utf8` добавляет BOM (ломает `.ini`). Для новых файлов — `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))`.
- Многофайловые правки — полной перезаписью файла. Но при большом количестве кириллицы в одном блоке проверять результат через `Select-String` с латинским паттерном, а не полагаться только на отсутствие ошибки PowerShell.
- Копирование длинных PowerShell-блоков иногда обрезается на границе (`MissingExpressionAfterToken`) — при такой ошибке вставлять блок заново целиком, не пытаться угадать, что потерялось.
- В `package.json` скрипты добавлять через `npm pkg set scripts.<name>=<value>`.
- VS Code иногда даёт ложные красные подсветки; финальная проверка только терминалом.
- **`tsc` и `npm test` — проверять и подтверждать раздельно на каждом шаге.** Тесты Jest не ловят все ошибки типов (транслируются через Babel/SWC без полной проверки) — подтверждено дважды в Phase 6 (`Table.source`, `Image.thumbnail_url`).
- Git: два компьютера — `git pull` перед работой, `git push` после каждой сессии. Репозиторий: `https://github.com/kagort/wikiviz` (ветка `main`).

---

## 10. Стиль работы с разработчиком

- Объяснять «зачем», а не только «что»; маленькие шаги с проверкой; ссылки на разделы ТЗ/Roadmap.
- Разведка перед кодом систематически окупается — в Phase 6 дважды привела к находкам, влияющим на дизайн (sort-key мусор в таблицах, дублирующийся `name` в локациях), и один раз — к обнаружению реального бага backend до того, как он попал в виджет.
- Архитектурные развилки — явно на выбор пользователя через `ask_user_input_v0` с обоснованием (числовая vs строковая сортировка; react-leaflet vs сырой Leaflet).
- Regression-тест перед исправлением бага; диагностический скрипт с группировкой находок перед гипотезой.
- Проверка на en и ru обязательна для любого нового extractor'а/механизма, работающего с реальным HTML.
- Библиотеки, не работающие надёжно в тестовой среде (Leaflet), не насилуются юнит-тестами — вместо этого: чистые функции с логикой тестируются отдельно, сам рендер проверяется визуально через служебную dev-страницу, с явным подтверждением пользователя по пунктам.
- В конце сессии/крупного этапа — отдельный лог сессии (детали, находки, инциденты) и обновлённый общий контекст-документ (актуальное состояние, без истории конкретной сессии).