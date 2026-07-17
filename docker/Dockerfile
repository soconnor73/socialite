# Use a lightweight python slim base image
FROM python:3.11-slim

# Install system dependencies (nginx, cron)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Remove default Nginx site configuration and copy our custom nginx configuration
RUN rm -f /etc/nginx/sites-enabled/default \
    && cp /app/docker/nginx.conf /etc/nginx/conf.d/default.conf

# Setup the cron job
RUN cp /app/docker/cronjob /etc/cron.d/socialite-cron \
    && chmod 0644 /etc/cron.d/socialite-cron \
    && crontab /etc/cron.d/socialite-cron

# Fix potential Windows CRLF line endings for Linux execution
RUN sed -i 's/\r$//' /app/docker/entrypoint.sh /etc/cron.d/socialite-cron

# Make entrypoint script executable
RUN chmod +x /app/docker/entrypoint.sh

# Expose port 80 for the Nginx web server
EXPOSE 80

# Run entrypoint script
ENTRYPOINT ["/app/docker/entrypoint.sh"]
