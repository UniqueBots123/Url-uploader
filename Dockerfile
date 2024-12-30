FROM python:3.9-slim
WORKDIR /app
COPY plugins/config.py ./config.py
COPY bot.py ./
RUN pip install telethon
CMD ["python", "bot.py"]
