FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm && \
    python -m spacy download en_core_web_md

RUN python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]