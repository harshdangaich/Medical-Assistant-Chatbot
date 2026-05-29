from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from middlewares.exception_handlers import catch_exception_middleware
from routes.upload_pdfs import router as upload_router
from routes.ask_question import router as ask_router



app=FastAPI(title="Medical Assistant API",description="API for AI Medical Assistant Chatbot")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    upload_path = openapi_schema.get("paths", {}).get("/upload_pdfs/", {})
    post_schema = upload_path.get("post", {})
    content = post_schema.get("requestBody", {}).get("content", {})
    multipart_schema = content.get("multipart/form-data", {}).get("schema", {})
    ref = multipart_schema.get("$ref", "")

    if ref:
        schema_name = ref.split("/")[-1]
        component = openapi_schema.get("components", {}).get("schemas", {}).get(schema_name, {})
        files_property = component.get("properties", {}).get("files", {})
        items = files_property.get("items", {})
        if items.get("type") == "string":
            items.pop("contentMediaType", None)
            items["format"] = "binary"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



# middleware exception handlers
app.middleware("http")(catch_exception_middleware)

# routers

# 1. upload pdfs documents
app.include_router(upload_router)
# 2. asking query
app.include_router(ask_router)
