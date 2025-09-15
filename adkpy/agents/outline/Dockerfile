# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

RUN pip install uv

# --- Dependency Installation ---
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache-dir -r requirements.txt

# --- Application Code ---
# Copy the outline agent's code
COPY . /app/agents/outline

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the outline agent's port
EXPOSE 10002

# --- Run the application ---
CMD ["python", "-m", "outline.a2a_server"]