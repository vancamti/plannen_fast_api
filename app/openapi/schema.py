from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def apply_custom_openapi(
    app: FastAPI,
    *,
    title: str = "My API",
    version: str = "1.0.0",
    description: str = "Custom error codes",
) -> None:
    """
    Patch app.openapi to generate a schema where
    validation errors are documented as 400 instead of 422.
    Call this after routers are included so
    routes are complete when the schema is generated.
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
        )

        # Replace all 422 responses with 400 in the schema
        for path_item in openapi_schema.get("paths", {}).values():
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                responses = operation.get("responses", {})
                if "422" in responses:
                    responses["400"] = responses.pop("422")

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # install the override
