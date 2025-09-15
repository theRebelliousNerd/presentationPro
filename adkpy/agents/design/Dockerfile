# Use an official Python runtime as a parent image with uv
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Set the working directory in the container
WORKDIR /app

# --- Dependency Installation ---
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# --- Application Code ---
# Copy the design agent's code
COPY . /app/agents/design

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the design agent's port
EXPOSE 10006

# --- Run the application ---
CMD ["python", "-m", "design.a2a_server"]