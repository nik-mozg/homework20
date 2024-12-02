# Используем базовый образ с Python
FROM python:3.12.4

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости
RUN poetry install --no-dev

# Устанавливаем переменные окружения
ENV DJANGO_SETTINGS_MODULE=mysite.settings
ENV DJANGO_DEBUG=1

# Открываем порт
EXPOSE 8000

# Команда для запуска приложения
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
