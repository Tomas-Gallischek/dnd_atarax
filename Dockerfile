# Použití odlehčené verze Pythonu
FROM python:3.12-slim

# Nastavení proměnných prostředí pro Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Nastavení pracovního adresáře v kontejneru
WORKDIR /app

# Instalace systémových závislostí pro PostgreSQL (psycopg)
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Zkopírování a instalace závislostí
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Zkopírování zbytku kódu aplikace
COPY . /app/

# Příkaz pro spuštění serveru
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]