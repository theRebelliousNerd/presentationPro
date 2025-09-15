# Archived Original Agent Files

This directory contains the original monolithic agent implementations before the A2A migration.

## Files Preserved

- `base.py` - Original base agent class
- `clarifier_agent.py` - Original clarifier agent
- `clarifier_agent_v2.py` - V2 clarifier with ADK enhancements
- `outline_agent.py` - Original outline generator
- `slide_writer_agent.py` - Original slide content writer
- `critic_agent.py` - Original slide critic
- `notes_polisher_agent.py` - Original speaker notes polisher
- `design_agent.py` - Original design generator
- `script_writer_agent.py` - Original script assembler
- `research_agent.py` - Original research agent
- `orchestrator.py` - Original monolithic orchestrator

## Migration Date

Archived on: 2025-01-14

## Purpose

These files are preserved for:
1. Reference during migration debugging
2. Rollback if needed
3. Historical documentation
4. Comparison with new A2A implementation

## New Structure

The new A2A architecture organizes each agent in its own directory:
```
agents/
├── clarifier/
├── outline/
├── slide_writer/
├── critic/
├── notes_polisher/
├── design/
├── script_writer/
├── research/
└── base/
```

Each agent directory contains:
- `agent.py` - ADK agent definition
- `a2a_server.py` - A2A protocol server
- `agent_executor.py` - Task executor
- `Dockerfile` - Container configuration
- `requirements.txt` - Dependencies