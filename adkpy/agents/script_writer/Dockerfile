# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install --upgrade pip && pip install uv

# --- Dependency Installation ---
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# --- Application Code ---
# Copy the script_writer agent's code
COPY . /app/agents/script_writer

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the script_writer agent's port
EXPOSE 10007

# --- Run the application ---
CMD ["python", "-m", "script_writer.a2a_server"]