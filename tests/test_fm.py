import pytest
from pytest import fixture
from quart import Quart
from quart_minify.minify import Minify

app = Quart(__name__)


@app.route("/html")
def html():
    return """<html>
            <body>
                <h1>
                    HTML
                </h1>
            </body>
        </html>"""


@app.route("/bypassed")
def bypassed():
    return """<html>
            <body>
                <h1>
                    HTML
                </h1>
            </body>
        </html>"""


@app.route("/js")
def js():
    return """<script>
        ["J", "S"].reduce(
            function (a, r) {
                return a + r
            })
    </script>"""


@app.route("/cssless")
def cssless():
    return """<style>
        @a: red;
        body {
            color: @a;
        }
    </style>"""


@app.route("/cssless_false")
def cssless_false():
    return """<style>
        body {
            color: red;;
        }
    </style>"""


@fixture
def client():
    app.config["TESTING"] = True
    client = app.test_client()
    yield client


@pytest.mark.asyncio
async def test_html_bypassing(client):
    """ testing HTML route bypassing """
    Minify(app=app, html=True, cssless=False, js=False, bypass=["/html"])

    resp = await client.get("/html")
    data = await resp.get_data()

    assert b"<html> <body> <h1> HTML </h1> </body> </html>" != data


@pytest.mark.asyncio
async def test_html_minify(client):
    """ testing HTML minify option """
    Minify(app=app, html=True, cssless=False, js=False)

    resp = await client.get("/html")
    data = await resp.get_data()

    assert b"<html> <body> <h1> HTML </h1> </body> </html>" == data


@pytest.mark.asyncio
async def test_javascript_minify(client):
    """ testing JavaScript minify option """
    Minify(app=app, html=False, cssless=False, js=True)

    resp = await client.get("/js")
    data = await resp.get_data()

    assert b'<script>["J","S"].reduce(function(a,r){return a+r})</script>' == data


@pytest.mark.asyncio
async def test_lesscss_minify(client):
    """ testing css and less minify option """
    Minify(app=app, html=False, cssless=True, js=False)

    resp = await client.get("/cssless")
    data = await resp.get_data()

    assert b"<style>body{color:red;}</style>" == data


@pytest.mark.asyncio
async def test_minify_cache(client):
    """ testing caching minifed response """
    minify_store = Minify(app=app, js=False, cssless=True, cache=True)

    first_resp = await client.get("/cssless")
    # to cover hashing return
    first_resp_data = await first_resp.get_data()  # noqa: F841

    resp = await client.get("/cssless")
    second_resp_data = await resp.get_data()

    assert (
        second_resp_data.decode("utf8").replace("<style>", "").replace("</style>", "")
        in minify_store.history.values()
    )


def test_false_input(client):
    """ testing false input for raise coverage """
    try:
        Minify(app=None)
    except Exception as e:
        assert type(e) is AttributeError
    try:
        Minify(app, "nothing", "nothing")
    except Exception as e:
        assert type(e) is TypeError


@pytest.mark.asyncio
async def test_fail_safe(client):
    """ testing fail safe enabled with false input """
    Minify(app=app, fail_safe=True)

    resp = await client.get("/cssless_false")
    data = await resp.get_data()

    assert (
        b"""<style>
        body {
            color: red;;
        }
    </style>"""
        == data
    )


@pytest.mark.asyncio
async def test_fail_safe_false_input(client):
    """testing fail safe disabled with false input """
    Minify(app=app, fail_safe=False, cache=False)
    try:
        await client.get("/cssless_false")
    except Exception as e:
        assert "CompilationError" == e.__class__.__name__
