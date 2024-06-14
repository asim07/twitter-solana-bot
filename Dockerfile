FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code and the migration script
COPY . .

CMD [ "python", "-u", "main.py" ]