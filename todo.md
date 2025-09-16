1. Fix Makefile targets referencing removed `orchestrator`/`mcp-server` services.  
2. Update container health checks so required binaries (`curl`/`wget`) exist or use Python probes.  
3. Honor agent model overrides selected in the Settings UI.  
4. Make autosave delete pruned chat/outline/slide rows before inserting new data.  
5. Restore clarified goals on reload by parsing/saving sentinel messages properly.  
6. Derive presentation titles from outline strings rather than nonexistent `title` fields.  
7. Switch active presentation to the duplicated copy immediately after cloning.  
8. Provide default server-action base URLs that work outside Docker.  
9. Persist full slide design data (design spec/code/image flags, etc.).  
10. Keep initial-input preferences stored and hydrated after reloads.  
11. Persist generated full-script content end-to-end.  
12. Pass selected critic model into slide generation.  
13. Use supplied assets inside the ScriptWriter agent.  
14. Feed assets/constraints/existing content into SlideWriter.  
15. Save selected design variants during autosave.  
16. ~~Fix VisionCV auto-review routing so it hits the Vision service without extra config.~~
17. ~~Expand backend logging so the project log viewer is meaningful.~~
18. ~~Make the Script tab editable/persisted or otherwise sync with storage.~~
19. ~~Implement a real orchestrate agent that coordinates microservices.~~
20. ~~Tie Research helper outputs into the main workflow and persistence.~~
21. ~~Forward requested outline length/tone/audience to the Outline agent.~~
22. Augment Arango RAG with semantic/vector retrieval.  
23. Surface Vision-derived placement recommendations in the UI.  
24. Put the project node/link graph to use in clients or agents.  
25. Persist and reuse Research agent output instead of returning ephemeral data.  
26. Parallelize or stream slide generation so the UI stays responsive.  
27. Persist global token adjustments (“apply to all”).  
28. Provide a way to enable Vision-based auto QA in normal runs.  
29. Wire template-selection endpoints into the frontend.  
30. Persist layout metadata when “Bake to Image” runs.  
31. Save Vision contrast overlay settings with slides.  
32. Improve asset ingest chunking so large documents retain context.  
33. Auto-trigger clarifier follow-ups when `finished:false`.  
34. Surface research notes directly inside the slide editor workflow.  
35. Let users apply slide critic suggestions automatically.  
36. Add cross-slide consistency checking during generation.  
37. Allow Arango design rules to evolve via telemetry/preferences.  
38. Support additional transports (STDIO/SSE) for the Vision MCP server.  
39. Sync clarified asset categories through to Arango records.  
40. Record slide-to-asset usage after design workflows.  
41. Centralize telemetry aggregation for per-agent metrics.  
42. Make telemetry instrumentation consistent across agents.  
43. Build a user-facing telemetry dashboard.  
44. Fix review drawer fetches when running `npm run dev`.  
45. Sanitize SVG uploads before serving.  
46. Await autosave operations during reset to avoid races.  
47. Keep VisionCV tool lists in sync between MCP server and dev UI.  
48. Ensure asset registration hits the proper host outside Docker.  
49. Resolve image-generation service DNS failure (`api-gateway:8088` lookup).  
50. Investigate and complete full script generation workflow.  
51. Prevent crashes on multi-file uploads.  
52. Add ARIA description for the Settings dialog to clear accessibility warning.
