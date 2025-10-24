from copy import copy
from typing import Callable, Type


class RegistryException(Exception):
    def __init__(self, entity_id) -> None:
        self.entity_id = entity_id


class EntityDoesNotExist(RegistryException):
    def __str__(self) -> str:
        return f"Entity with id '{self.entity_id}' does not exist."


class EntityAlreadyExists(RegistryException):
    def __str__(self) -> str:
        return f"Entity with id '{self.entity_id}' already exists."


class ExceptionRegistry:
    def __init__(self):
        self._entities: dict[Type[Exception], Callable] = {}

    @property
    def exceptions(self):
        return self.entities

    def exception(self, handler: Callable):
        def decorator(exception: Type[Exception]):
            self.register(exception, handler)
            return exception

        return decorator

    def handle_exceptions(self, handler: Callable[[Type[Exception], Callable], None]) -> None:
        for exception, func in self._entities.items():
            handler(exception, func)

    @property
    def entities(self) -> dict[Type[Exception], Callable]:
        return copy(self._entities)

    def register(self, id_: Type[Exception], value: Callable) -> None:
        if id_ in self._entities:
            raise EntityAlreadyExists(id_)

        self._entities[id_] = value

    def get_entity(self, id_: Type[Exception]) -> Callable:
        entity = self._entities.get(id_)
        if entity is None:
            raise EntityDoesNotExist(id_)

        return entity

    def include_register(self, register: 'ExceptionRegistry') -> None:
        for id_, entity in register.entities.items():
            self.register(id_, entity)

    def __call__(self, handler: Callable[[Type[Exception], Callable], None]) -> None:
        self.handle_exceptions(handler)
