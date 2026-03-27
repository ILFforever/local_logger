import json
import torch
from datetime import datetime
from pathlib import Path


class LocalLogger:
    def __init__(self, project, mode="online", log_dir="logs"):
        self.project = project
        self.mode = mode  # "online", "offline", or "disabled"
        self.model = None
        self.log_mode = None
        self.metrics = []
        self.step = 0

        if mode == "disabled":
            self.run_dir = None
            return

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.log_dir / f"{project}_{timestamp}"
        self.run_dir.mkdir(exist_ok=True)

        self.metrics_file = self.run_dir / "metrics.jsonl"
        self.config_file = self.run_dir / "config.json"
        self.model_dir = self.run_dir / "model_params"
        self.model_dir.mkdir(exist_ok=True)

        with open(self.config_file, "w") as f:
            json.dump(
                {"project": project, "mode": mode, "start_time": timestamp}, f, indent=2
            )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.finish()

    def watch(self, model, log="all"):
        self.model = model
        self.log_mode = log

        if self.mode == "disabled":
            return

        if log in ["all", "parameters", "gradients"]:
            self._log_model_params(label="initial")

    def _log_model_params(self, label=None):
        params_info = {}
        for name, param in self.model.named_parameters():
            numel = param.numel()
            params_info[name] = {
                "shape": list(param.shape),
                "mean": float(param.mean().item()),
                "std": float(param.std(correction=0).item()) if numel > 0 else 0.0,
                "min": float(param.min().item()),
                "max": float(param.max().item()),
                "requires_grad": param.requires_grad,
            }

        tag = label if label is not None else f"step_{self.step}"
        params_file = self.model_dir / f"params_{tag}.json"
        with open(params_file, "w") as f:
            json.dump(params_info, f, indent=2)

    def log(self, metrics):
        self.step += 1
        log_entry = {
            "step": self.step,
            "timestamp": datetime.now().isoformat(),
            **metrics,
        }
        self.metrics.append(log_entry)

        if self.mode == "disabled":
            return

        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()  # Force write to disk for live viewing

    def finish(self):
        if self.mode == "disabled" or self.run_dir is None:
            return

        if self.model is not None and self.log_mode in ["all", "parameters", "gradients"]:
            self._log_model_params(label="final")

        summary_file = self.run_dir / "summary.json"
        summary = {
            "total_steps": self.step,
            "end_time": datetime.now().isoformat(),
            "metrics_summary": {},
        }

        if self.metrics:
            for key in self.metrics[0].keys():
                if key not in ["step", "timestamp"]:
                    values = [m[key] for m in self.metrics if key in m and isinstance(m[key], (int, float))]
                    if values:
                        summary["metrics_summary"][key] = {
                            "min": float(min(values)),
                            "max": float(max(values)),
                            "mean": float(sum(values) / len(values)),
                            "final": float(values[-1]),
                        }

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"Logging saved to: {self.run_dir}")
