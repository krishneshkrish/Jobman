# Use the official Playwright image which includes all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

# Install your Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY . .

# Run the bot
CMD ["python", "main.py"]