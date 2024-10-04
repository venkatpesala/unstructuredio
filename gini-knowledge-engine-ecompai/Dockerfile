# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Install necessary dependencies
#RUN apt-get update --fix-missing && apt-get install -y --fix-missing build-essential \
#    libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the local code into the container at /app
COPY . /app

# Set environment variable for OpenAI API key
ENV OPENAI_API_KEY='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'

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8001
EXPOSE 8001

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
