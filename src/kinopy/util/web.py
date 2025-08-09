"""
This module mimics `requests.api` so that it can be used as a drop-in replacement.
The difference is that `kinopy` uses a common Session object to set the `User-Agent` header.
"""
import requests

import kinopy

SESSION = requests.Session()
SESSION.headers["User-Agent"] = f"kinopy {kinopy.__version__}"


def request(method, url, **kwargs):
    # By using the 'with' statement we are sure the session is closed, thus we
    # avoid leaving sockets open which can trigger a ResourceWarning in some
    # cases, and look like a memory leak in others.
    with SESSION as session:
        return session.request(method=method, url=url, **kwargs)


def get(url, params=None, **kwargs):
    return request("get", url, params=params, **kwargs)


def options(url, **kwargs):
    return request("options", url, **kwargs)


def head(url, **kwargs):
    kwargs.setdefault("allow_redirects", False)
    return request("head", url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request("post", url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request("put", url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request("patch", url, data=data, **kwargs)


def delete(url, **kwargs):
    return request("delete", url, **kwargs)
