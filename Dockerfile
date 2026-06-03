FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your actual working script into the container
COPY Devine.py .

# Run your script when the container starts
CMD ["python", "Devine.py"]