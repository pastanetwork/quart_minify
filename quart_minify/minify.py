from hashlib import md5
from io import StringIO
import re
from collections import OrderedDict

from htmlmin import minify as minify_html
from jsmin import jsmin
from lesscpy import compile
from quart import request


class Minify:
    def __init__(
        self,
        app=None,
        html=True,
        js=True,
        cssless=True,
        cache=True,
        fail_safe=True,
        bypass=(),
        remove_console=False,
        console_types=('log', 'warn', 'error'),
        remove_debugger=False,
        cache_limit=100
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
        @param: remove_console Remove console statements from JavaScript (default: False)
        @param: console_types Tuple of console types to remove: 'log', 'warn', 'error' (default: ('log', 'warn', 'error'))
        @param: remove_debugger Remove debugger statements from JavaScript (default: False)
        @param: cache_limit Maximum number of items to keep in cache (default: 100)
        """
        self.app = app
        self.html = html
        self.js = js
        self.cssless = cssless
        self.cache = cache
        self.fail_safe = fail_safe
        self.bypass = bypass
        self.remove_console = remove_console
        self.console_types = console_types
        self.remove_debugger = remove_debugger
        self.cache_limit = cache_limit
        # Use OrderedDict for LRU cache implementation
        self.history = OrderedDict()  # where cache hash and compiled response stored
        self.hashes = OrderedDict()  # where the hashes and text will be stored

        # Validate boolean parameters without using eval() (security fix)
        bool_params = {
            'cssless': cssless,
            'js': js,
            'html': html,
            'cache': cache,
            'remove_console': remove_console,
            'remove_debugger': remove_debugger
        }
        for param_name, param_value in bool_params.items():
            if not isinstance(param_value, bool):
                raise TypeError(f"minify({param_name}=) requires True or False")

        if self.app:
            self.init_app(self.app)

    def init_app(self, app):
        self.app = app
        self.app.after_request(self.to_loop_tag)

    def _evict_lru_cache(self, cache_dict):
        """
        Evict least recently used item from cache if limit is reached.
        @param: cache_dict The cache dictionary to evict from
        """
        if len(cache_dict) >= self.cache_limit:
            # Remove oldest (least recently used) item
            cache_dict.popitem(last=False)

    def get_hashed(self, text):
        """
        Return text hashed and store it in hashes with LRU eviction.
        @param: text The text to hash
        @return: The hash string
        """
        if text in self.hashes:
            self.hashes.move_to_end(text)
            return self.hashes[text]
        else:
            if self.cache and len(self.hashes) >= self.cache_limit:
                self._evict_lru_cache(self.hashes)

            hashed = md5(text.encode("utf8")).hexdigest()[:9]
            self.hashes[text] = hashed
            return hashed

    def _remove_balanced_parens(self, text, start_pos):
        """
        Helper to find and remove text with balanced parentheses.
        @param: text The text to search in
        @param: start_pos Position of opening parenthesis
        @return: End position of closing parenthesis, or -1 if not found
        """
        depth = 0
        in_string = False
        string_char = None
        escape_next = False

        for i in range(start_pos, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char in ('"', "'", '`') and not in_string:
                in_string = True
                string_char = char
                continue

            if in_string:
                if char == string_char:
                    in_string = False
                    string_char = None
                continue

            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    return i

        return -1

    def remove_console_statements(self, js_code):
        """
        Remove console statements from JavaScript code based on console_types.
        Uses improved parsing to handle nested parentheses and strings correctly.
        @param: js_code JavaScript code to process
        @return: JavaScript code with console statements removed
        """
        if not self.remove_console:
            return js_code

        result = js_code
        for console_type in self.console_types:
            pattern = rf'\bconsole\.{console_type}\s*\('
            offset = 0

            while True:
                match = re.search(pattern, result[offset:])
                if not match:
                    break

                abs_start = offset + match.start()
                paren_start = offset + match.end() - 1

                paren_end = self._remove_balanced_parens(result, paren_start)

                if paren_end == -1:
                    offset = paren_start + 1
                    continue

                before = result[:abs_start]
                after = result[paren_end + 1:]

                after = re.sub(r'^\s*;?\s*', '', after)

                result = before + after
                offset = abs_start

        return result

    def store_minifed(self, css, text, to_replace):
        """
        Minify and store in history with hash key, using LRU eviction.
        @param: css Whether this is CSS/LESS (True) or JavaScript (False)
        @param: text The full text being processed
        @param: to_replace The specific content to minify
        @return: Minified content
        """
        cache_key = self.get_hashed(text)

        if self.cache and cache_key in self.history:
            self.history.move_to_end(cache_key)
            return self.history[cache_key]
        else:
            if css:
                minifed = compile(StringIO(to_replace), minify=True, xminify=True)
            else:
                js_code = self.remove_console_statements(to_replace)

                if self.remove_debugger:
                    js_code = re.sub(r'\bdebugger\s*;?\s*', '', js_code)

                minifed = jsmin(js_code)

            if self.cache:
                if len(self.history) >= self.cache_limit:
                    self._evict_lru_cache(self.history)
                self.history[cache_key] = minifed

            return minifed

    async def to_loop_tag(self, response):
        if (
            response.content_type == "text/html; charset=utf-8"
            and (request.url_rule is None or request.url_rule.rule not in self.bypass)
        ):
            response.direct_passthrough = False
            text = await response.get_data(as_text=True)

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

            final_resp = minify_html(text, remove_comments=True) if self.html else text
            response.set_data(final_resp)

        return response
