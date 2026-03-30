## 1. Что делает сервис

Сервис принимает параметры генерации:
- `topic` — тема;
- `number` — количество вопросов;
- `question_types` — типы вопросов;
- `language` — язык ответа;
- `difficulty` — сложность;
- `audience` — целевая аудитория;
- `extra_instructions` — дополнительные инструкции;
- `files` — один или несколько PDF-файлов.

На выходе сервис пытается получить от модели JSON со списком вопросов, правильными ответами, объяснениями и, по возможности, ссылками на источник внутри PDF.

---

## 2. Требования

- Python 3.11
- доступ к OpenAI API или OpenAI-compatible API;
- валидный `OPENAI_API_KEY`.

Зависимости из репозитория:
- `fastapi[standard]>=0.115.0`
- `openai[aiohttp]>=1.109.0`
- `pydantic-settings>=2.6.0`
- `aiofiles>=24.1.0`

---

## 3. Установка

Из корня проекта:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Создай `.env` на основе примера:

```bash
cp .env.example .env
```

---

## 4. Настройка `.env`

Ниже пример рабочего `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.4-mini

MAX_UPLOAD_SIZE_MB=30
MAX_PARALLEL_LLM_CALLS=3
WORKER_COUNT=3
REQUEST_TIMEOUT_SECONDS=180

ENABLE_REASONING=false
REASONING_EFFORT=medium
FORCE_JSON_RESPONSE=true
ALLOW_NON_PDF_FILES=false

STORAGE_DIR=storage
```

### Описание переменных

#### Обязательные
- `OPENAI_API_KEY` — ключ API.

#### Основные
- `OPENAI_BASE_URL` — базовый URL API. Для OpenAI обычно `https://api.openai.com/v1`.
- `OPENAI_MODEL` — имя модели.
- `STORAGE_DIR` — папка для хранения файлов задач и результатов.

#### Ограничения и производительность
- `MAX_UPLOAD_SIZE_MB` — лимит размера одного загружаемого файла.
- `MAX_PARALLEL_LLM_CALLS` — максимальное число одновременных запросов к LLM.
- `WORKER_COUNT` — количество фоновых воркеров очереди.
- `REQUEST_TIMEOUT_SECONDS` — timeout внешнего запроса к LLM.

#### Поведение генерации
- `ENABLE_REASONING` — включать reasoning-параметры, если их поддерживает backend.
- `REASONING_EFFORT` — уровень reasoning (`low`, `medium`, `high` и т.д., если backend это поддерживает).
- `FORCE_JSON_RESPONSE` — просить модель вернуть JSON.
- `ALLOW_NON_PDF_FILES` — разрешать ли загружать не-PDF файлы. По умолчанию `false`.

### Обратная совместимость

Исправленная версия сервиса также понимает старые имена переменных:
- `LLM_MODEL` вместо `OPENAI_MODEL`
- `MAX_PARALLEL_REQUESTS` вместо `MAX_PARALLEL_LLM_CALLS`

---

## 5. Запуск сервиса

### Вариант 1. Через uvicorn

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Вариант 2. Через FastAPI CLI

```bash
fastapi dev app/main.py
```

### Вариант 3. Через корневой entrypoint

После исправления корневой `main.py` просто экспортирует приложение из `app.main`, поэтому можно использовать и его:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

После запуска API будет доступно по адресу:

- `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 6. Доступные endpoint'ы

### `GET /health`
Проверка, что сервис жив.

Пример ответа:

```json
{
  "status": "ok",
  "app": "LLM Service"
}
```

---

### `GET /config`
Возвращает снимок текущей конфигурации сервиса.

Полезно для отладки: видно модель, storage, лимиты и размер очереди.

---

### `POST /generate`
Синхронная генерация. Запрос выполняется сразу, и ответ возвращается в этом же HTTP-вызове.

Подходит для:
- быстрых запросов;
- отладки;
- интеграций, где не нужна очередь.

---

### `POST /jobs/generate`
Асинхронная генерация через очередь.

Сервис:
1. создаёт задачу;
2. сохраняет входные файлы;
3. кладёт задачу в очередь;
4. возвращает `job_id`.

Далее результат можно забирать через `GET /jobs/{job_id}`.

Подходит для:
- более долгих задач;
- пакетной обработки;
- сценариев, где клиент готов опрашивать статус.

---

### `GET /jobs/{job_id}`
Возвращает полное состояние задачи:
- статус;
- входные параметры;
- список файлов;
- логи;
- ошибки;
- сырой ответ модели;
- распарсенный JSON, если парсинг удался.

Статусы:
- `queued`
- `running`
- `finished`
- `failed`

---

### `GET /question/{prompt}/{number}`
Legacy-эндпоинт для обратной совместимости.

Использует упрощённый сценарий:
- `prompt` → тема;
- `number` → количество вопросов.

Подходит только для простых вызовов без файлов и без расширенных параметров.

---

## 7. Поддерживаемые типы вопросов

Параметр `question_types` передаётся как строка через запятую:

- `single_choice`
- `multiple_choice`
- `true_false`
- `100k1`

Пример:

```text
single_choice,multiple_choice,true_false
```

Если `question_types` не указан, сервис использует:

```text
single_choice
```

---

## 8. Примеры запросов

### 8.1. Синхронная генерация без файлов

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -F "topic=Линейная алгебра" \
  -F "number=4" \
  -F "question_types=single_choice,multiple_choice" \
  -F "language=ru" \
  -F "difficulty=medium" \
  -F "audience=студенты первого курса"
```

---

### 8.2. Синхронная генерация с PDF

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -F "topic=Математический анализ" \
  -F "number=5" \
  -F "question_types=single_choice,short_answer,true_false" \
  -F "language=ru" \
  -F "difficulty=medium" \
  -F "audience=студенты" \
  -F "extra_instructions=Сделай вопросы без двусмысленностей" \
  -F "files=@./materials/lecture_01.pdf"
```

Если передаётся PDF, сервис отправляет его в LLM как `data:application/pdf;base64,...` через `Responses API`.

---

### 8.3. Постановка задачи в очередь

```bash
curl -X POST http://127.0.0.1:8000/jobs/generate \
  -F "topic=Базы данных" \
  -F "number=6" \
  -F "question_types=single_choice,true_false,short_answer" \
  -F "language=ru" \
  -F "difficulty=easy" \
  -F "audience=junior backend developers" \
  -F "files=@./materials/db_intro.pdf"
```

Пример ответа:

```json
{
  "job_id": "2c0d2a55-3f44-4e2a-b3cf-7df9f79fa5d2",
  "status": "queued",
  "created_at": "2026-03-27T10:15:30.000000"
}
```

---

### 8.4. Проверка статуса задачи

```bash
curl http://127.0.0.1:8000/jobs/2c0d2a55-3f44-4e2a-b3cf-7df9f79fa5d2
```

Пример сокращённого ответа:

```json
{
  "id": "2c0d2a55-3f44-4e2a-b3cf-7df9f79fa5d2",
  "status": "finished",
  "created_at": "2026-03-27T10:15:30.000000",
  "started_at": "2026-03-27T10:15:31.000000",
  "finished_at": "2026-03-27T10:15:40.000000",
  "request": {
    "topic": "Базы данных",
    "number": 6,
    "question_types": ["single_choice", "true_false", "short_answer"],
    "language": "ru",
    "difficulty": "easy",
    "audience": "junior backend developers",
    "extra_instructions": null
  },
  "files": [
    "/absolute/path/to/storage/<job_id>/inputs/db_intro.pdf"
  ],
  "errors": [],
  "logs": [
    "[10:15:30] Задание создано и поставлено в очередь",
    "[10:15:31] Задание взял worker #0",
    "[10:15:31] Начата обработка задания",
    "[10:15:40] Ответ успешно получен и распарсен"
  ],
  "result": {
    "raw_response": "{...}",
    "parsed_response": {
      "topic": "Базы данных",
      "language": "ru",
      "question_count": 6,
      "questions": [],
      "warnings": []
    }
  }
}
```

---

## 9. Формат результата

Сервис ожидает JSON примерно такого вида:

```json
{
  "topic": "Линейная алгебра",
  "language": "ru",
  "question_count": 4,
  "questions": [
    {
      "id": "q1",
      "type": "single_choice",
      "difficulty": "medium",
      "question": "Что называется собственным значением матрицы?",
      "options": [
        {"id": "A", "text": "Число, при котором det(A - λI)=0"},
        {"id": "B", "text": "Ранг матрицы"},
        {"id": "C", "text": "След матрицы"}
      ],
      "correct_answers": ["A"],
      "explanation": "Собственное значение определяется из характеристического уравнения det(A - λI)=0.",
      "source_reference": "стр. 12",
      "metadata": {}
    }
  ],
  "warnings": []
}
```

### Поля результата

- `topic` — тема генерации;
- `language` — язык ответа;
- `question_count` — количество вопросов;
- `questions` — список вопросов;
- `warnings` — предупреждения.

### Поля вопроса

- `id` — уникальный ID вопроса;
- `type` — тип вопроса;
- `difficulty` — сложность;
- `question` — текст вопроса;
- `options` — список вариантов ответа или `null`;
- `correct_answers` — список правильных ответов;
- `explanation` — объяснение;
- `source_reference` — ссылка на источник в PDF, если модель смогла надёжно её указать;
- `metadata` — дополнительные данные.

### Специфика типов

#### `single_choice`
- один правильный ответ;
- обычно 3–6 вариантов;
- в `correct_answers` должен быть один ID.

#### `multiple_choice`
- несколько правильных ответов;
- обычно 4–7 вариантов;
- в `correct_answers` несколько ID.

#### `true_false`
- варианты ответов должны быть `True` и `False`;
- обычно используются ID `T` и `F`.

#### `short_answer`
- `options = null`;
- в `correct_answers` лежат допустимые краткие ответы.

#### `matching`
- пары записываются в `metadata.pairs`;
- формат элементов:

```json
{"left_id": "L1", "right_id": "R2"}
```

#### `ordering`
- правильная последовательность лежит в `metadata.correct_order`.

---

## 10. Как сервис работает внутри

### Без файлов
Если PDF не переданы, сервис использует `chat.completions`.

### С PDF
Если переданы PDF, сервис использует `Responses API` и вкладывает файлы как `input_file` с `data URL`.

### Очередь
- задачи складываются в in-memory очередь;
- фоновые воркеры забирают задачи;
- состояние сохраняется в `storage/<job_id>/`.

Внутри каталога задачи обычно появляются:
- `inputs/` — загруженные файлы;
- `job_state.json` — текущее состояние задачи;
- `traceback.txt` — traceback при ошибке.

---

## 11. Ограничения

1. По умолчанию принимаются только PDF.
2. Хранилище задач — in-memory, поэтому после перезапуска процесса активные задачи и индекс по ним теряются.
3. Файлы и результаты на диске остаются в `STORAGE_DIR`, пока ты их не удалишь сам.
4. Для работы с PDF нужен backend, совместимый с OpenAI `Responses API` и поддерживающий file inputs.
5. Даже при `FORCE_JSON_RESPONSE=true` модель иногда может вернуть невалидный JSON. В таком случае:
   - `result.raw_response` сохранится;
   - `result.parsed_response` будет `null`;
   - в `errors` появится сообщение о проблеме парсинга.

---

## 12. Типичные ошибки и как их исправить

### `OPENAI_API_KEY не задан`
Проверь, что в `.env` указан ключ:

```env
OPENAI_API_KEY=...
```

---

### `Поддерживаются только PDF-файлы`
Ты отправил файл не с расширением `.pdf`, а `ALLOW_NON_PDF_FILES=false`.

Решения:
- передавать только PDF;
- либо выставить:

```env
ALLOW_NON_PDF_FILES=true
```

---

### `Файл ... превышает лимит ... MB`
Нужно увеличить лимит:

```env
MAX_UPLOAD_SIZE_MB=50
```

---

### Ошибка при обработке PDF через `Responses API`
Это значит, что выбранный API backend не поддерживает один из режимов:
- `responses.create(...)`
- `input_file`
- PDF как `data:application/pdf;base64,...`

Решение:
- использовать backend, совместимый с OpenAI Responses API;
- либо временно вызывать сервис без файлов.

---

### Задача переходит в `failed`
Смотри:
- `GET /jobs/{job_id}`;
- поле `errors`;
- поле `logs`;
- файл `storage/<job_id>/traceback.txt`.

---

## 13. Минимальный сценарий запуска

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполни OPENAI_API_KEY
uvicorn app.main:app --reload
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
```

Тестовая генерация:

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -F "topic=Основы Python" \
  -F "number=3" \
  -F "question_types=single_choice,true_false" \
  -F "language=ru"
```

---

## 14. Что стоит улучшить дальше

Если захочешь развивать сервис дальше, вот самые полезные следующие шаги:
- вынести хранение задач из памяти в Redis/PostgreSQL;
- добавить автоматическую очистку старых файлов;
- сделать retry/backoff на `429` и `5xx`;
- добавить auth;
- ограничить число задач на пользователя;
- добавить streaming/SSE;
- вынести prompt templates по разным сценариям: тест, экзамен, интервью, олимпиада.

---

## 15. Быстрая памятка

### Запуск

```bash
uvicorn app.main:app --reload
```

### Healthcheck

```bash
curl http://127.0.0.1:8000/health
```

### Синхронная генерация

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -F "topic=История SQL" \
  -F "number=5" \
  -F "question_types=single_choice,short_answer"
```

### Генерация через очередь

```bash
curl -X POST http://127.0.0.1:8000/jobs/generate \
  -F "topic=ООП в Python" \
  -F "number=5" \
  -F "question_types=single_choice,true_false" \
  -F "files=@./lesson.pdf"
```

### Проверка задачи

```bash
curl http://127.0.0.1:8000/jobs/<job_id>
```

---

README готов для размещения в корне проекта как `README.md`.
