#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main Flask application for the frontend dashboard."""

from flask import Flask, render_template
import logging

# --- Configuration ---
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# --- Routes ---
@app.route("/")
def index():
    """Renders the main dashboard view."""
    return render_template("index.html")


@app.route("/graph")
def graph():
    """Renders the Spanner graph visualization."""
    # TODO: Fetch graph data from Spanner and pass it to the template
    return render_template("graph.html")


@app.route("/plan")
def plan():
    """Renders the development plan."""
    # TODO: Read the DEV_ASSISTANT_PLAN.md file and pass the content to the template
    with open("../DEV_ASSISTANT_PLAN.md", "r") as f:
        plan_content = f.read()
    return render_template("plan.html", plan_content=plan_content)


@app.route("/logs")
def logs():
    """Renders the logs."""
    # TODO: Read the .gemini.md file and pass the content to the template
    with open("../.gemini.md", "r") as f:
        log_content = f.read()
    return render_template("logs.html", log_content=log_content)


# --- Main Execution ---
if __name__ == "__main__":
    app.run(debug=True)