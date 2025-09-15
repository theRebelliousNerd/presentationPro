# Use an official Python runtime as a parent image with uv
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Set the working directory in the container
WORKDIR /app

# --- Dependency Installation ---
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# --- Application Code ---
# Copy the critic agent's code
COPY . /app/agents/critic

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the critic agent's port
EXPOSE 10004

# --- Run the application ---
CMD ["python", "-m", "critic.a2a_server"]