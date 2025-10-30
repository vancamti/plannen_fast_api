from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .handlers import validation_exception_handler


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
