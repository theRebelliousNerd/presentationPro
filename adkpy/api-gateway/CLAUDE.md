# CLAUDE.md - ADK/A2A Orchestrator Directory

This directory contains the orchestration service that coordinates multi-agent workflows, manages sessions, and routes tasks between agents.

## Orchestrator Architecture

The orchestrator acts as the central nervous system of the ADK/A2A platform:

```
Request Flow
    ├─> Session Management
    │   ├─> Session Creation/Validation
    │   ├─> Context Preservation
    │   └─> State Management
    │
    ├─> Agent Discovery
    │   ├─> Capability Matching
    │   ├─> Load Assessment
    │   └─> Routing Decision
    │
    ├─> Task Execution
    │   ├─> Sequential Processing
    │   ├─> Parallel Execution
    │   └─> Error Recovery
    │
    └─> Response Aggregation
        ├─> Result Merging
        ├─> Telemetry Collection
        └─> Client Response
```

## Core Orchestration Patterns

### 1. Sequential Orchestration

```python
class SequentialOrchestrator:
    """Execute agents in a defined sequence"""

    async def execute(
        self,
        agents: List[str],
        initial_input: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Run agents sequentially, passing output to next agent"""
        context = initial_input
        results = []

        for agent_name in agents:
            try:
                # Discover agent
                agent = await self.discover_agent(agent_name)

                # Execute with current context
                result = await agent.execute(
                    input=context,
                    session_id=session_id
                )

                # Update context for next agent
                context = self.merge_context(context, result)
                results.append({
                    "agent": agent_name,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                # Handle failure based on policy
                if self.should_fail_fast:
                    raise
                results.append({
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        return {
            "results": results,
            "final_context": context,
            "session_id": session_id
        }
```

### 2. Parallel Orchestration

```python
class ParallelOrchestrator:
    """Execute multiple agents concurrently"""

    async def execute(
        self,
        agents: List[str],
        input_data: Dict[str, Any],
        session_id: str,
        max_concurrency: int = 5
    ) -> Dict[str, Any]:
        """Run agents in parallel with concurrency control"""

        semaphore = asyncio.Semaphore(max_concurrency)

        async def run_agent(agent_name: str):
            async with semaphore:
                agent = await self.discover_agent(agent_name)
                return await agent.execute(
                    input=input_data,
                    session_id=session_id
                )

        # Create tasks for all agents
        tasks = [
            run_agent(agent_name)
            for agent_name in agents
        ]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        return {
            "results": {
                agent: result
                for agent, result in zip(agents, results)
            },
            "session_id": session_id,
            "execution_time_ms": self.calculate_execution_time()
        }
```

### 3. Conditional Orchestration

```python
class ConditionalOrchestrator:
    """Route to different agents based on conditions"""

    async def execute(
        self,
        routing_rules: List[RoutingRule],
        input_data: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute agents based on conditional logic"""

        execution_path = []

        for rule in routing_rules:
            if await self.evaluate_condition(rule.condition, input_data):
                # Execute agent for this condition
                agent = await self.discover_agent(rule.agent)
                result = await agent.execute(
                    input=input_data,
                    session_id=session_id
                )

                execution_path.append({
                    "rule": rule.name,
                    "agent": rule.agent,
                    "result": result
                })

                # Update input for next evaluation
                input_data = self.merge_context(input_data, result)

                # Check if we should continue
                if rule.terminal:
                    break

        return {
            "execution_path": execution_path,
            "final_output": input_data,
            "session_id": session_id
        }
```

### 4. Pipeline Orchestration

```python
class PipelineOrchestrator:
    """Complex multi-stage pipeline execution"""

    async def execute(
        self,
        pipeline: PipelineDefinition,
        input_data: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute multi-stage pipeline with data transformation"""

        stage_results = {}
        current_data = input_data

        for stage in pipeline.stages:
            # Execute stage based on type
            if stage.type == "transform":
                current_data = await self.transform_data(
                    data=current_data,
                    transform=stage.transform
                )

            elif stage.type == "agent":
                agent = await self.discover_agent(stage.agent)
                result = await agent.execute(
                    input=current_data,
                    session_id=session_id
                )
                current_data = result
                stage_results[stage.name] = result

            elif stage.type == "parallel":
                # Execute sub-agents in parallel
                results = await self.execute_parallel_stage(
                    agents=stage.agents,
                    input_data=current_data,
                    session_id=session_id
                )
                current_data = self.merge_parallel_results(results)
                stage_results[stage.name] = results

            elif stage.type == "conditional":
                # Branch based on condition
                branch = self.evaluate_branch(stage.condition, current_data)
                sub_pipeline = stage.branches[branch]
                result = await self.execute(
                    pipeline=sub_pipeline,
                    input_data=current_data,
                    session_id=session_id
                )
                current_data = result
                stage_results[stage.name] = result

        return {
            "pipeline": pipeline.name,
            "stage_results": stage_results,
            "final_output": current_data,
            "session_id": session_id
        }
```

## Agent Discovery Mechanism

### Discovery Strategy

```python
class AgentRegistry:
    """Central registry for agent discovery"""

    def __init__(self):
        self.agents = {}
        self.capabilities = defaultdict(list)
        self.health_checks = {}

    async def register_agent(
        self,
        agent_id: str,
        agent_card: AgentCard,
        endpoint: str
    ):
        """Register an agent with its capabilities"""

        # Store agent information
        self.agents[agent_id] = {
            "card": agent_card,
            "endpoint": endpoint,
            "registered_at": datetime.utcnow(),
            "status": "active"
        }

        # Index by capabilities
        for capability in agent_card.capabilities:
            self.capabilities[capability.type].append(agent_id)

        # Start health monitoring
        asyncio.create_task(self.monitor_health(agent_id))

    async def discover_agent(
        self,
        requirement: AgentRequirement
    ) -> Optional[AgentProxy]:
        """Discover best agent for requirement"""

        # Find agents with matching capabilities
        candidates = self.find_capable_agents(requirement)

        if not candidates:
            return None

        # Select best agent based on load and availability
        best_agent = await self.select_best_agent(
            candidates,
            requirement
        )

        # Return proxy to agent
        return AgentProxy(
            agent_id=best_agent,
            endpoint=self.agents[best_agent]["endpoint"]
        )

    def find_capable_agents(
        self,
        requirement: AgentRequirement
    ) -> List[str]:
        """Find agents matching requirements"""

        capable_agents = []

        for agent_id, info in self.agents.items():
            # Check if agent is healthy
            if info["status"] != "active":
                continue

            # Check capabilities
            agent_card = info["card"]
            if self.matches_requirements(agent_card, requirement):
                capable_agents.append(agent_id)

        return capable_agents

    async def select_best_agent(
        self,
        candidates: List[str],
        requirement: AgentRequirement
    ) -> str:
        """Select best agent from candidates"""

        scores = {}

        for agent_id in candidates:
            # Calculate selection score
            score = 0

            # Factor 1: Current load
            load = await self.get_agent_load(agent_id)
            score += (100 - load) * 0.4

            # Factor 2: Recent success rate
            success_rate = self.get_success_rate(agent_id)
            score += success_rate * 0.3

            # Factor 3: Capability match strength
            match_strength = self.calculate_match_strength(
                agent_id,
                requirement
            )
            score += match_strength * 0.3

            scores[agent_id] = score

        # Return agent with highest score
        return max(scores, key=scores.get)
```

### Service Discovery Integration

```python
class ServiceDiscovery:
    """Integration with service discovery systems"""

    def __init__(self, discovery_type: str = "consul"):
        self.discovery_type = discovery_type
        self.client = self.create_client()

    def create_client(self):
        """Create appropriate discovery client"""
        if self.discovery_type == "consul":
            return ConsulClient()
        elif self.discovery_type == "etcd":
            return EtcdClient()
        elif self.discovery_type == "kubernetes":
            return K8sClient()
        else:
            return StaticDiscovery()

    async def discover_service(
        self,
        service_name: str,
        version: str = None
    ) -> ServiceEndpoint:
        """Discover service endpoint"""

        if self.discovery_type == "kubernetes":
            # Use Kubernetes service discovery
            return await self.discover_k8s_service(service_name, version)

        elif self.discovery_type == "consul":
            # Use Consul service discovery
            return await self.discover_consul_service(service_name, version)

        else:
            # Use static configuration
            return self.get_static_endpoint(service_name)

    async def register_service(
        self,
        service_name: str,
        endpoint: str,
        health_check: str = None
    ):
        """Register service with discovery system"""

        if self.discovery_type == "consul":
            await self.client.agent.service.register(
                name=service_name,
                address=endpoint.split(":")[0],
                port=int(endpoint.split(":")[1]),
                check=health_check
            )
```

## Session Management

### Session Lifecycle

```python
class SessionManager:
    """Manage orchestration sessions"""

    def __init__(self):
        self.sessions = {}
        self.session_store = SessionStore()

    async def create_session(
        self,
        user_id: str,
        initial_context: Dict[str, Any]
    ) -> Session:
        """Create new orchestration session"""

        session = Session(
            id=str(uuid4()),
            user_id=user_id,
            created_at=datetime.utcnow(),
            context=initial_context,
            state="active",
            metadata={}
        )

        # Store in memory
        self.sessions[session.id] = session

        # Persist to storage
        await self.session_store.save(session)

        # Set TTL
        asyncio.create_task(
            self.expire_session(session.id, ttl=3600)
        )

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve session by ID"""

        # Check memory cache
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Load from storage
        session = await self.session_store.load(session_id)
        if session:
            self.sessions[session_id] = session

        return session

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ):
        """Update session context"""

        session = await self.get_session(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        # Update context
        session.context.update(updates)
        session.updated_at = datetime.utcnow()

        # Persist changes
        await self.session_store.save(session)

    async def expire_session(self, session_id: str, ttl: int):
        """Expire session after TTL"""

        await asyncio.sleep(ttl)

        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.state = "expired"

            # Clean up resources
            await self.cleanup_session(session_id)

            # Remove from memory
            del self.sessions[session_id]

    async def cleanup_session(self, session_id: str):
        """Clean up session resources"""

        # Cancel any running tasks
        if session_id in self.running_tasks:
            for task in self.running_tasks[session_id]:
                task.cancel()

        # Clear temporary data
        await self.clear_session_cache(session_id)

        # Archive session data
        await self.archive_session(session_id)
```

### Context Preservation

```python
class ContextManager:
    """Manage context across agent interactions"""

    def __init__(self):
        self.context_transformers = {}

    def merge_contexts(
        self,
        base_context: Dict[str, Any],
        new_context: Dict[str, Any],
        merge_strategy: str = "deep"
    ) -> Dict[str, Any]:
        """Merge contexts with specified strategy"""

        if merge_strategy == "shallow":
            # Simple dictionary update
            return {**base_context, **new_context}

        elif merge_strategy == "deep":
            # Deep merge with nested structures
            return self.deep_merge(base_context, new_context)

        elif merge_strategy == "append":
            # Append new context to lists
            merged = base_context.copy()
            for key, value in new_context.items():
                if key in merged and isinstance(merged[key], list):
                    merged[key].extend(value if isinstance(value, list) else [value])
                else:
                    merged[key] = value
            return merged

        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")

    def deep_merge(self, dict1: dict, dict2: dict) -> dict:
        """Recursively merge two dictionaries"""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + value
            else:
                result[key] = value

        return result

    def extract_context(
        self,
        full_context: Dict[str, Any],
        required_keys: List[str]
    ) -> Dict[str, Any]:
        """Extract specific context keys for agent"""

        extracted = {}
        for key in required_keys:
            if "." in key:
                # Handle nested keys
                value = self.get_nested_value(full_context, key)
            else:
                value = full_context.get(key)

            if value is not None:
                extracted[key] = value

        return extracted
```

## Task Routing Logic

### Intelligent Routing

```python
class TaskRouter:
    """Route tasks to appropriate agents"""

    def __init__(self):
        self.routing_rules = []
        self.load_balancer = LoadBalancer()

    async def route_task(
        self,
        task: Task,
        session_id: str
    ) -> RoutingDecision:
        """Determine best routing for task"""

        # Analyze task requirements
        requirements = self.analyze_task(task)

        # Find matching routes
        possible_routes = self.find_routes(requirements)

        if not possible_routes:
            raise NoRouteFoundError(f"No route for task: {task.type}")

        # Select optimal route
        optimal_route = await self.select_optimal_route(
            possible_routes,
            task,
            session_id
        )

        return RoutingDecision(
            route=optimal_route,
            agents=optimal_route.agents,
            estimated_time_ms=optimal_route.estimated_time,
            confidence=optimal_route.confidence
        )

    def analyze_task(self, task: Task) -> TaskRequirements:
        """Analyze task to determine requirements"""

        requirements = TaskRequirements()

        # Determine required capabilities
        if task.type == "generate_presentation":
            requirements.capabilities = [
                "content_generation",
                "outline_creation",
                "slide_design"
            ]
            requirements.sequential = True

        elif task.type == "research":
            requirements.capabilities = ["web_search", "document_analysis"]
            requirements.parallel = True

        # Estimate resource needs
        requirements.estimated_tokens = self.estimate_tokens(task)
        requirements.estimated_time_ms = self.estimate_time(task)

        return requirements

    async def select_optimal_route(
        self,
        routes: List[Route],
        task: Task,
        session_id: str
    ) -> Route:
        """Select optimal route based on multiple factors"""

        scores = {}

        for route in routes:
            score = 0

            # Factor 1: Agent availability
            availability = await self.check_availability(route.agents)
            score += availability * 30

            # Factor 2: Historical performance
            performance = self.get_route_performance(route, task.type)
            score += performance * 25

            # Factor 3: Cost efficiency
            cost_score = self.calculate_cost_score(route, task)
            score += cost_score * 20

            # Factor 4: Session affinity
            affinity = self.calculate_session_affinity(route, session_id)
            score += affinity * 15

            # Factor 5: Load distribution
            load_score = self.calculate_load_score(route)
            score += load_score * 10

            scores[route] = score

        return max(scores, key=scores.get)
```

## Error Propagation

### Error Handling Strategy

```python
class ErrorHandler:
    """Centralized error handling for orchestration"""

    def __init__(self):
        self.error_policies = {}
        self.retry_manager = RetryManager()

    async def handle_agent_error(
        self,
        error: Exception,
        agent: str,
        context: Dict[str, Any]
    ) -> ErrorResolution:
        """Handle errors from agent execution"""

        # Classify error
        error_type = self.classify_error(error)

        # Get policy for error type
        policy = self.get_error_policy(error_type, agent)

        # Apply policy
        if policy.action == "retry":
            return await self.retry_agent(
                agent=agent,
                context=context,
                max_attempts=policy.max_retries,
                backoff=policy.backoff
            )

        elif policy.action == "fallback":
            return await self.use_fallback_agent(
                original_agent=agent,
                context=context,
                fallback=policy.fallback_agent
            )

        elif policy.action == "compensate":
            return await self.compensate_error(
                agent=agent,
                error=error,
                context=context
            )

        elif policy.action == "fail":
            # Propagate error with context
            raise OrchestrationError(
                message=f"Agent {agent} failed: {error}",
                agent=agent,
                original_error=error,
                context=context
            )

    def classify_error(self, error: Exception) -> str:
        """Classify error type for policy application"""

        if isinstance(error, TimeoutError):
            return "timeout"
        elif isinstance(error, RateLimitError):
            return "rate_limit"
        elif isinstance(error, ValidationError):
            return "validation"
        elif isinstance(error, ServiceUnavailableError):
            return "service_unavailable"
        else:
            return "unknown"

    async def retry_agent(
        self,
        agent: str,
        context: Dict[str, Any],
        max_attempts: int = 3,
        backoff: float = 2.0
    ) -> Any:
        """Retry agent execution with exponential backoff"""

        attempt = 1
        delay = 1.0

        while attempt <= max_attempts:
            try:
                # Attempt execution
                result = await self.execute_agent(agent, context)

                # Log successful retry
                logger.info(f"Agent {agent} succeeded on attempt {attempt}")

                return result

            except Exception as e:
                if attempt == max_attempts:
                    # Final attempt failed
                    raise MaxRetriesExceededError(
                        agent=agent,
                        attempts=max_attempts,
                        last_error=e
                    )

                # Log retry attempt
                logger.warning(
                    f"Agent {agent} failed on attempt {attempt}, "
                    f"retrying in {delay}s: {e}"
                )

                # Wait before retry
                await asyncio.sleep(delay)
                delay *= backoff
                attempt += 1
```

## Retry Strategies

### Retry Policies

```python
class RetryPolicy:
    """Define retry behavior for different scenarios"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""

        # Exponential backoff
        delay = min(
            self.initial_delay * (self.backoff_factor ** (attempt - 1)),
            self.max_delay
        )

        # Add jitter to prevent thundering herd
        if self.jitter:
            delay *= (0.5 + random.random())

        return delay

    def should_retry(
        self,
        error: Exception,
        attempt: int
    ) -> bool:
        """Determine if retry should be attempted"""

        # Check attempt limit
        if attempt >= self.max_attempts:
            return False

        # Check if error is retryable
        if isinstance(error, (ValidationError, AuthenticationError)):
            return False  # Non-retryable errors

        if isinstance(error, RateLimitError):
            # Always retry rate limits with appropriate delay
            return True

        # Default: retry on transient errors
        return True
```

## Circuit Breaker Patterns

### Circuit Breaker Implementation

```python
class CircuitBreaker:
    """Prevent cascading failures with circuit breaker"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_count = 0

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection"""

        # Check circuit state
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                self.half_open_count = 0
            else:
                raise CircuitOpenError(
                    f"Circuit breaker is open, retry after {self.recovery_timeout}s"
                )

        # Half-open state: limited requests
        if self.state == "half-open":
            if self.half_open_count >= self.half_open_requests:
                # Enough successful requests, close circuit
                self.state = "closed"
                self.failure_count = 0

        try:
            # Execute function
            result = await func(*args, **kwargs)

            # Success: update state
            if self.state == "half-open":
                self.half_open_count += 1

            return result

        except Exception as e:
            self._record_failure()
            raise

    def _record_failure(self):
        """Record failure and update circuit state"""

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""

        if not self.last_failure_time:
            return True

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""

        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time,
            "time_until_reset": max(
                0,
                self.recovery_timeout - (time.time() - (self.last_failure_time or 0))
            ) if self.state == "open" else None
        }
```

## Load Balancing

### Load Balancing Strategies

```python
class LoadBalancer:
    """Balance load across available agents"""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.agent_loads = defaultdict(int)
        self.last_selected = {}

    async def select_agent(
        self,
        agents: List[str],
        context: Dict[str, Any] = None
    ) -> str:
        """Select agent based on load balancing strategy"""

        if self.strategy == "round_robin":
            return self.round_robin_select(agents)

        elif self.strategy == "least_connections":
            return await self.least_connections_select(agents)

        elif self.strategy == "weighted":
            return self.weighted_select(agents, context)

        elif self.strategy == "consistent_hash":
            return self.consistent_hash_select(agents, context)

        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def round_robin_select(self, agents: List[str]) -> str:
        """Simple round-robin selection"""

        key = ",".join(sorted(agents))
        last_index = self.last_selected.get(key, -1)
        next_index = (last_index + 1) % len(agents)
        self.last_selected[key] = next_index

        return agents[next_index]

    async def least_connections_select(self, agents: List[str]) -> str:
        """Select agent with least active connections"""

        loads = {}
        for agent in agents:
            loads[agent] = await self.get_agent_load(agent)

        return min(loads, key=loads.get)

    def weighted_select(
        self,
        agents: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Select based on agent weights and capabilities"""

        weights = {}
        for agent in agents:
            # Base weight
            weight = 1.0

            # Adjust for agent capabilities
            if context and "requirements" in context:
                weight *= self.calculate_capability_match(
                    agent,
                    context["requirements"]
                )

            # Adjust for current load
            weight *= (100 - self.agent_loads[agent]) / 100

            weights[agent] = weight

        # Weighted random selection
        total = sum(weights.values())
        rand = random.uniform(0, total)

        cumulative = 0
        for agent, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return agent

        return agents[-1]  # Fallback
```

## Performance Monitoring

### Orchestration Metrics

```python
class OrchestrationMetrics:
    """Track orchestration performance metrics"""

    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(float))
        self.histograms = defaultdict(list)

    def record_orchestration(
        self,
        orchestration_type: str,
        duration_ms: float,
        agent_count: int,
        success: bool
    ):
        """Record orchestration execution metrics"""

        key = f"{orchestration_type}:{agent_count}_agents"

        self.metrics[key]["count"] += 1
        self.metrics[key]["total_duration_ms"] += duration_ms
        self.metrics[key]["success" if success else "failure"] += 1

        # Track histogram for percentiles
        self.histograms[key].append(duration_ms)

        # Calculate running averages
        self.metrics[key]["avg_duration_ms"] = (
            self.metrics[key]["total_duration_ms"] /
            self.metrics[key]["count"]
        )

    def get_percentile(
        self,
        key: str,
        percentile: float
    ) -> float:
        """Calculate percentile for metric"""

        if key not in self.histograms or not self.histograms[key]:
            return 0.0

        sorted_values = sorted(self.histograms[key])
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""

        summary = {}

        for key, metrics in self.metrics.items():
            summary[key] = {
                "count": metrics["count"],
                "avg_duration_ms": metrics["avg_duration_ms"],
                "success_rate": (
                    metrics.get("success", 0) /
                    metrics["count"] * 100
                    if metrics["count"] > 0 else 0
                ),
                "p50_duration_ms": self.get_percentile(key, 50),
                "p95_duration_ms": self.get_percentile(key, 95),
                "p99_duration_ms": self.get_percentile(key, 99)
            }

        return summary
```

## Troubleshooting

### Common Issues

1. **"No agents available"**:
   ```python
   # Check agent registry
   registry = AgentRegistry()
   print(f"Registered agents: {registry.list_agents()}")

   # Verify agent health
   for agent in registry.list_agents():
       health = await registry.check_health(agent)
       print(f"{agent}: {health}")
   ```

2. **"Session expired"**:
   ```python
   # Extend session TTL in config
   SESSION_TTL = 7200  # 2 hours

   # Implement session refresh
   async def refresh_session(session_id):
       session = await session_manager.get_session(session_id)
       session.updated_at = datetime.utcnow()
       await session_manager.save(session)
   ```

3. **"Circuit breaker open"**:
   ```python
   # Check circuit breaker state
   breaker = circuit_breakers.get(service_name)
   state = breaker.get_state()
   print(f"State: {state['state']}")
   print(f"Failures: {state['failure_count']}")
   print(f"Reset in: {state['time_until_reset']}s")

   # Manual reset if needed
   breaker.reset()
   ```

### Debug Mode

Enable orchestrator debugging:
```bash
export ORCHESTRATOR_DEBUG=true
export ORCHESTRATOR_LOG_LEVEL=DEBUG
export TRACE_ORCHESTRATION=true

# This enables:
# - Detailed execution traces
# - Agent communication logs
# - Performance profiling
# - Session state dumps
```

## Migration Procedures

### Upgrading Orchestration Patterns

1. **Test new pattern in staging**:
   ```python
   # Feature flag for new pattern
   if Config.ENABLE_NEW_ORCHESTRATION:
       orchestrator = NewOrchestrator()
   else:
       orchestrator = LegacyOrchestrator()
   ```

2. **Gradual rollout**:
   ```python
   # Percentage-based rollout
   if random.random() < Config.NEW_PATTERN_PERCENTAGE:
       use_new_pattern()
   ```

3. **Monitor metrics**:
   ```python
   # Compare performance
   metrics.record_pattern_comparison(
       old_pattern_metrics,
       new_pattern_metrics
   )
   ```

## Contact & Support

- **Orchestration Issues**: File issue with `[ORCH]` tag
- **Performance Problems**: Include metrics from telemetry
- **Pattern Requests**: Submit design document for review
- **Emergency**: Use break-glass procedures for critical failures