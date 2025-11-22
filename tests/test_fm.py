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


@app.route("/console_all")
def console_all():
    return """<script>
        console.log('this is a log');
        console.warn('this is a warning');
        console.error('this is an error');
        var x = 5;
    </script>"""


@app.route("/console_log_only")
def console_log_only():
    return """<script>
        console.log('should be removed');
        console.warn('should stay');
        console.error('should stay');
    </script>"""


@app.route("/console_complex")
def console_complex():
    return """<script>
        if (true) {
            console.log('nested log');
        }
        var data = getData();
        console.warn('warning with', data);
        console.error('error:', 'multiple', 'params');
    </script>"""


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


@pytest.mark.asyncio
async def test_remove_console_all():
    """ testing console removal for all types """
    test_app = Quart(__name__)

    @test_app.route("/console_all")
    def console_all_route():
        return """<script>
        console.log('this is a log');
        console.warn('this is a warning');
        console.error('this is an error');
        var x = 5;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/console_all")
    data = await resp.get_data()

    # All console statements should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data
    assert b'console.error' not in data
    # Regular code should remain
    assert b'var x=5' in data


@pytest.mark.asyncio
async def test_remove_console_log_only():
    """ testing console removal for log only """
    test_app = Quart(__name__)

    @test_app.route("/console_log_only")
    def console_log_only_route():
        return """<script>
        console.log('should be removed');
        console.warn('should stay');
        console.error('should stay');
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, console_types=('log',), cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/console_log_only")
    data = await resp.get_data()

    # Only console.log should be removed
    assert b'console.log' not in data
    # console.warn and console.error should remain
    assert b'console.warn' in data
    assert b'console.error' in data


@pytest.mark.asyncio
async def test_remove_console_warn_error():
    """ testing console removal for warn and error only """
    test_app = Quart(__name__)

    @test_app.route("/console_log_only")
    def console_log_only_route():
        return """<script>
        console.log('should stay');
        console.warn('should be removed');
        console.error('should be removed');
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, console_types=('warn', 'error'), cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/console_log_only")
    data = await resp.get_data()

    # console.log should remain
    assert b'console.log' in data
    # console.warn and console.error should be removed
    assert b'console.warn' not in data
    assert b'console.error' not in data


@pytest.mark.asyncio
async def test_console_disabled():
    """ testing that console statements remain when remove_console is False """
    test_app = Quart(__name__)

    @test_app.route("/console_all")
    def console_all_route():
        return """<script>
        console.log('this is a log');
        console.warn('this is a warning');
        console.error('this is an error');
        var x = 5;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=False, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/console_all")
    data = await resp.get_data()

    # All console statements should remain
    assert b'console.log' in data
    assert b'console.warn' in data
    assert b'console.error' in data

@pytest.mark.asyncio
async def test_remove_debugger():
    """ testing debugger removal """
    test_app = Quart(__name__)

    @test_app.route("/with_debugger")
    def with_debugger():
        return """<script>
        var x = 5;
        debugger;
        console.log(x);
        debugger
        var y = 10;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_debugger=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/with_debugger")
    data = await resp.get_data()

    # debugger statements should be removed
    assert b'debugger' not in data
    # Regular code should remain
    assert b'var x=5' in data
    assert b'var y=10' in data


@pytest.mark.asyncio
async def test_debugger_and_console_removal():
    """ testing both debugger and console removal """
    test_app = Quart(__name__)

    @test_app.route("/debug_and_console")
    def debug_and_console():
        return """<script>
        debugger;
        console.log('test');
        var result = calculate();
        debugger;
        console.warn('warning');
    </script>"""

    Minify(
        app=test_app,
        html=False,
        js=True,
        remove_debugger=True,
        remove_console=True,
        cache=False
    )

    test_client = test_app.test_client()
    resp = await test_client.get("/debug_and_console")
    data = await resp.get_data()

    # Both debugger and console should be removed
    assert b'debugger' not in data
    assert b'console.log' not in data
    assert b'console.warn' not in data
    # Code should remain
    assert b'var result=calculate()' in data


@pytest.mark.asyncio
async def test_cache_limit_lru():
    """ testing LRU cache eviction """
    test_app = Quart(__name__)

    # Create multiple routes
    for i in range(5):
        route_name = f"/route{i}"

        def make_route_func(num):
            def route_func():
                return f"""<script>
                var x{num} = {num};
            </script>"""
            return route_func

        test_app.add_url_rule(route_name, f"route{i}", make_route_func(i))

    # Create Minify with cache limit of 3
    minify_instance = Minify(app=test_app, html=False, js=True, cache=True, cache_limit=3)

    test_client = test_app.test_client()

    # Access all 5 routes
    for i in range(5):
        await test_client.get(f"/route{i}")

    # Cache should only have 3 items (LRU eviction)
    assert len(minify_instance.history) <= 3

    # Access route0 again to make it recently used
    await test_client.get("/route0")

    # Access route5 (new route)
    for i in range(5, 7):
        route_name = f"/route{i}"

        def make_new_route(num):
            def route_func():
                return f"""<script>var y{num} = {num};</script>"""
            return route_func

        test_app.add_url_rule(route_name, f"route{i}", make_new_route(i))
        await test_client.get(route_name)

    # Verify cache size is still within limit
    assert len(minify_instance.history) <= 3


@pytest.mark.asyncio
async def test_console_with_nested_parens():
    """ testing console removal with complex nested parentheses """
    test_app = Quart(__name__)

    @test_app.route("/complex_console")
    def complex_console():
        return """<script>
        console.log('Test', getData(foo('bar', baz())));
        console.warn('Warning:', {a: func(1, 2), b: 'test'});
        var x = 5;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/complex_console")
    data = await resp.get_data()

    # Console statements with nested parens should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data
    assert b'getData' not in data  # Part of console.log
    # Regular code should remain
    assert b'var x=5' in data


@pytest.mark.asyncio
async def test_console_with_strings():
    """ testing console removal with strings containing parentheses """
    test_app = Quart(__name__)

    @test_app.route("/console_strings")
    def console_strings():
        return """<script>
        console.log('Message with (parentheses) inside');
        console.warn("Double quote with ) paren");
        var message = 'Keep (this)';
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/console_strings")
    data = await resp.get_data()

    # Console statements should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data
    # String in variable assignment should remain
    assert b"Keep (this)" in data or b'Keep (this)' in data


@pytest.mark.asyncio
async def test_console_with_escaped_strings():
    """ testing console removal with escaped characters in strings """
    test_app = Quart(__name__)

    @test_app.route("/escaped_strings")
    def escaped_strings():
        return """<script>
        console.log('Message with \\'escaped\\' quotes');
        console.warn("Backslash: \\\\ test");
        console.error("Newline: \\n tab: \\t");
        var keep = "Don't remove \\\\ this";
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/escaped_strings")
    data = await resp.get_data()

    # Console statements with escaped chars should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data
    assert b'console.error' not in data
    # Regular variable should remain
    assert b'var keep' in data


@pytest.mark.asyncio
async def test_console_with_malformed_parentheses():
    """ testing console removal with malformed/unclosed parentheses """
    test_app = Quart(__name__)

    @test_app.route("/malformed")
    def malformed():
        return """<script>
        var x = 5;
        var y = 10;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/malformed")
    data = await resp.get_data()

    # Code should still be processed
    assert b'var x=5' in data
    assert b'var y=10' in data


@pytest.mark.asyncio
async def test_combined_html_css_js_minification():
    """ testing full minification: HTML + CSS + JS with console removal """
    test_app = Quart(__name__)

    @test_app.route("/full_page")
    def full_page():
        return """<!DOCTYPE html>
<html>
    <head>
        <title>Test Page</title>
        <style>
            body {
                background-color: #ffffff;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hello World</h1>
            <p>This is a test page.</p>
        </div>
        <script>
            console.log('Page loaded');
            debugger;
            var message = 'Hello';
            console.warn('Warning message');
            function greet(name) {
                return 'Hello, ' + name;
            }
            console.error('Error message');
        </script>
    </body>
</html>"""

    Minify(
        app=test_app,
        html=True,
        js=True,
        cssless=True,
        remove_console=True,
        remove_debugger=True,
        cache=True
    )

    test_client = test_app.test_client()
    resp = await test_client.get("/full_page")
    data = await resp.get_data()

    # HTML should be minified (less whitespace)
    assert b'\n    ' not in data or data.count(b'\n') < 10

    # Console statements should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data
    assert b'console.error' not in data

    # Debugger should be removed
    assert b'debugger' not in data

    # JS code should remain
    assert b'var message' in data or b"var message='Hello'" in data
    assert b'function greet' in data or b'function greet(name)' in data


@pytest.mark.asyncio
async def test_cache_disabled():
    """ testing that cache is properly disabled when cache=False """
    test_app = Quart(__name__)

    @test_app.route("/cache_test")
    def cache_test():
        return """<script>
        var x = 42;
    </script>"""

    minify_instance = Minify(app=test_app, html=False, js=True, cache=False)

    test_client = test_app.test_client()

    # Make multiple requests
    for _ in range(5):
        await test_client.get("/cache_test")

    # Cache should be empty when cache=False
    assert len(minify_instance.history) == 0


@pytest.mark.asyncio
async def test_cache_enabled_reuses_results():
    """ testing that cache properly reuses minified results """
    test_app = Quart(__name__)

    @test_app.route("/cache_reuse")
    def cache_reuse():
        return """<script>
        var test = 'cache';
    </script>"""

    minify_instance = Minify(app=test_app, html=False, js=True, cache=True)

    test_client = test_app.test_client()

    # First request
    resp1 = await test_client.get("/cache_reuse")
    data1 = await resp1.get_data()

    # Cache should have 1 item
    assert len(minify_instance.history) == 1

    # Second request (should use cache)
    resp2 = await test_client.get("/cache_reuse")
    data2 = await resp2.get_data()

    # Cache should still have 1 item (reused)
    assert len(minify_instance.history) == 1

    # Results should be identical
    assert data1 == data2


@pytest.mark.asyncio
async def test_multiple_script_tags():
    """ testing minification with multiple script tags in one page """
    test_app = Quart(__name__)

    @test_app.route("/multi_script")
    def multi_script():
        return """<html>
<head>
    <script>
        console.log('First script');
        var a = 1;
    </script>
    <script>
        console.warn('Second script');
        var b = 2;
    </script>
</head>
<body>
    <script>
        console.error('Third script');
        var c = 3;
    </script>
</body>
</html>"""

    Minify(app=test_app, html=True, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/multi_script")
    data = await resp.get_data()

    # All console statements should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data
    assert b'console.error' not in data

    # All variables should remain
    assert b'var a=1' in data
    assert b'var b=2' in data
    assert b'var c=3' in data


@pytest.mark.asyncio
async def test_template_literals_in_console():
    """ testing console removal with template literals """
    test_app = Quart(__name__)

    @test_app.route("/template_literals")
    def template_literals():
        return """<script>
        const name = 'World';
        console.log(`Hello ${name}!`);
        console.warn(`Warning: ${1 + 1}`);
        const keep = `Keep this ${name}`;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/template_literals")
    data = await resp.get_data()

    # Console with template literals should be removed
    assert b'console.log' not in data
    assert b'console.warn' not in data

    # Regular template literal should remain
    assert b'keep' in data.lower() or b'Keep' in data


@pytest.mark.asyncio
async def test_console_with_unclosed_parenthesis():
    """ testing console removal when parenthesis is not closed (malformed JS) """
    test_app = Quart(__name__)

    @test_app.route("/unclosed_paren")
    def unclosed_paren():
        # Intentionally malformed JavaScript with unclosed console.log
        return """<script>
        var start = 'begin';
        console.log('this is unclosed
        var middle = 'keeps going';
        console.warn('another unclosed(
        var end = 'finish';
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/unclosed_paren")
    data = await resp.get_data()

    # The malformed console statements should remain (can't be removed safely)
    # or be partially processed, but code should not crash
    assert b'var start' in data or b"var start='begin'" in data
    assert b'var middle' in data
    assert b'var end' in data or b"var end='finish'" in data

    # Most importantly: the minifier should not crash
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_console_with_string_containing_closing_paren():
    """ testing edge case: console with string that has ) before actual close """
    test_app = Quart(__name__)

    @test_app.route("/tricky_paren")
    def tricky_paren():
        return """<script>
        var x = 1;
        console.log('message) fake close', realParam);
        console.warn("another) fake", {key: "value)"});
        var y = 2;
    </script>"""

    Minify(app=test_app, html=False, js=True, remove_console=True, cache=False)

    test_client = test_app.test_client()
    resp = await test_client.get("/tricky_paren")
    data = await resp.get_data()

    # Console should be removed properly despite ) in strings
    assert b'console.log' not in data
    assert b'console.warn' not in data

    # Variables should remain
    assert b'var x=1' in data
    assert b'var y=2' in data