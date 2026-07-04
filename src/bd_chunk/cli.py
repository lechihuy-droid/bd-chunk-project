import typer

app = typer.Typer()

@app.command()
def health():
    typer.echo("bdchunk ok")
