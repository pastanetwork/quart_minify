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
  bypass=()):
  """
    A Quart extension to minify flask response for html,
    javascript, css and less.
    @param: app Quart app instance to be passed (default:None).
    @param: js To minify the css output (default:False).
    @param: cssless To minify spaces in css (default:True).
    @param: cache To cache minifed response with hash (default: True).
    @param: fail_safe to avoid raising error while minifying (default True).
    @param: bypass a list of the routes to be bypassed by the minifier
    Notice: bypass route should be identical to the url_rule used for example:
    bypass=['/user/<int:user_id>', '/users']
  """
```

## Credit:
Adapted from [flask_minify](https://github.com/mrf345/flask_minify)

- [htmlmin][1322354e]: HTML python minifier.
- [lesscpy][1322353e]: Python less compiler and css minifier.
- [jsmin][1322355e]: JavaScript python minifier.

[1322353e]: https://github.com/lesscpy/lesscpy "lesscpy repo"
[1322354e]: https://github.com/mankyd/htmlmin "htmlmin repo"
[1322355e]: https://github.com/tikitu/jsmin "jsmin repo"
