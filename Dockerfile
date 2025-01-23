FROM python:3.11
ENV TZ="Europe/Kiev"

# Set the working directory
WORKDIR /app

# Copy necessary files
COPY main.py logger.py requirements.txt crontab .env ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create the persistent directories
RUN mkdir -p /app/dumps && chmod 777 /app/dumps
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Install cron and set up the cron jobs
RUN apt-get update && apt-get install -y chromium && apt-get install -y cron postgresql-client && crontab crontab && chmod +x main.py

# Start cron
CMD ["cron", "-f"]