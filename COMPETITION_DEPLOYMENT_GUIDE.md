# Project GENESIS: Competition Deployment & Portability Guide
## Master Instructions for Presenting on Any Windows or Linux Computer in Lucknow

---

### 1. Executive Summary

Project **GENESIS** has been fully packaged and containerized to run seamlessly on **any Windows (10/11) or Linux (Ubuntu, Debian, Fedora, Arch)** computer.

Whether the presentation computer has an NVIDIA GPU or is a standard CPU-only laptop, GENESIS automatically detects the hardware and adjusts its neural inference pipelines (PyTorch CUDA or multithreaded CPU fallback) so that **nothing crashes during your live demonstration**.

Moreover, the React frontend has been pre-compiled and mounted directly into the FastAPI server (`frontend/dist`), meaning **the presentation machine does NOT even require Node.js or npm**. Starting the Python backend automatically serves the entire web interface at:
👉 **`http://localhost:8000/`**

---

### 2. Pre-Competition Preparation (Before Leaving for Lucknow)

Copy the entire `Project GENESIS` directory onto a high-speed **USB Flash Drive (16GB or 32GB)** or push it to a private **GitHub / GitLab** repository.

Ensure the following core folders and files are present on your USB drive:
```text
Project GENESIS/
├── backend/
│   ├── app/                      # FastAPI routers, AI engines, ML models
│   ├── bin/
│   │   ├── vina.exe              # AutoDock Vina for Windows (pre-bundled)
│   │   └── vina                  # AutoDock Vina for Linux (pre-bundled)
│   └── data/
│       ├── receptors/            # Pre-cached 3D receptors (6LU7, 1ERE, 1IEP, etc.)
│       └── ingestion/            # Pre-cached TDC benchmark datasets
├── frontend/
│   └── dist/                     # Pre-compiled production React SPA (Zero Node.js needed!)
├── Dockerfile                    # Multi-platform container configuration
├── docker-compose.yml            # 1-command container orchestration
├── environment_genesis.yml       # Conda cross-platform environment spec
├── requirements_full.txt         # Pip universal package requirements
├── install_genesis_windows.bat   # 1-Click Windows installer
├── run_genesis.bat               # 1-Click Windows launcher (auto-opens browser)
├── install_genesis_linux.sh      # 1-Click Linux installer
├── run_genesis.sh                # 1-Click Linux launcher (auto-opens browser)
├── genesis_dev.db                # Pre-populated SQLite projects & candidates database
└── vector_store.json             # Pre-built FAISS knowledge embeddings
```

---

### 3. Deployment Mode 1: Docker (Recommended — 100% Guaranteed)

If the computer provided at the competition has **Docker** installed (Docker Desktop on Windows or Docker Engine on Linux), this is the fastest, zero-friction method.

#### Steps:
1. Open Terminal or PowerShell in the `Project GENESIS` directory.
2. Run:
   ```bash
   docker compose up --build
   ```
3. Open your browser and go to:
   ```text
   http://localhost:8000/
   ```
*Everything (Python 3.11, RDKit, PyTorch, AutoDock Vina, and the web interface) runs inside an isolated, identical environment.*

---

### 4. Deployment Mode 2: Native Windows (1-Click Launch)

If the competition computer is running Windows 10 or 11:

#### First-Time Setup (2–3 minutes):
1. Plug in your USB drive and copy `Project GENESIS` to the Desktop or `C:\`.
2. Double-click:
   👉 **`install_genesis_windows.bat`**
   - Automatically detects Conda or standard Python.
   - Installs all scientific dependencies (`rdkit`, `torch`, `fastapi`, `chemprop`, etc.).
   - Confirms `backend\bin\vina.exe` and `frontend\dist`.

#### Launching the Program:
1. Simply double-click:
   👉 **`run_genesis.bat`**
   - Starts the FastAPI server.
   - Automatically opens your default web browser to **`http://127.0.0.1:8000/`**.

---

### 5. Deployment Mode 3: Native Linux (Ubuntu / Debian / Fedora / Arch)

If the competition computer is running Linux:

#### First-Time Setup (2 minutes):
1. Copy the folder to the home directory (`~/ProjectGENESIS`).
2. Open a terminal and run:
   ```bash
   chmod +x install_genesis_linux.sh run_genesis.sh
   ./install_genesis_linux.sh
   ```
   - Installs system graphics libraries (`libgl1`, `libglib2.0-0`).
   - Sets up the Python environment.
   - Sets execution permissions on the pre-bundled `backend/bin/vina`.

#### Launching the Program:
1. Run:
   ```bash
   ./run_genesis.sh
   ```
   - Starts the server and automatically opens your browser.

---

### 6. Air-Gapped / 100% Offline Guarantee

At academic competitions, venue Wi-Fi is frequently slow, congested, or blocked by institutional firewalls. Project GENESIS is specifically engineered to run **completely offline**:

1. **Pre-cached Receptors:** Target structures for SARS-CoV-2 Mpro (`6LU7`), Estrogen Receptor Alpha (`1ERE`), Abl Kinase (`1IEP`), EGFR (`1M17`), and COX-2 (`1CX2`) are stored locally in `backend/data/receptors/`.
2. **Pre-trained AI Models:** Chemprop D-MPNN evidential weights and QSAR regressors are saved locally in `backend/data/models_weights/`.
3. **Pre-computed Knowledge Base:** The scientific vector store is loaded locally from `vector_store.json`.
4. **Pre-packaged Molecular Docking:** Both Windows (`vina.exe`) and Linux (`vina`) executables are already inside `backend/bin/`.

**You do NOT need active internet connection to demonstrate molecular docking, lead optimisation, virtual screening, or generative reinforcement learning to the judges.**

---

### 7. Recommended 3-Minute Live Competition Pitch Flow

When presenting to the judges in Lucknow, follow this high-impact demo sequence:

| Step | Time | What to Show in the UI (`http://localhost:8000/`) | What to Say to the Judges |
|:---:|:---:|---|---|
| **1. Hook & Overview** | 0:00 - 0:45 | **Landing Page / Molecular Lab**<br>Show the 3D WebGL viewer loaded with SARS-CoV-2 Main Protease (`6LU7`). | *"GENESIS is an end-to-end autonomous AI drug discovery platform. Rather than fragmented tools, it unifies target validation, deep neural bioactivity prediction, 3D physics docking, and closed-loop reinforcement learning into one interface."* |
| **2. Multi-Physics 3D Docking** | 0:45 - 1:30 | Select Target `6LU7`, lead `Nirmatrelvir (Paxlovid)`. Click **"Run AutoDock Vina & PyMOL"**.<br>Observe binding pose rotation and $\Delta G = -7.8\text{ kcal/mol}$. | *"Here, AutoDock Vina explores the 3D conformational pocket across CPU threads, while our GNINA 3D-CNN rescores the pose on spatial voxel density grids to quantify sub-2-Angstrom binding confidence."* |
| **3. Deep Predictive AI & ADMET** | 1:30 - 2:15 | Switch to the **"Lead Optimisation"** tab.<br>Inspect the Multi-Property Objective (MPO) radar chart, QSAR $pIC_{50}$, 4-pillar ADME traffic lights, and Ames/hERG cardiac safety alerts. | *"Drug discovery fails because of ADMET and toxicity liabilities. Our Chemprop Directed Message Passing Neural Network computes deep evidential regression, outputting both predicted potency and epistemic uncertainty ($u_{epistemic}$)."* |
| **4. Autonomous Discovery Loop** | 2:15 - 3:00 | Switch to the **"Iterative Discovery"** tab.<br>Show the automated 9-stage discovery cycle and parent-child molecular lineage DAG tree. | *"Finally, our closed-loop self-optimising worker runs a 9-stage active learning loop: generating de novo molecules with REINVENT 4, screening, docking, predicting, and iteratively climbing the Pareto frontier."* |

---

### 8. Emergency Troubleshooting Cheat-Sheet

- **Port 8000 already in use:**
  - *Windows:* `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`
  - *Linux:* `fuser -k 8000/tcp`
- **Target machine has no GPU:**
  - No action needed! GENESIS automatically detects CUDA availability:
    `DEVICE = "cuda" if torch.cuda.is_available() else "cpu"`
    All models run stably on multi-threaded CPU.
- **Judge asks for Swagger / OpenAPI documentation:**
  - Open a new tab to: **`http://localhost:8000/docs`** to show the complete enterprise REST API schema.
