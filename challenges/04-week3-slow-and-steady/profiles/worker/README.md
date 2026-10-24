# Worker profile (`sloth-worker`)

Text the coordinator installs into the Hermes profile `sloth-worker` (owned by Lane 3; `~/.hermes/` is coordinator-only).

- `skills/prototype-box/SKILL.md`: how the Worker builds a card inside the box. The runner (`sloth work`) also inlines this text into the task prompt, so a run does not depend on the skill being installed.
- `skills/worker-desk/SKILL.md`: the Worker bot's Discord desk in `#sk-worker` (`go`, `approve <run_id>`, `publish <run_id>`, `status` → `sloth` commands with `--project`).
- Approval wording lives in `sloth/builder/approval.py`; `sloth work` and `sloth approve` post it.

Profile settings the runner relies on (set by the coordinator, see `docs/lanes/builder.md`): `model.provider: openrouter`, `model.default: <llm.openrouter_model>`, `terminal.cwd` under `~/GitRepositories/skunkworks-prototypes`, browser and computer-use toolsets disabled, approvals manual with the deny list.
