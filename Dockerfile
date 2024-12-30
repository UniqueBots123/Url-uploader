FROM python:3.9-slim
WORKDIR /app
COPY bot.py config.py ./
RUN pip install telethon
CMD ["python", "bot.py"]
