from __future__ import annotations
import json
import typer
from . import facts as F
from . import gallery
from . import render as R

app = typer.Typer(help="A ghosts in the decentralized world computer", no_args_is_help=True)
app.add_typer(gallery.app, name="gallery")


@app.command()
def summon(address: str, site: list[str] = typer.Option(None, "--site", help="Website(s) the dapp lived at"),
           force: bool = typer.Option(False, help="Refetch even if facts.json exists")):
    """Gather the code-verified facts of one contract into data/ghosts/<address>/facts.json."""
    f = F.summon(address, site, force=force)
    life, chain, birth = f.get("life") or {}, f.get("chain") or {}, f.get("birth") or {}
    typer.echo(f"{f['name']}  {f['address']}")
    typer.echo(f"  born   {str(birth.get('timestamp'))[:10]}  block {birth.get('block')}  age {(f.get('age') or {}).get('hardfork')}")
    lt = life.get("last_tx") or {}
    typer.echo(f"  life   {life.get('tx_count')} txs, last {str(lt.get('timestamp'))[:10]} {lt.get('method')}  balance {chain.get('balance_eth', life.get('balance_eth'))} ETH  code {'present' if chain.get('code_present') else 'GONE'}")
    typer.echo(f"  source {(f.get('source') or {}).get('provider')} {(f.get('source') or {}).get('compiler_version')}  story {'yes' if (f.get('eh') or {}).get('short_description') else 'no'}  sites {[s.get('host') for s in f.get('sites', [])]}")
    typer.echo(f"  via    {', '.join(f['sources_used'])}")


@app.command()
def show(address: str):
    """Print facts.json."""
    typer.echo(json.dumps(F.summon(address), indent=1))



@app.command()
def render(address: str):
    """Render web/ghosts/<address>/index.html from the ghost's data."""
    typer.echo(R.render(address))


@app.command("render-all")
def render_all():
    """Render every ghost in data/ghosts."""
    for p in R.render_all():
        typer.echo(p)


@app.command("classify")
def classify_cmd(address: str, rerun_wounds: bool = typer.Option(False, "--rerun-wounds")):
    """Decide what kind of ghost a contract is (writes verdict.json)."""
    from .classify import classify as _c
    v = _c(address, rerun_wounds=rerun_wounds)
    typer.echo(v["kind"])
    for r in v["reasons"]:
        typer.echo(f"  - {r}")


@app.command("wounds")
def wounds_cmd(address: str, no_slither: bool = typer.Option(False, "--no-slither")):
    """Look for vulnerabilities (writes wounds.json)."""
    from .wounds import analyze
    w = analyze(address, use_slither=not no_slither)
    typer.echo(f"tier {w['tier']} {len(w['findings'])} findings")


from .pick import pick_cmd  # noqa: E402
app.command("pick")(pick_cmd)
from .incidents import app as incidents_app  # noqa: E402
app.add_typer(incidents_app, name="incidents")
from .face import face_cmd  # noqa: E402
app.command("face")(face_cmd)


from .story import cli_story  # noqa: E402
app.command("story")(cli_story)


from .haunt import haunt_cmd  # noqa: E402
app.command("haunt")(haunt_cmd)


from .og import og_cmd, og_all_cmd  # noqa: E402
app.command("og")(og_cmd)
app.command("og-all")(og_all_cmd)


if __name__ == "__main__":
    app()
