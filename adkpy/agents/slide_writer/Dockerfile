# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

RUN pip install uv

# --- Dependency Installation ---
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache-dir -r requirements.txt

# --- Application Code ---
# Copy the slide_writer agent's code
COPY . /app/agents/slide_writer

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the slide_writer agent's port
EXPOSE 10003

# --- Run the application ---
CMD ["python", "-m", "slide_writer.a2a_server"]