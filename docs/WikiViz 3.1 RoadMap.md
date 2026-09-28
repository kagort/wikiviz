# WikiViz

## Roadmap разработки

**Версия:** 3.1

**Цель:** последовательная разработка WikiViz одним разработчиком от пустого репозитория до расширяемой платформы анализа и визуализации документов.

---

# 0. Общая стратегия

Разработка делится на четыре уровня:

```text
LEVEL 1
Foundation
↓
LEVEL 2
Wikipedia MVP
↓
LEVEL 3
Intelligent WikiViz
↓
LEVEL 4
Universal Text Analysis Platform
```

Главное правило:

> **Новая функция добавляется через новый источник, модуль, extractor, transformer, NLP-компонент или widget, а не через переписывание существующего ядра.**

---

# PHASE 0 — Project Foundation

Без изменений.

---

# PHASE 1 — Architecture Contracts

Без изменений.

---

# PHASE 2 — Wikipedia Client

Без изменений.

---

# PHASE 3 — Article Normalization

Без изменений по функциональности MVP.

Однако уже на этом этапе необходимо соблюдать архитектурный принцип:

> Wikipedia Article Model не должен становиться единственной внутренней моделью документа.

В дальнейшем `Article` должен рассматриваться как специализированное представление Wikipedia-документа поверх универсального `NormalizedDocument`.

---

# PHASE 4 — Basic Extractors

Без изменений.

---

# PHASE 5 — Widget Framework

Без изменений.

---

# PHASE 6 — Первые Widgets

Без изменений.

---

# PHASE 7 — Widget Selector

Без изменений.

---

# PHASE 8 — Result System

Без изменений.

---

# PHASE 9 — Cache

Без изменений.

---

# PHASE 10 — Security

Без изменений.

---

# PHASE 11 — Error Handling

Без изменений.

---

# PHASE 12 — Test Corpus

Без изменений.

---

# PHASE 13 — Automated Testing

Без изменений.

---

# PHASE 14 — MVP

MVP объявляется завершённым после прохождения полного сценария:

```text
Wikipedia URL
      ↓
Validation
      ↓
MediaWiki API
      ↓
Normalization
      ↓
Extraction
      ↓
Widget selection
      ↓
Visualization
      ↓
Redis
      ↓
UUID result page
```

На этом этапе WikiViz является устойчивым сервисом анализа Wikipedia.

---

# === ПОСЛЕ MVP ===

После MVP архитектура постепенно расширяется от Wikipedia-specific системы к универсальной платформе обработки документов.

---

# PHASE 15 — Universal Document Model

## Цель

Отделить внутреннюю модель данных от Wikipedia.

Создать универсальную абстракцию:

```text
NormalizedDocument
```

Она должна быть способна описывать как:

```text
Wikipedia article
```

так и:

```text
plain text
TXT
Markdown
HTML
```

в последующих версиях.

Концептуальная структура:

```text
NormalizedDocument
│
├── metadata
├── structure
├── content
├── entities
├── relations
├── linguistic_data
└── provenance
```

### Основные сущности

```text
Document
Section
Paragraph
Sentence
List
Table
Image
Link
Entity
EntityMention
Relation
```

### Требование

NLP и Widgets не должны зависеть от Wikipedia-specific HTML или MediaWiki API.

---

# PHASE 16 — Source Adapter Layer

## Цель

Изолировать различные источники документов.

Создать архитектурную абстракцию:

```text
SourceAdapter
```

Первый реализованный источник:

```text
WikipediaAdapter
```

В будущем:

```text
TxtAdapter
PlainTextAdapter
MarkdownAdapter
HtmlAdapter
PdfAdapter
DocxAdapter
```

Архитектура:

```text
Wikipedia ──→ WikipediaAdapter ──┐
                                │
TXT ───────→ TxtAdapter ────────┤
                                ↓
                         NormalizedDocument
```

### Требование

Добавление нового источника не должно требовать изменения:

- NLP Engine;
    
- существующих extractors;
    
- WidgetRegistry;
    
- существующих widgets;
    
- ResultPage.
    

---

# PHASE 17 — NLP Foundation

## Цель

Создать независимый NLP Engine.

NLP Engine принимает:

```text
NormalizedDocument
```

и добавляет лингвистическую информацию.

Первый этап:

```text
sentence segmentation
tokenization
lemmatization
part-of-speech
morphology
dependency parsing
```

Результаты сохраняются в универсальной модели.

Например:

```text
Document
 ↓
Sentence[]
 ↓
Token[]
 ↓
Lemma
POS
Morphology
Dependency
```

NLP Engine не должен знать, был ли документ получен из:

```text
Wikipedia
TXT
Markdown
HTML
```

---

# PHASE 18 — Entity Layer

## Цель

Добавить универсальную модель сущностей.

Типы:

```text
Person
Location
Organization
Event
Work
Concept
Unknown
```

Создать:

```text
Entity
EntityType
EntityMention
EntityReference
```

Каждая сущность должна по возможности содержать:

```text
id
type
label
description
source
confidence
provenance
```

---

# PHASE 19 — NER

## Цель

Научить NLP Engine извлекать сущности из произвольного текста.

Например:

```text
Albert Einstein was born in Ulm in 1879.
```

может преобразовываться в:

```text
PERSON
    Albert Einstein

LOCATION
    Ulm

DATE
    1879
```

Источником таких сущностей является:

```text
source = nlp
```

### Требование

NER должен работать одинаково для:

```text
Wikipedia
TXT
Markdown
HTML
```

после их преобразования в `NormalizedDocument`.

---

# PHASE 20 — User Text Input

## Цель

Добавить возможность анализа произвольного пользовательского текста.

Поддержать:

```text
plain text input
TXT file
```

### Сценарий

```text
User
 ↓
Paste text / upload TXT
 ↓
Text Adapter
 ↓
NormalizedDocument
 ↓
NLP Engine
 ↓
Entities
 ↓
Linguistic analysis
 ↓
Widget Selector
 ↓
Visualization
```

### UI

Добавить отдельный режим:

```text
Analyze Wikipedia
Analyze Text
```

или единый интерфейс выбора источника:

```text
Source:
○ Wikipedia URL
○ Text
○ TXT file
```

### Ограничения

На первом этапе:

- ограничить размер пользовательского текста;
    
- валидировать вход;
    
- безопасно обрабатывать Unicode;
    
- не выполнять пользовательский HTML;
    
- не интерпретировать TXT как HTML;
    
- ограничивать время NLP-обработки.
    

---

# PHASE 21 — Entity Visualization

## Цель

Визуализировать сущности, извлечённые NLP.

Добавить:

```text
EntityCards
EntityList
EntityHighlights
```

Возможности:

- группировка по типу;
    
- сортировка;
    
- фильтрация;
    
- переход к месту упоминания;
    
- отображение confidence;
    
- отображение source.
    

Например:

```text
PERSON
 ├── Albert Einstein
 ├── Max Planck
 └── Niels Bohr

LOCATION
 ├── Ulm
 ├── Berlin
 └── Princeton
```

---

# PHASE 22 — Provenance and Mentions

## Цель

Связать извлечённые сущности с исходным текстом.

Каждый `EntityMention` должен по возможности хранить:

```text
document_id
sentence_id
start_offset
end_offset
text
entity_id
confidence
source
```

Это позволяет реализовать:

```text
Entity
   ↓
Mentions
   ↓
Original text
```

и подсвечивать найденные сущности непосредственно в тексте.

---

# PHASE 23 — Relation Extraction

## Цель

Добавить извлечение отношений между сущностями.

Первоначальный набор:

```text
PERSON → born_in → LOCATION
PERSON → member_of → ORGANIZATION
PERSON → authored → WORK
PERSON → died_in → LOCATION
EVENT → occurred_in → LOCATION
PERSON → participated_in → EVENT
```

Каждая связь:

```json
{
  "source": "entity-1",
  "relation": "authored",
  "target": "entity-2",
  "confidence": 0.82,
  "source": "nlp"
}
```

Relation extraction является независимым модулем и не должен изменять Entity API.

---

# PHASE 24 — EntityGraph

## Цель

Создать граф сущностей и отношений.

Источник данных:

```text
Entity[]
Relation[]
```

Graph не должен создавать собственную альтернативную модель сущностей.

Функции:

- nodes;
    
- edges;
    
- zoom;
    
- pan;
    
- filtering;
    
- graph depth;
    
- node details;
    
- relation details;
    
- grouping by entity type.
    

Архитектура:

```text
NormalizedDocument
       ↓
Entity[]
       ↓
Relation[]
       ↓
EntityGraph
```

---

# PHASE 25 — Intelligent Widget Selection

## Цель

Расширить Rule-based Selector с учётом NLP.

Пример:

```text
locations > 0
    → MapWidget

people > 5
    → EntityCards

events > 5
    → TimelineWidget

relations > 3
    → EntityGraph

numericSeries > 1
    → StatisticsChart
```

Selector должен оставаться независимым от источника.

---

# PHASE 26 — Wikidata Integration

Без изменений по основной идее.

```text
Wikipedia
    ↓
Entity
    ↓
Wikidata ID
    ↓
Additional structured information
```

Wikidata рассматривается как дополнительный источник данных, а не как обязательная часть NLP.

---

# PHASE 27 — Advanced Widgets

Добавлять по одному:

```text
EntityCards
EntityGraph
GlossaryWidget
RelationMatrix
AdvancedTimeline
ComparativeChart
EntityMap
NetworkStatistics
```

Каждый widget подключается через:

```text
WidgetRegistry
```

---

# PHASE 28 — Additional Text Formats

## Цель

Расширить Source Adapter Layer.

Добавить:

```text
Markdown
HTML
PDF
DOCX
```

Каждый формат должен иметь собственный adapter/parser.

Общий pipeline:

```text
Source
 ↓
Adapter
 ↓
NormalizedDocument
 ↓
NLP
 ↓
Visualization
```

NLP Engine и Widget API при этом не изменяются.

---

# PHASE 29 — PDF Export

Без изменений.

---

# PHASE 30 — Internationalization

Без изменений.

---

# PHASE 31 — Performance

После появления NLP необходимо отдельно оптимизировать:

- NLP model loading;
    
- NLP model caching;
    
- batch processing;
    
- parallel extraction;
    
- lazy loading widgets;
    
- Redis caching;
    
- background processing;
    
- large document processing.
    

Для больших пользовательских документов предпочтителен асинхронный pipeline.

---

# PHASE 32 — Background Jobs

Архитектура:

```text
POST /analyze
       ↓
Job
       ↓
Worker
       ↓
Source Adapter
       ↓
Normalization
       ↓
Extraction / NLP
       ↓
Result
```

Статусы:

```text
queued
processing
ready
error
```

Это особенно важно для:

- больших TXT;
    
- PDF;
    
- DOCX;
    
- NLP;
    
- relation extraction;
    
- графов;
    
- PDF export.
    

---

# PHASE 33 — Observability

Добавить:

```text
source type
document size
processing time
NLP processing time
entities extracted
relations extracted
widget selection
cache hit/miss
errors
```

Это позволит сравнивать производительность различных источников.

---

# PHASE 34 — Production

Без изменений по общей концепции.

---

# PHASE 35 — Research Layer

После стабилизации технической платформы можно проводить исследования.

## Extraction quality

Оценивать:

```text
precision
recall
F1
```

для:

- entities;
    
- dates;
    
- locations;
    
- organizations;
    
- events;
    
- relations.
    

## NLP quality

Исследовать:

- качество NER;
    
- качество dependency parsing;
    
- качество relation extraction;
    
- переносимость моделей между языками;
    
- влияние длины документа;
    
- влияние структуры текста.
    

## Visualization quality

Исследовать:

- корректность WidgetSelector;
    
- информативность визуализаций;
    
- потерю информации при нормализации;
    
- когнитивную нагрузку различных представлений.
    

---

# PHASE 36 — Universal Text Analysis Platform

## Конечная архитектурная цель

WikiViz постепенно превращается из:

```text
Wikipedia visualization tool
```

в:

```text
Universal Text Analysis & Visualization Platform
```

Итоговый pipeline:

```text
                    ┌── Wikipedia
                    │
                    ├── TXT
                    ├── Plain Text
                    ├── Markdown
                    ├── HTML
                    ├── PDF
                    ├── DOCX
                    └── API
                         ↓
                 ┌───────────────┐
                 │ Source Layer  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │   Parsers     │
                 └───────┬───────┘
                         ↓
              ┌─────────────────────┐
              │ Normalized Document │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │   NLP Engine        │
              └──────────┬──────────┘
                         ↓
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
      Entities       Relations      Linguistics
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                Structured Knowledge
                         ↓
                 Widget Selector
                         ↓
                  Widget Registry
                         ↓
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Tables          Graph          Timeline
          ↓              ↓              ↓
        Map            Charts        Entity Cards
                         ↓
                   Result / Export
```

---

# Критические контрольные точки

## Checkpoint A

После Phase 1:

> Можно получить и отобразить fixture через API.

## Checkpoint B

После Phase 3:

> Реальная Wikipedia статья превращается в Normalized Article.

## Checkpoint C

После Phase 7:

> Система автоматически выбирает виджеты.

## Checkpoint D

После Phase 14:

> **Wikipedia MVP готов.**

## Checkpoint E

После Phase 15:

> Wikipedia-specific модель отделена от универсальной модели документа.

## Checkpoint F

После Phase 17:

> NLP Engine работает с NormalizedDocument независимо от источника.

## Checkpoint G

После Phase 20:

> Пользователь может передать TXT/plain text и получить NLP-анализ.

## Checkpoint H

После Phase 23:

> Entities + Relations извлекаются независимо от источника.

## Checkpoint I

После Phase 24:

> EntityGraph строится поверх существующей модели.

## Checkpoint J

После Phase 28:

> Несколько форматов документов используют единый pipeline.

---

# Главный критерий расширяемости

После завершения MVP разработчик должен иметь возможность добавить:

```text
TxtAdapter
```

не изменяя:

```text
NLP Engine
WikipediaAdapter
WidgetRegistry
MapWidget
TableWidget
TimelineWidget
EntityGraph
```

Добавить:

```text
NewEntityExtractor
```

не изменяя:

```text
Source Layer
Widget Layer
Redis
API
```

Добавить:

```text
NewWidget
```

не изменяя:

```text
Source Adapters
Extractors
NLP Engine
```

Если добавление нового источника, extractor или widget требует переписывания ядра, архитектура считается неудовлетворительной.

---

# Основной архитектурный принцип

> **WikiViz сначала является Wikipedia-проектом, но архитектурно с самого начала строится как платформа обработки документов.**

Wikipedia — первый источник.

TXT — первый будущий внешний источник.

NLP — независимый слой анализа.

Widgets — независимый слой представления.

`NormalizedDocument` — главный контракт между ними.