# pyrefly: ignore [missing-import]
from aiogram import Router
from .start import router as start_router
from .registration import router as reg_router
from .quiz import router as quiz_router
from .menu import router as menu_router
from .help import router as help_router
from .fallback import router as fallback_router

def get_handlers_router() -> Router:
    main_router = Router()
    # Order matters: fallback must be last
    main_router.include_routers(
        start_router,
        reg_router,
        quiz_router,
        menu_router,
        help_router,
        fallback_router
    )
    return main_router
