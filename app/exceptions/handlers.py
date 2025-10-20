from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse



#Todo: customize evt verder
async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
):
    # You can customize the body however you like
    return JSONResponse(
        status_code=400,
        content={
            "detail": [".".join(e["loc"]) + ": " + e["msg"] for e in exc.errors()],
            "body": exc.body,
            "message": "Bad Reqest"
        },
    )
