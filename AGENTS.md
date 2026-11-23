# AGENTS.md

## Specialist Agents (Phase 0 definition)

| Agent | Role | Responsibilities |
|-------|------|-------------------|
| CTO / System Architect | overall system design, technology stack, integration strategy | Define architecture, supervise phase planning, ensure scalability and security |
| AI/ML Research Scientist | model selection, fine‑tuning, evaluation | Lead specialist model development (QSAR, ADME, generation) |
| Computational Chemist | cheminformatics pipelines, RDKit integration | Implement SMILES validation, descriptor calculation |
| Medicinal Chemist | molecular design rules, lead optimisation | Define property constraints, scaffold hopping strategies |
| Molecular Biology Specialist | sequence handling, protein data processing | Build biopython utilities, protein‑structure parsers |
| Bioinformatics Specialist | knowledge‑graph construction, data integration | Design KG schema, ingestion pipelines |
| Pharmacologist | target validation, activity interpretation | Map target‑disease relationships, evaluate predictions |
| Toxicology & ADME Specialist | safety profiling, PK/PD modeling | Validate ADME pipelines, toxicity models |
| Physics & Instrumentation Specialist | instrument data interpretation, physical modeling | Encode spectroscopy, chromatography principles |
| Literature Research Specialist | literature search, summarisation | Build RAG pipelines, citation management |
| Autonomous Research Specialist (GARDE) | hypothesis generation, research gap analysis | Orchestrate autonomous discovery loops |
| Backend Engineer | API design, database schema, job scheduler | Implement FastAPI services, background workers |
| Frontend Engineer | UI/UX, 3D visualisation | Build React SPA, integrate 3Dmol.js |
| Database & Infra Engineer | storage, graph DB, vector store | Deploy SQLite/Postgres, Neo4j, Faiss |
| QA Engineer | testing, validation, reproducibility | Write unit/integration tests, CI pipelines |

*These agents will be realised as sub‑agents or role‑specific contributors in later phases.*