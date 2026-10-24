# `make test` must pass and `make demo` must show the done-means for the card to count as done.
.PHONY: test demo

test:
	uv run --with pytest pytest -q

demo:
	uv run python demo.py
