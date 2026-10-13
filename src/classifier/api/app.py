import sqlite3
import typing
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import fastapi
import modern_di
import modern_di_fastapi
from fastapi.staticfiles import StaticFiles

from classifier.api import ioc, settings
from classifier.api.repositories.cache_repository import AppCache
from classifier.api.resources.database_resource import create_analysis_table
from classifier.api.resources.demo_cases import load_demo_cases
from classifier.api.resources.models_resource import load_models
from classifier.api.routes import ROUTER_OBJ
from classifier.api.settings import ServiceSettings


class AppBuilder:
    def __init__(self, service_settings: ServiceSettings | None = None) -> None:
        self.app: typing.Final = fastapi.FastAPI(
            title="CTG Classifier API",
            version="0.1.0",
            lifespan=self.lifespan_manager,
        )
        self.app.include_router(ROUTER_OBJ)
        self.app.mount("/", StaticFiles(directory=settings.api_settings.frontend_dir, html=True), name="frontend")
        di_container: typing.Final = modern_di.Container(
            groups=ioc.ALL_GROUPS,
            context={ServiceSettings: service_settings or settings.service_settings},
        )
        modern_di_fastapi.setup_di(self.app, di_container)
        di_container.validate()

    @asynccontextmanager
    async def lifespan_manager(self, app: fastapi.FastAPI) -> AsyncGenerator[None]:
        di_container: typing.Final = modern_di_fastapi.fetch_di_container(app)
        di_container.open()
        service_settings: typing.Final = di_container.resolve(ServiceSettings)
        app_cache: typing.Final = di_container.resolve(AppCache)
        app_cache.classifiers = load_models(service_settings)
        app_cache.demo_cases = load_demo_cases(service_settings.demo_cases_path)
        service_settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        with di_container.build_child_container(scope=modern_di.Scope.REQUEST) as startup_container:
            create_analysis_table(startup_container.resolve(sqlite3.Connection))
        yield


app: typing.Final = AppBuilder().app
