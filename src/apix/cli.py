import typer

app = typer.Typer()


@app.command()
def get():
    pass


@app.command()
def post():
    pass


@app.command()
def put():
    pass


@app.command()
def patch():
    pass


@app.command()
def delete():
    pass


if __name__ == "__main__":
    app()
