# Project Status

## Current Phase Overview
- **Phase 0: Audit & Architecture** – Completed.
- **Phase 1: Platform Foundation** – Completed (FastAPI, SQLite, Vite/React SPA, Windows task automation).
- **Phase 2: Scientific Knowledge Base** – Completed (FAISS vector store, sentence-transformers, Neo4j bridge, literature ingestion).
- **Phase 3: Cheminformatics Core** – Completed (RDKit exact weight, Hill formula, Crippen LogP, Lipinski profiling, 3D ETKDG/MMFF conformer, 2D SVG depiction, dedicated `genesis-gpu` environment).
- **Phase 4: Protein, Docking & Molecular Visualisation Engine** – Completed (AutoDock Vina 1.2.7 integration, Meeko ligand preparation, RCSB target fetching, active site pocket calculation, multithreaded docking, interactive 3Dmol.js WebGL viewer, and Schrödinger PyMOL 3.1.0 Open-Source Visualisation Engine).
- **Phase 5: Virtual Screening Pipeline** – Completed (Curated chemical libraries, cheminformatics pre-filtering, asynchronous batched Vina docking, real-time progress monitoring, multi-parametric scoring [ΔG, LE, LLE], Project Candidates DB persistence, streaming CSV/JSON export, PyMOL publication snapshots, and React Screening Console).
- **Phase 6: Lead Optimisation & QSAR / AI Prediction Models** – Completed (702-D composite feature extractor, target-specific QSAR regressors, applicability domain index, comprehensive ADME pharmacokinetics, in silico cardiac/Ames/DILI toxicity profiling, bioisosteric MMP engine, MPO desirability scoring, and React Lead Optimisation Studio).
- **Phase 7: Molecular Generation & De Novo Design** – Up next.

---

## Completed Phase 6: Lead Optimisation & AI Prediction Models Deliverables

1. **High-Dimensional Molecular Descriptor Extractor (`descriptor_extractor.py`):**
   - **Composite 702-Dimensional Feature Vectors:** Combines 512-bit Morgan Circular Fingerprints (ECFP4, radius 2), 166-bit MACCS structural keys, and 24 RDKit 2D physicochemical descriptors (MW, LogP, TPSA, HBD, HBA, RotBonds, CSP3, AromaticRings, MolMR, LabuteASA, BalabanJ, BertzCT, Chi, Kappa, etc.).
   - **Tanimoto Similarity Calculator:** Enables rapid nearest-neighbor structural comparison for applicability domain assessment.

2. **Target-Specific QSAR Bioactivity Engine (`qsar_engine.py`):**
   - **Calibrated Multi-Model Ensembles:** Standardized Ridge Regression and Random Forest Regressor ensembles trained on validated ChEMBL/literature bioactivity reference sets.
   - **Supported Target Families:**
     - SARS-CoV-2 Main Protease Mpro (`6LU7`): Nirmatrelvir, Boceprevir, GC376, etc.
     - Abl Tyrosine Kinase (`1IEP`): Imatinib, Dasatinib, Nilotinib, Ponatinib, etc.
     - Estrogen Receptor Alpha ER$\alpha$ (`1ERE`): Estradiol, Tamoxifen, Raloxifene, etc.
     - EGFR Kinase Domain (`1M17`): Erlotinib, Gefitinib, Lapatinib, Osimertinib, etc.
     - Cyclooxygenase-2 COX-2 (`1CX2`): Celecoxib, Rofecoxib, Indomethacin, etc.
   - **Metrics Output:** Predicted $pIC_{50}$ ($-\log_{10}[IC_{50}\text{ in M}]$), Estimated $IC_{50}$ in nM and $\mu\text{M}$, and categorical activity tier (`Potent Active`, `Moderate Active`, `Weak / Micromolar`, `Inactive`).
   - **Applicability Domain (AD) Index:** Computes nearest-neighbor Tanimoto similarity against the training space; alerts if predictions extrapolate outside the training distribution ($T < 0.30$).
   - **Multi-Target Selectivity Evaluation:** Cross-target bioactivity profiling to evaluate on-target vs off-target binding affinity.

3. **Comprehensive ADME Pharmacokinetics Engine (`adme_engine.py`):**
   - **Human Intestinal Absorption (HIA %):** Quantitative absorption estimation and high/moderate/poor classification.
   - **Caco-2 Cell Permeability:** Apparent cellular permeability in $10^{-6}\text{ cm/s}$ (Low $<2$, Moderate $2-8$, High $>8$).
   - **P-glycoprotein (P-gp) Efflux Matrix:** Classifies P-gp substrate probability and P-gp inhibition risk.
   - **Blood-Brain Barrier (BBB) Penetration:** Quantitative $\log BB$ (Clark model) and categorical CNS penetrant (`BBB+`) vs non-penetrant (`BBB-`).
   - **Plasma Protein Binding (PPB %):** Predicts bound fraction and fraction unbound ($f_u$).
   - **Volume of Distribution ($VD_{ss}$ in L/kg):** Predicts physiological tissue distribution volume.
   - **Cytochrome P450 Metabolism Matrix (5 Isoforms):** Multi-class substrate and inhibition profiling across CYP1A2, CYP2C9, CYP2C19, CYP2D6, and CYP3A4, with Drug-Drug Interaction (DDI) risk assessment.
   - **Excretion & Elimination:** Total clearance ($CL_{tot}$ in $\text{mL/min/kg}$) and terminal half-life ($t_{1/2}$) dosing interval projections.
   - **Composite ADME Desirability Score ($0 - 100$).**

4. **Predictive Toxicity & Safety Engine (`toxicity_engine.py`):**
   - **hERG Cardiac Safety:** Potassium channel $I_{Kr}$ inhibition probability, flagging pro-arrhythmic QT prolongation risk.
   - **Ames Mutagenicity:** Bacterial DNA reactivity prediction and mutagenic flag.
   - **Drug-Induced Liver Injury (DILI):** Hepatotoxicity risk probability and severity tier.
   - **Acute Oral Toxicity (Rat $LD_{50}$ in mg/kg):** Quantitative lethal dose estimation mapped to GHS Hazard Categories (Category I to V).
   - **Toxicophoric Substructure Alerts:** Scans against 10 reactive motifs (aromatic nitro, primary aromatic amines, alkyl halides, epoxides, hydrazines, Michael acceptors, quinones, etc.).
   - **Composite Safety Index ($0 - 100$).**

5. **Lead Optimisation & Bioisostere Engine (`lead_optimizer.py`):**
   - **Matched Molecular Pair (MMP) Transformations:** Proposes targeted medicinal chemistry modifications:
     - $-\text{COOH} \to \text{Tetrazole, Acylsulfonamide}$ (permeability & pKa tuning)
     - Phenol $-\text{OH} \to \text{Indole NH}$ (glucuronidation protection)
     - Phenyl $\to \text{Pyridine}$ (lipophilicity reduction, aqueous solubility)
     - Aromatic $-\text{H} \to -\text{F}$ (metabolic blocking)
     - Methyl $\to -\text{CF}_3$ (hydrophobic pocket packing)
     - Amide $\to \text{1,2,4-Oxadiazole}$ (proteolytic resistance)
     - Basic Solubilizing Tails (morpholine addition)
   - **Multi-Property Objective (MPO) Desirability:** 5-dimensional geometric mean desirability function balancing potency ($pIC_{50}$), lipophilicity ($\text{cLogP} \in [1.5, 3.5]$), polar surface area ($\text{TPSA} \in [40, 120]$), safety (low hERG/Ames), and ADME.
   - **Analog Scoring:** Computes $\Delta pIC_{50}$, $\Delta \log P$, $\Delta MPO$, and medicinal chemistry hypothesis for each proposed analog.

6. **FastAPI Endpoints (`backend/app/routers/qsar_adme.py`):**
   - `POST /ai_models/qsar/predict`
   - `POST /ai_models/qsar/multi_target`
   - `POST /ai_models/adme/profile`
   - `POST /ai_models/toxicity/profile`
   - `POST /ai_models/lead_opt/suggest`
   - `POST /ai_models/lead_opt/comprehensive_lead_profile`
   - `POST /ai_models/candidates/{id}/evaluate_all` (updates SQLite `candidates` table)

7. **Frontend Lead Optimisation & AI Prediction Studio (`LeadOptimization.tsx`):**
   - Preset lead molecule selector (Nirmatrelvir, Imatinib, Estradiol, Erlotinib, Celecoxib, Ibuprofen).
   - Target receptor selector.
   - Multi-Property Objective (MPO) radial gauge and 5-bar dimension breakdown.
   - QSAR Bioactivity panel with $pIC_{50}$, $IC_{50}$ (nM), and applicability domain indicator.
   - Multi-target selectivity cross-comparison grid.
   - ADME 4-pillar traffic lights (Absorption, Distribution, 5-CYP Matrix, Elimination).
   - In silico toxicity and structural toxicophore tag cloud.
   - Bioisostere suggestion cards with 1-click "Load into Studio" and "Save to Candidates DB".

8. **Automated Verification:**
   - **Phase 6 AI Models Suite (`test_phase6.bat`):** 10 / 10 tests passed (100%).
   - **Virtual Screening Suite (`test_screening.bat`):** 10 / 10 tests passed (100%).
   - **PyMOL Visualisation Engine Suite (`test_pymol.bat`):** 9 / 9 tests passed (100%).
   - **Chemistry Core Suite (`test_endpoint.bat`):** 12 / 12 tests passed (100%).

---
*Status updated on 2026-11-20.*


---

## AI Scientific Integration Plan (Milestones 1–6 Complete — 100% Fully Verified)

Integrating 10 Scientific Repositories: TDC, ChEMBL Client, DeepChem, Chemprop, REINVENT4, TorchDrug, GNINA, RDKit, Datamol, and Open Targets Platform.

### Subsystem Architecture & Test Verification

| Milestone | Subsystem | Components | Status | Test Suite |
|---|---|---|---|---|
| **Milestone 1** | Scientific Data Foundation & Governance | ChEMBL REST ($pIC_{50}$ normalization), Open Targets GraphQL (tractability, safety), TDC Benchmark Ingestion, Datamol Bemis-Murcko scaffolding, Zero-leakage Data Governance | **100% COMPLETE** | `test_milestone1.bat` (5/5 PASS, 100%) |
| **Milestone 2** | Deep Neural Predictive Engine | Chemprop 2.3.1 D-MPNN on RTX 3060 CUDA, Deep Evidential Regression ($u_{epistemic}$), Multi-Task ADMET (Caco-2, hERG) | **100% COMPLETE** | `test_milestone2.bat` (3/3 PASS, 100% CUDA) |
| **Milestone 3** | GNINA 3D-CNN Docking Engine | 8-Channel 3D Spatial Voxel Grid, CNNscore (RMSD < 2Å), CNNaffinity ($pK_d$), Hybrid Composite Scoring ($0.5 \cdot -\text{Vina} + 0.5 \cdot \text{CNNaffinity}\times\text{CNNscore}$) | **100% COMPLETE** | `test_milestone3.bat` (100% PASS in 3.67s CUDA) |
| **Milestone 4** | Generative Multi-Objective RL Engine | REINVENT 4 RNN Generative Engine on RTX 3060 CUDA, De Novo SMILES, Bioisosteric Scaffold Hopping, 5-Term Composite Reward | **100% COMPLETE** | `test_milestone4.bat` (100% PASS) |
| **Milestone 5** | Closed-Loop Iterative Discovery Worker & Lineage System | Automated 9-Stage Discovery Loop, Parent-Child Molecular Lineage DAG (`CandidateNode.parent_id`), Active Learning Criteria ($u_{epistemic} > 0.65$), Failure Taxonomy Classification, Multi-Objective Pareto Frontier Tracking | **100% COMPLETE** | `test_milestone5.bat` (5/5 PASS, 100%) |
| **Milestone 6** | Unified Portal Verification & End-to-End Campaign | Multi-Target Benchmark (SARS-CoV-2 Mpro 6LU7, ESR1 1ERE), Full Regression Suites, Interactive Frontend Lineage Studio (`IterativeDiscovery.tsx`) | **100% COMPLETE** | `test_milestone6.bat` (4/4 PASS, 100%) |

*Status updated on 2026-11-21.*
