from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from arbor_imago import config
from arbor_imago.routers import user, auth, user_access_token, api_key_scope, gallery, api_key, pages
from arbor_imago.auth import utils as auth_utils


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('startingup')
    yield
    print('closingdown')

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=list(config.HEADER_KEYS.values()),
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):

    response = JSONResponse(status_code=exc.status_code,
                            content={"detail": exc.detail}, headers=exc.headers)

    # if a special header 'X-Auth-Logout' is set, the user should be logged out, so remove their cookie
    if exc.headers and exc.headers.get(config.HEADER_KEYS['auth_logout']) is not None:
        auth_utils.delete_access_token_cookie(response)
    return response


app.include_router(auth.AuthRouter().router)
app.include_router(user.UserRouter().router)
app.include_router(gallery.GalleryRouter().router)
app.include_router(user_access_token.UserAccessTokenRouter().router)
app.include_router(api_key.ApiKeyRouter().router)
app.include_router(api_key_scope.ApiKeyScopeRouter().router)
app.include_router(pages.PagesRouter().router)

app.include_router(user.UserAdminRouter().router)
app.include_router(gallery.GalleryAdminRouter().router)
app.include_router(user_access_token.UserAccessTokenAdminRouter().router)
app.include_router(api_key.ApiKeyAdminRouter().router)
app.include_router(api_key_scope.ApiKeyScopeAdminRouter().router)
