Инструкция по установке всех необходимых комонентов под Windows PowerShell:
1) Установить Python 3.11 или ниже (https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe)

2) Установить Ollama с официального сайта (https://ollama.com/download/windows)

3) В терминале перейди в директорию сервиса(LLM_service)

4) Для установки всего необходимого для python используй команды:
python -m pip install --upgrade pip
pip install -r requirements.txt
ollama pull qwen3:8b

5) Добавить **/LLM_service/__pycache__ в .gitignore



Для запуска сервиcа:
1) Перейти в директорию сервиса

2) Ввести в консоли команду fastapi dev main.py



Запросы к сервису:
После пункта 2) в логе отобразится что-то типо:
	.
	.
	.
      INFO   Will watch for changes in these directories: ['C:\\Users\\Илья\\code\\LLM_service']
----> INFO   Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)  
      INFO   Started reloader process [6920] using WatchFiles
      INFO   Started server process [9740]
      INFO   Waiting for application startup.
      INFO   Application startup complete.

Нас интересует ссылка http://127.0.0.1:8000 
Для того, чтобы сделать запрос к модели, нужно перейти по ссылке:
http://127.0.0.1:8000/question/{prompt}/{number}
Где {prompt} - текст запроса, а {number} - количество вопросов для генерации.

ВАЖНО! Модель жрёт очень много оперативной памяти, так что запускать её параллельно с чем-то ещё не рекомендую