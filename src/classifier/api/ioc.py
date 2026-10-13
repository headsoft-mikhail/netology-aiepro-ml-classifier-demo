import sqlite3
import typing

from modern_di import Group, Scope, providers

from classifier.api.repositories.analysis_repository import AnalysisRepository
from classifier.api.repositories.cache_repository import AppCache
from classifier.api.repositories.predictions_repository import PredictionsRepository
from classifier.api.resources.database_resource import create_database_connection
from classifier.api.settings import ServiceSettings
from classifier.api.use_cases.submit_demo_record_use_case import SubmitDemoRecordUseCase


class Resources(Group):
    service_settings: typing.Final = providers.ContextProvider(scope=Scope.APP, context_type=ServiceSettings)
    database_connection: typing.Final = providers.Factory(
        creator=create_database_connection,
        scope=Scope.REQUEST,
        cache=providers.CacheSettings(finalizer=sqlite3.Connection.close),
    )


class Repositories(Group):
    app_cache: typing.Final = providers.Factory(creator=AppCache, scope=Scope.APP, cache=True)
    analysis_repository: typing.Final = providers.Factory(creator=AnalysisRepository, scope=Scope.REQUEST, cache=True)
    predictions_repository: typing.Final = providers.Factory(creator=PredictionsRepository, scope=Scope.APP, cache=True)


class UseCases(Group):
    submit_demo_record: typing.Final = providers.Factory(creator=SubmitDemoRecordUseCase, scope=Scope.REQUEST)


ALL_GROUPS: typing.Final[list[type[Group]]] = [Resources, Repositories, UseCases]
