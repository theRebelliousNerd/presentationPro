
"""Workflow definitions for PresentationPro."""

from pathlib import Path

WORKFLOWS_DIR = Path(__file__).parent
PRESENTATION_WORKFLOW_PATH = WORKFLOWS_DIR / "presentation_workflow.yaml"
RESEARCH_WORKFLOW_PATH = WORKFLOWS_DIR / "research_workflow.yaml"
DESIGN_REFRESH_WORKFLOW_PATH = WORKFLOWS_DIR / "design_refresh_workflow.yaml"
EVIDENCE_SWEEP_WORKFLOW_PATH = WORKFLOWS_DIR / "evidence_sweep_workflow.yaml"
RESEARCH_PREP_WORKFLOW_PATH = WORKFLOWS_DIR / "research_prep_workflow.yaml"
REGRESSION_VALIDATION_WORKFLOW_PATH = WORKFLOWS_DIR / "regression_validation_workflow.yaml"

WORKFLOW_PATHS = {
    "presentation_workflow": PRESENTATION_WORKFLOW_PATH,
    "research_workflow": RESEARCH_WORKFLOW_PATH,
    "design_refresh_workflow": DESIGN_REFRESH_WORKFLOW_PATH,
    "evidence_sweep_workflow": EVIDENCE_SWEEP_WORKFLOW_PATH,
    "research_prep_workflow": RESEARCH_PREP_WORKFLOW_PATH,
    "regression_validation_workflow": REGRESSION_VALIDATION_WORKFLOW_PATH,
}

__all__ = [
    "WORKFLOWS_DIR",
    "WORKFLOW_PATHS",
    "PRESENTATION_WORKFLOW_PATH",
    "RESEARCH_WORKFLOW_PATH",
    "DESIGN_REFRESH_WORKFLOW_PATH",
    "EVIDENCE_SWEEP_WORKFLOW_PATH",
    "RESEARCH_PREP_WORKFLOW_PATH",
    "REGRESSION_VALIDATION_WORKFLOW_PATH",
]
