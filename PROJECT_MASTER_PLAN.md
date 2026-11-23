# Project Master Plan

## Vision
The GENESIS platform will become a unified AI‑assisted research environment for early‑stage drug discovery, combining literature intelligence, cheminformatics, docking, AI prediction, and autonomous hypothesis generation.

## Phase Overview
| Phase | Goal | Key Deliverables |
|------|------|------------------|
| 0 | Audit & Architecture | Architecture diagram, roadmap, knowledge‑graph design (completed) |
| 1 | Platform Foundation | FastAPI backend skeleton, React/Vite frontend shell, auth placeholders, CI/CD, basic DB schema |
| 2 | Scientific Knowledge Foundation | Knowledge‑graph service, vector store, ingestion scheduler |
| 3 | Cheminformatics Core | RDKit integration, SMILES validation, descriptor extraction |
| 4 | Protein & Docking | AutoDock Vina integration, 3Dmol visualiser |
| 5 | Virtual Screening | Library import, filtering, ranking |
| 6 | AI Prediction Models | QSAR, ADME, toxicity models, model registry |
| 7 | Molecular Generation | Diffusion / VAE generator, candidate tracking |
| 8 | Self‑Optimisation Loop | Failure analysis, iterative optimisation |
| 9 | GARDE Research Engine | Gap detection, hypothesis generation, test design |
|10| New Method Prototyping | Computational method sandbox, benchmarking |
|11| Full Integration | End‑to‑end workflow demo |
|12| Validation & Release | Testing, security review, performance tuning |

## Dependencies between phases
- Phases 2‑4 rely on the DB and API from Phase 1.
- Phase 6 requires scientific core from Phases 3‑5.
- Phase 9 builds on the knowledge‑graph and literature pipeline from Phase 2.

---

*This plan will be refined as the project progresses.*