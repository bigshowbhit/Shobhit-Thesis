# FROM python:3.11-slim

# WORKDIR /app

# # Install dependencies
# COPY client/requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy client code
# COPY client/ /app/

# # Create non-root user
# RUN useradd -m app && chown -R app:app /app
# USER app

# # Persistent directories
# VOLUME ["/app/state", "/app/staging"]

# # Main entrypoint
# CMD ["python", "client.py"]

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY client/requirements.txt /app/client/requirements.txt
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r client/requirements.txt -r server/requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY client/ /app/client/
COPY server/ /app/server/

# Create non-root user
RUN useradd -m app && chown -R app:app /app
USER app

# Persistent directories
VOLUME ["/app/state", "/app/staging"]

# Set working directory to client by default
WORKDIR /app/client

# Default command (can be overridden)
CMD ["python", "client.py"]