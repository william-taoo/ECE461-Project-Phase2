"""
Tests for CustomObjects.LLMQuerier.

These unit tests verify that LLMQuerier.query correctly handles:
 - successful HTTP responses and JSON parsing
 - non-200 HTTP status codes
 - exceptions raised by the requests layer

The tests mock the requests.post call so no network I/O occurs.
"""

from __future__ import annotations
import json
import requests
import pytest
from unittest.mock import MagicMock
from typing import Any
from CustomObjects.LLMQuerier import LLMQuerier

class DummyResponse:
    def __init__(self, status_code: int, content: bytes) -> None:
        self.status_code = status_code
        self.content = content


def test_query_success(monkeypatch: Any) -> None:
    dummy = DummyResponse(200, json.dumps({
        'choices': [
            {'message': {'content': '  Hello world  '}}
        ]
    }).encode('utf-8'))

    def fake_post(url: str, headers: str=None, json: str=None) -> DummyResponse:
        return dummy

    monkeypatch.setattr(requests, 'post', fake_post)

    q = LLMQuerier(endpoint='https://example.com/api', api_key='key')
    out = q.query('hi')
    assert out == 'Hello world'


def test_query_non_200(monkeypatch: Any) -> None:
    dummy = DummyResponse(500, b'')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: dummy)
    q = LLMQuerier(endpoint='https://example.com/api', api_key='key')
    assert q.query('x') is None


def test_query_exception(monkeypatch: Any) -> None:
    def raise_exc(*args: Any, **kwargs: Any) -> RuntimeError:
        raise RuntimeError('boom')
    monkeypatch.setattr(requests, 'post', raise_exc)
    q = LLMQuerier(endpoint='https://example.com/api', api_key='key')
    assert q.query('hi') is None
