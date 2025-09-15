"""
A2A Policies

Central policy models for orchestration.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class BudgetPolicy(BaseModel):
  maxTokensPerAgent: int = 60_000
  maxTokensPerTrace: int = 180_000
  maxMsPerAgent: int = 60_000
  maxMsPerTrace: int = 180_000


class RetryPolicy(BaseModel):
  maxAttempts: int = 2
  backoffMs: int = 750
  retryable: List[str] = ["rate_limit", "transient", "timeout"]


class SafetyPolicy(BaseModel):
  redactPII: bool = True
  allowDomains: List[str] = []
  attachmentLimit: int = 10


class StopPolicy(BaseModel):
  qualityGate: float = 0.8
  marginalGainThreshold: float = 0.05


class OrchestrationPolicy(BaseModel):
  budget: BudgetPolicy = BudgetPolicy()
  retry: RetryPolicy = RetryPolicy()
  safety: SafetyPolicy = SafetyPolicy()
  stop: StopPolicy = StopPolicy()


def default_policy() -> OrchestrationPolicy:
  return OrchestrationPolicy()

