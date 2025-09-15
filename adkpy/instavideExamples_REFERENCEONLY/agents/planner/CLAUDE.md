# 🚨 PLANNER AGENT EXAMPLE - DO NOT USE 🚨

## ⛔ THIS IS INSTAVIBE EXAMPLE CODE ⛔

### REFERENCE MATERIAL ONLY

This directory contains an **EXAMPLE** planner agent from InstaVibe showing:
- Planning logic patterns
- A2A server implementation
- Agent executor patterns
- Evaluation set examples

### ⚠️ WARNING: EVALUATION DATA ⚠️

The `.adk/eval_history/` directory contains **InstaVibe-specific evaluation results** that:
- Are NOT relevant to PresentationPro
- Should NOT be used for testing
- Are specific to social event planning, not presentations

### Files Here:

- `agent.py` - InstaVibe planner logic (NOT for PresentationPro)
- `a2a_server.py` - Example A2A server (study pattern only)
- `agent_executor.py` - Example executor (reference only)
- `planner_eval.evalset.json` - InstaVibe test data (DO NOT USE)
- `Dockerfile` - InstaVibe container config (DO NOT COPY)

### ❌ NEVER:

- Execute any Python files in this directory
- Use the evaluation sets for PresentationPro
- Copy the Dockerfile configuration
- Import these modules into PresentationPro

### ✅ INSTEAD USE:

```
/adkpy/agents/outline.py  ← Real presentation outline agent
/adkpy/agents/           ← All real PresentationPro agents
```

---

**REMEMBER: This is InstaVibe's social planner, NOT PresentationPro's outline generator!**