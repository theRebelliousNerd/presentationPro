# Telemetry Schema (No Code)

UsageEvent
- model: string (e.g., googleai/gemini-2.5-flash)
- kind: prompt|completion|image_call|tool
- promptTokens?: number
- completionTokens?: number
- durationMs?: number
- cost?: number (computed downstream)
- at: timestamp
- step?: string (agent/tool name)
- traceId?: string

Aggregation
- Per presentationId, per user/session, per trace.

