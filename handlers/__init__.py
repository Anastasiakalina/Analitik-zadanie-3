from aiogram import Router

from . import common, file_handler, context_handler


def get_routers() -> Router:
    main_router = Router()
    main_router.include_router(common.router)
    main_router.include_router(file_handler.router)
    main_router.include_router(context_handler.router)
    return main_router