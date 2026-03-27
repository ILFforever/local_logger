# LocalLogger

A lightweight, offline alternative to [Weights & Biases (wandb)](https://wandb.ai) for logging PyTorch training runs. No account, no internet, no setup — just drop in and go.

Logs are saved as plain JSON files. Comes with a live Streamlit dashboard and a query script for checking stats from the terminal.

---

## Install

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. In your training script

```python
from local_logger import LocalLogger

logger = LocalLogger(project="my-project")
logger.watch(model, log="all")  # log parameter stats

for epoch in range(epochs):
    # ... training loop ...
    logger.log({
        "train_loss": avg_train_loss,
        "val_loss": avg_val_loss,
        "lr": current_lr,
    })

logger.finish()
```

Or as a context manager (auto-calls `finish()`):

```python
with LocalLogger(project="my-project") as logger:
    logger.watch(model)
    for epoch in range(epochs):
        logger.log({"train_loss": ..., "val_loss": ...})
```

### 2. Live dashboard

```bash
# Windows
start_dashboard.bat

# Mac/Linux
streamlit run logger_dashboard.py
```

Opens at `http://localhost:8501`. Auto-refreshes every 5 seconds during training.

### 3. Query stats from terminal

```bash
python query_logs.py              # summary of all runs
python query_logs.py --latest     # most recent run
python query_logs.py --run cnn    # any run matching "cnn"
python query_logs.py --all        # print every epoch
```

---

## Migrating from wandb

| wandb | LocalLogger |
|---|---|
| `wandb.init(project="x")` | `LocalLogger(project="x")` |
| `wandb.watch(model)` | `logger.watch(model)` |
| `wandb.log({...})` | `logger.log({...})` |
| `wandb.finish()` | `logger.finish()` |
| `mode="disabled"` | `mode="disabled"` |

**Not supported:** `wandb.config`, `wandb.Image`, `wandb.Table`, `wandb.sweep`

---

## Log structure

```
logs/
└── my-project_20260328_020358/
    ├── config.json        # project name, start time
    ├── metrics.jsonl      # one JSON line per epoch
    ├── summary.json       # min/max/mean/final for each metric
    └── model_params/
        ├── params_initial.json   # weights at start
        └── params_final.json     # weights at end
```

Logs are plain files — share a run by just zipping the folder.

---

## Options

```python
LocalLogger(
    project="my-project",   # run name prefix
    mode="online",          # "online" | "offline" | "disabled"
    log_dir="logs",         # where to save logs
)
```

`mode="disabled"` skips all disk writes — useful for quick test runs.
