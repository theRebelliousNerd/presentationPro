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
# Copy the research agent's code
COPY . /app/agents/research

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Expose the research agent's port
EXPOSE 10008

# --- Run the application ---
CMD ["python", "-m", "research.a2a_server"]