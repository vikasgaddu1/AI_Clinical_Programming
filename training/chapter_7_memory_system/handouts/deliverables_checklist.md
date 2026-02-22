# Chapter 7: Agent Memory System — Deliverables Checklist

## Exercise Deliverables

| # | Exercise | Deliverable | Done? | Confidence (1-5) |
|---|---------|-------------|-------|-------------------|
| 7.1 | Why Agents Forget | Identified 3+ decision points in DM spec | | |
| 7.1 | Why Agents Forget | Filled in memory gaps table | | |
| 7.1 | Why Agents Forget | Articulated conventions vs memory difference | | |
| 7.2 | Coding Standards | Read all sections of coding_standards.yaml | | |
| 7.2 | Coding Standards | Traced YAML -> MemoryManager -> agent context -> R code | | |
| 7.2 | Coding Standards | Verified header and naming compliance in generated code | | |
| 7.3 | Decisions & Pitfalls | Recorded 3 decisions and 2 pitfalls via API | | |
| 7.3 | Decisions & Pitfalls | Verified persistence in YAML on disk | | |
| 7.3 | Decisions & Pitfalls | Read memory back with fresh MemoryManager | | |
| 7.4 | Cross-Domain Memory | Created DM domain context with decisions + derived vars | | |
| 7.4 | Cross-Domain Memory | Read DM context from simulated AE pipeline | | |
| 7.4 | Cross-Domain Memory | Built AE agent context with cross-domain info | | |
| 7.5 | Pitfall Promotion | Created matching pitfalls in 2 studies | | |
| 7.5 | Pitfall Promotion | Detected promotable patterns via scan | | |
| 7.5 | Pitfall Promotion | Promoted a pitfall with reviewer attribution | | |
| 7.5 | Pitfall Promotion | Verified promoted pitfall visible to new studies | | |

## Concepts Understood

| Concept | Can explain? | Can implement? |
|---------|-------------|----------------|
| Why stateless agents need memory | | |
| Layered memory (company + study) | | |
| coding_standards.yaml structure | | |
| Program header template and modification history | | |
| DecisionRecord data model and API | | |
| PitfallRecord data model and API | | |
| DomainContext for cross-domain awareness | | |
| Auto-flag + manual approve promotion | | |
| `build_agent_context()` for different agent types | | |
| CDISC compliance rules in coding standards | | |

## Self-Assessment

Rate your confidence (1-5):

- [ ] I can explain why agents need persistent memory: ___
- [ ] I can read and modify coding_standards.yaml: ___
- [ ] I can use the MemoryManager API to record and retrieve data: ___
- [ ] I can trace how memory flows from YAML files into agent-generated code: ___
- [ ] I can explain the pitfall promotion workflow: ___

## Notes

> Space for your notes during the session:
>
> ___________________________________________________________________________
>
> ___________________________________________________________________________
>
> ___________________________________________________________________________
