1. В терминал скопировать следующие команды:
pip install python-multipart
pip install -U langchain-community
pip install langchain pandas tiktoken huggingface_hub

2. Запустить файл Progon.py

3. Чтобы добавить к следующей генерации квиза файл (только форматы pdf, txt, md), надо прописать в консоли команду:
curl.exe -X 'POST' 'http://127.0.0.1:8000/uploadfile/' -F 'file=@{full_path}'
Вставив на место {full_path} полный путь до файла