"""Ghost-buster recipes (one per wound check) and the solc 0.8.38 compile gate."""
from .recipes import R as RECIPES, recipe_for, apply_renames, meaning_problems  # noqa: F401
from .compile import compile_solidity, VERSION  # noqa: F401
