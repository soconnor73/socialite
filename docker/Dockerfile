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
# (nginx.conf includes /app/docker/security-headers.conf directly, no separate copy needed)
RUN rm -f /etc/nginx/sites-enabled/default \
    && cp /app/docker/nginx.conf /etc/nginx/conf.d/default.conf

# Fix potential Windows CRLF line endings for Linux execution. Must run
# BEFORE `crontab` installs the job below: a raw CR byte fed to `crontab` is
# stored as a literal two-character "\r" (verified via `crontab -l`), which
# makes the job's trailing `2>&1` redirection invalid ("Bad fd number") and
# silently prevents the entire compound command from ever running.
RUN sed -i 's/\r$//' /app/docker/entrypoint.sh /app/docker/cronjob

# Make entrypoint script executable
RUN chmod +x /app/docker/entrypoint.sh

# Install the weekly scrape job as root's crontab. (Not placed under
# /etc/cron.d/ too — that location requires a 6-field format with an explicit
# user column, which this 5-field per-user crontab syntax doesn't have; cron
# would just log an "unknown user" warning for it on every reload.)
RUN crontab /app/docker/cronjob

# Expose port 80 for the Nginx web server
EXPOSE 80

# Run entrypoint script
ENTRYPOINT ["/app/docker/entrypoint.sh"]
