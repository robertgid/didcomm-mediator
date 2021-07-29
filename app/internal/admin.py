import json

from databases import Database
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse

import app.db.crud as crud
from app.settings import templates, WEBROOT as SETTING_WEBROOT, URL_STATIC, \
    CERT_FILE as SETTING_CERT_FILE, CERT_KEY_FILE as SETTING_CERT_KEY_FILE
from app.dependencies import get_db
from app.core.global_config import GlobalConfig
from app.core.singletons import GlobalMemcachedClient

from .auth import auth_user as _auth_user, login as _login, logout as _logout


router = APIRouter()


BASE_URL = '/admin'


async def check_is_logged(request: Request):
    current_user = await _auth_user(request)
    if current_user is None:
        raise HTTPException(status_code=401, detail=f'Unauthorized')


@router.get("/")
async def admin_panel(request: Request, db: Database = Depends(get_db)):
    cfg = GlobalConfig(db, GlobalMemcachedClient.get())
    current_user = await _auth_user(request)
    if current_user is None:
        superuser = await crud.load_superuser(db, mute_errors=True)
        if superuser:
            current_step = 0  # login form
        else:
            current_step = 1  # create superuser form
    else:
        current_step = 2  # configure Webroot & SSL

    # variables
    env = {
        'webroot': SETTING_WEBROOT,
        'cert_file': SETTING_CERT_FILE or '',
        'cert_key_file': SETTING_CERT_KEY_FILE or ''
    }
    full_base_url = str(request.base_url)
    if full_base_url.endswith('/'):
        full_base_url = full_base_url[:-1]

    ssl_option = await cfg.get_ssl_option()
    settings = {
        'webroot': await cfg.get_webroot() or full_base_url,
        'full_base_url': full_base_url,
        'ssl_option': ssl_option or 'manual'
    }
    if 'x-forwarded-proto' in request.headers:
        scheme = request.headers['x-forwarded-proto']
        if scheme == 'https':
            settings['webroot'] = settings['webroot'].replace('http://', 'https://')
            settings['full_base_url'] = settings['full_base_url'].replace('http://', 'https://')

    context = {
        'github': 'https://github.com/Sirius-social/didcomm',
        'issues': 'https://github.com/Sirius-social/didcomm/issues',
        'spec': 'https://identity.foundation/didcomm-messaging/spec/',
        'features': 'https://github.com/Sirius-social/didcomm#features',
        'download': 'https://hub.docker.com/r/socialsirius/didcomm',
        'base_url': BASE_URL,
        'current_user': current_user,
        'current_step': current_step,
        'env': env,
        'settings': settings,
        'static': {
            'styles': URL_STATIC + '/admin/css/styles.css',
            'vue': URL_STATIC + '/vue.min.js',
            'axios': URL_STATIC + '/axios.min.js',
        }
    }
    response = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            **context
        }
    )
    return response


@router.post("/login", status_code=201)
async def login(request: Request, response: Response, db: Database = Depends(get_db)):
    js = await request.json()
    username, password = js.get('username'), js.get('password')
    user = await crud.load_user(db, username, mute_errors=True)
    if user:
        success = crud.check_password(user, password)
        if success:
            await _login(response, user)
        else:
            raise HTTPException(status_code=400, detail=f'Password incorrect')
    else:
        raise HTTPException(status_code=400, detail=f'Not found user with username: "{username}"')


@router.get("/logout")
async def login(request: Request, response: Response):
    await _logout(request, response)
    return RedirectResponse(url=BASE_URL)


@router.post("/create_user", status_code=201)
async def create_user(request: Request, response: Response, db: Database = Depends(get_db)):
    js = await request.json()
    username, password1, password2 = js.get('username'), js.get('password1'), js.get('password2')
    if not username:
        raise HTTPException(status_code=400, detail='Username must be filled')
    if len(username) < 4:
        raise HTTPException(status_code=400, detail='Username length must not be less than 4 symbols')
    if len(password1) < 6:
        raise HTTPException(status_code=400, detail='Password length must not be less than 6 symbols')
    if password1 != password2:
        raise HTTPException(status_code=400, detail='Passwords are not equal')
    user = await crud.load_user(db, username, mute_errors=True)
    if user:
        raise HTTPException(status_code=400, detail=f'User with username "{username}" already exists')
    else:
        user = await crud.create_user(db, username, password1)
        await _login(response, user)


@router.get("/ping")
async def ping():
    return {'success': True}


@router.post("/set_webroot", status_code=200)
async def set_webroot(request: Request, db: Database = Depends(get_db)):
    await check_is_logged(request)
    js = await request.json()
    value = js.get('value')
    cfg = GlobalConfig(db, GlobalMemcachedClient.get())
    await cfg.set_webroot(value)


@router.post("/set_ssl_option", status_code=200)
async def set_ssl_option(request: Request, db: Database = Depends(get_db)):
    await check_is_logged(request)
    js = await request.json()
    value = js.get('value')
    cfg = GlobalConfig(db, GlobalMemcachedClient.get())
    await cfg.set_ssl_option(value)
