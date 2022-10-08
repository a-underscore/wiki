from server import app, db


def run_app():
    db.create_all()

    return app


if __name__ == "__main__":
    db.create_all()

    app.run(debug=__debug__)
