# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

RUN pip install uv

# --- Dependency Installation ---
# Copy only the requirements file first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache-dir -r requirements.txt


# --- Application Code ---
COPY . /app/agents/clarifier

# --- Environment ---
ENV PYTHONPATH=/app/agents

# Make port 10001 available to the world outside this container
EXPOSE 10001

# --- Run the application ---
# Run a2a_server.py when the container launches
# Use the module execution '-m' which works well with the PYTHONPATH setup
CMD ["python", "-m", "clarifier.a2a_server"]