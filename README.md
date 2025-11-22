# quart_minify
[![Build Status](https://travis-ci.org/AceFire6/quart_minify.svg?branch=master)](https://travis-ci.org/AceFire6/quart_minify)
[![Coverage Status](https://coveralls.io/repos/github/AceFire6/quart_minify/badge.svg?branch=master)](https://coveralls.io/github/AceFire6/quart_minify?branch=master)

A Quart extension to minify quart response for html, javascript, css and less compilation as well.</h3>

## Install:
#### With pip
- `pip install quart-minify`

#### From the source:
- `git clone https://github.com/AceFire6/quart_minify.git`
- `cd quart_minify`
- `python setup.py install`

## Setup:
### Inside Quart app:

```python
from quart import Quart
from quart_minify.minify import Minify

app = Quart(__name__)
Minify(app=app)
```

### Result:

#### Before:
```html
<html>
  <head>
    <script>
      if (true) {
      	console.log('working !')
      }
    </script>
    <style>
      body {
      	background-color: red;
      }
    </style>
  </head>
  <body>
    <h1>Example !</h1>
  </body>
</html>
```
#### After:
```html
<html> <head><script>if(true){console.log('working !')}</script><style>body{background-color:red;}</style></head> <body> <h1>Example !</h1> </body> </html>
```

## Options:
```python
def __init__(self,
  app=None,
  html=True,
  js=False,
  cssless=True,
  cache=True,
  fail_safe=True,
  bypass=(),
  remove_console=False,
  console_types=('log', 'warn', 'error'),
  remove_debugger=False,
  cache_limit=100):
  """
    A Quart extension to minify flask response for html,
    javascript, css and less.
    @param: app Quart app instance to be passed (default:None).
    @param: js To minify the css output (default:False).
    @param: cssless To minify spaces in css (default:True).
    @param: cache To cache minifed response with hash (default: True).
    @param: fail_safe to avoid raising error while minifying (default True).
    @param: bypass a list of the routes to be bypassed by the minifier
    @param: remove_console Remove console statements from JavaScript (default: False).
    @param: console_types Tuple of console types to remove: 'log', 'warn', 'error' (default: ('log', 'warn', 'error')).
    @param: remove_debugger Remove debugger statements from JavaScript (default: False).
    @param: cache_limit Maximum number of items to keep in cache, uses LRU eviction (default: 100).
    Notice: bypass route should be identical to the url_rule used for example:
    bypass=['/user/<int:user_id>', '/users']
  """
```

### Advanced Features:

#### Console Removal
Remove all console statements (log, warn, error):
```python
Minify(app=app, remove_console=True)
```

Remove only `console.log`:
```python
Minify(app=app, remove_console=True, console_types=('log',))
```

Remove only `console.warn` and `console.error`:
```python
Minify(app=app, remove_console=True, console_types=('warn', 'error'))
```

#### Debugger Removal
Remove all `debugger;` statements from JavaScript:
```python
Minify(app=app, remove_debugger=True)
```

#### Cache Control
Set custom cache limit with LRU eviction (default: 100 items):
```python
Minify(app=app, cache_limit=50)  # Only cache 50 most recent responses
```

#### Combined Example (Production Ready)
Remove console logs and debugger statements for production:
```python
Minify(
    app=app,
    html=True,
    js=True,
    cssless=True,
    remove_console=True,
    remove_debugger=True,
    cache_limit=200
)
```

## What's New:

### Security & Performance Improvements:
- ✅ **Fixed `eval()` security vulnerability** - No longer uses `eval()` for parameter validation
- ✅ **LRU Cache with size limit** - Prevents memory leaks with configurable `cache_limit`
- ✅ **Improved console removal** - Better handling of nested parentheses and string literals
- ✅ **Debugger statement removal** - New `remove_debugger` option for production builds

## Credit:
Adapted from [flask_minify](https://github.com/mrf345/flask_minify)

- [htmlmin][1322354e]: HTML python minifier.
- [lesscpy][1322353e]: Python less compiler and css minifier.
- [jsmin][1322355e]: JavaScript python minifier.

[1322353e]: https://github.com/lesscpy/lesscpy "lesscpy repo"
[1322354e]: https://github.com/mankyd/htmlmin "htmlmin repo"
[1322355e]: https://github.com/tikitu/jsmin "jsmin repo"
