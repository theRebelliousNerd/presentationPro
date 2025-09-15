# Use an official Python runtime as a parent image with uv
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Set the working directory in the container
WORKDIR /app

# --- Dependency Installation ---
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# --- Application Code ---
# Copy the notes_polisher agent's code
COPY . /app/agents/notes_polisher

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the notes_polisher agent's port
EXPOSE 10005

# --- Run the application ---
CMD ["python", "-m", "notes_polisher.a2a_server"]