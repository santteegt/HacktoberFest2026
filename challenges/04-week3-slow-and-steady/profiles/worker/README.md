# Worker profile (`sloth-worker`)

> **Hermes profile distribution.** Install with `scripts/install.sh` (or `hermes profile install profiles/worker --name sloth-worker`, then fill `__SLOTH_HOME__` / `__SLOTH_PROTOTYPES__`). Refresh from the live profile with `scripts/export-profiles.sh`. `SOUL.md`, `config.yaml`, `skills/`, `cron/jobs.json` and `scripts/` here are exported from the live profile; edit them in Hermes and export, or edit here and re-run the install.

The Worker's distribution (owned by Lane 3).

- `skills/prototype-box/SKILL.md`: how the Worker builds a card inside the box. The runner (`sloth work`) also inlines this text into the task prompt, so a run does not depend on the skill being installed.
- `skills/worker-desk/SKILL.md`: the Worker bot's Discord desk in `#sk-worker` (`go`, `go deep`, `approve <run_id>`, `publish <run_id>`, `status` → `sloth` commands with `--project`).
- Two providers, chosen at `go` time: `go` runs the open-weights default (`llm.worker_provider` / `worker_model`, OpenRouter `google/gemma-4-26b-a4b-it`); `go deep` runs `sloth work --complex` on `llm.complex_provider` / `complex_model` (Anthropic `claude-sonnet-5-5`, closed, needs `ANTHROPIC_API_KEY` in the profile `.env`). Messages tag closed runs "(closed model, complex task)".
- Approval wording lives in `sloth/builder/approval.py`; `sloth work` and `sloth approve` post it.

Profile settings the runner relies on (set by the coordinator, see `docs/lanes/builder.md`): `model.provider: openrouter`, `model.default: <llm.openrouter_model>`, `terminal.cwd` under `~/GitRepositories/skunkworks-prototypes`, browser and computer-use toolsets disabled, approvals manual with the deny list.
