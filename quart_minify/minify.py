from hashlib import md5
from io import StringIO

from htmlmin import minify as minify_html
from jsmin import jsmin
from lesscpy import compile
from quart import request


class Minify:
    def __init__(
        self, app=None, html=True, js=True, cssless=True, cache=True, fail_safe=True, bypass=()
    ):
        """
        A Quart extension to minify flask response for html,
        javascript, css and less.
        @param: app Quart app instance to be passed (default:None).
        @param: js To minify the css output (default:False).
        @param: cssless To minify spaces in css (default:True).
        @param: cache To cache minifed response with hash (default: True).
        @param: fail_safe to avoid raising error while minifying (default True)
        @param: bypass a list of the routes to be bypassed by the minifer
        """
        self.app = app
        self.html = html
        self.js = js
        self.cssless = cssless
        self.cache = cache
        self.fail_safe = fail_safe
        self.bypass = bypass
        self.history = {}  # where cache hash and compiled response stored
        self.hashes = {}  # where the hashes and text will be stored

        for arg in ["cssless", "js", "html", "cache"]:
            if not isinstance(eval(arg), bool):
                raise (TypeError("minify(" + arg + "=) requires True or False"))

        if self.app:
            self.init_app(self.app)

    def init_app(self, app):
        self.app = app
        self.app.after_request(self.to_loop_tag)

    def get_hashed(self, text):
        """ to return text hashed and store it in hashes """
        if text in self.hashes.keys():
            return self.hashes.get(text)
        else:
            hashed = md5(text.encode("utf8")).hexdigest()[:9]
            self.hashes[text] = hashed
            return hashed

    def store_minifed(self, css, text, to_replace):
        """ to minify and store in history with hash key """
        if self.cache and self.get_hashed(text) in self.history.keys():
            return self.history[self.get_hashed(text)]
        else:
            minifed = (
                compile(StringIO(to_replace), minify=True, xminify=True)
                if css
                else jsmin(to_replace).replace("\n", ";")
            )

            if self.cache and self.get_hashed(text) not in self.history.keys():
                self.history[self.get_hashed(text)] = minifed

            return minifed

    async def to_loop_tag(self, response):
        if (
            response.content_type == "text/html; charset=utf-8"
            and request.url_rule.rule not in self.bypass
        ):
            response.direct_passthrough = False
            text = await response.get_data(raw=False)

            for tag in [t for t in [(0, "style")[self.cssless], (0, "script")[self.js]] if t != 0]:
                if f"<{tag} type=" in text or f"<{tag}>" in text:
                    for i in range(1, len(text.split(f"<{tag}"))):
                        to_replace = (
                            text.split(f"<{tag}", i)[i].split(f"</{tag}>")[0].split(">", 1)[1]
                        )

                        result = None
                        try:
                            result = (
                                text.replace(
                                    to_replace, self.store_minifed(tag == "style", text, to_replace)
                                )
                                if len(to_replace) > 2
                                else text
                            )
                            text = result
                        except Exception as e:
                            if self.fail_safe:
                                text = result or text
                            else:
                                raise e

            final_resp = minify_html(text) if self.html else text
            response.set_data(final_resp)

        return response
