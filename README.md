# LLM Question Service (async rewrite)

Переписанный вариант сервиса из `Rafl214/LLM_service`:
- без Ollama;
- с `AsyncOpenAI` и поддержкой OpenAI-compatible API;
- с очередью заданий и ограничением параллельных запросов к LLM;
- с приёмом PDF-файлов;
- с базой для разных типов вопросов.

## Что изменилось

### Было
- загрузка файла в `docs/`;
- синхронный вызов Ollama;
- один примитивный сценарий генерации вопросов;
- удаление папки `docs` после ответа.

### Стало
- `POST /jobs/generate` — поставить генерацию в очередь;
- `GET /jobs/{job_id}` — получить статус и результат;
- `POST /generate` — синхронный вызов без очереди;
- `GET /question/{prompt}/{number}` — упрощённая legacy-совместимость;
- PDF передаются в LLM напрямую как `data:application/pdf;base64,...`;
- количество одновременных внешних вызовов регулируется `MAX_PARALLEL_LLM_CALLS`;
- есть шаблоны под разные типы вопросов.

## Поддерживаемые типы вопросов

Передавай `question_types` как строку через запятую:

- `single_choice`
- `multiple_choice`
- `true_false`
- `short_answer`
- `matching`
- `ordering`

Пример:

```text
single_choice,multiple_choice,true_false
```

## Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
```

Заполни `.env`.

## Запуск

```bash
fastapi dev app/main.py
```

или

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Пример запроса в очередь

```bash
curl -X POST http://127.0.0.1:8000/jobs/generate \
  -F "topic=Математический анализ" \
  -F "number=6" \
  -F "question_types=single_choice,short_answer,true_false" \
  -F "difficulty=medium" \
  -F "audience=студенты 1 курса" \
  -F "files=@./materials/lecture.pdf"
```

Ответ:

```json
{
  "job_id": "...",
  "status": "queued",
  "created_at": "..."
}
```

Потом можно опрашивать:

```bash
curl http://127.0.0.1:8000/jobs/<job_id>
```

## Пример синхронного вызова

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -F "topic=Линейная алгебра" \
  -F "number=4" \
  -F "question_types=single_choice,multiple_choice"
```

## Формат результата

Сервис просит модель вернуть JSON следующего вида:

```json
{
  "topic": "...",
  "language": "ru",
  "question_count": 4,
  "questions": [
    {
      "id": "q1",
      "type": "single_choice",
      "difficulty": "medium",
      "question": "...",
      "options": [
        {"id": "A", "text": "..."},
        {"id": "B", "text": "..."}
      ],
      "correct_answers": ["A"],
      "explanation": "...",
      "source_reference": "стр. 3",
      "metadata": {}
    }
  ],
  "warnings": []
}
```

## Что ещё можно быстро добавить

- Redis/PostgreSQL вместо in-memory `jobs`;
- TTL-очистку старых задач и файлов;
- потоковую выдачу через SSE/WebSocket;
- retry/backoff на 429/5xx;
- отдельные prompt-шаблоны под экзамен, тест, олимпиаду, интервью.
