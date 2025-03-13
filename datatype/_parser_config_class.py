import json
import logging
import re
import zipfile
from dataclasses import dataclass
from io import TextIOWrapper
from re import Pattern
from typing import Optional, Any

from datatype._classes import DataType, PropertyResult
from datatype._utils import get_datatype
from datatype._classes import ParseResult


class ParserConfig:
    """
    Класс конфигурации парсера.

    Структура файла:

    - metadata.json
    - common.json
    - 1.json
    - ...
    - n.json


    :var title: Название парсера.
    :var description: Описание парсера.
    :var author: Автор парсера.
    :var version: Версия парсера.
    :var accepted_sources: Список допустимых источников.

    :var property_groups: Список групп свойств.
    """

    title: str
    description: Optional[str]
    author: str
    version: str
    accepted_sources: list[str]

    property_groups: list["PropertyGroup"]
    common_properties: list["Property"]

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
            self,
            title: str,
            description: str,
            author: str,
            version: str,
            accepted_sources: list[str],
            property_groups: list["PropertyGroup"],
            common_properties: list["Property"],
            logger: Optional[logging.Logger] = None
    ):
        if logger is not None:
            self._logger = logger
        self.title = title
        self.description = description
        self.author = author
        self.version = version
        self.accepted_sources = accepted_sources
        self.property_groups = property_groups
        self.common_properties = common_properties

        self._logger.debug("Конфигурация парсера создана.")

    @classmethod
    def load(cls, file_path: str, logger: Optional[logging.Logger] = logging.getLogger(__name__)) -> "ParserConfig":
        """
        Загружает конфигурацию парсера из файла.

        :param file_path: Путь к файлу.
        :param logger: Объект логгера.
        :return: Инициализированный экземпляр класса ParserConfig
        """

        _common_prop: list["Property"] = list()
        _property_groups: list["PropertyGroup"] = list()

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            _filelist = zip_ref.namelist()

            if 'metadata.json' not in _filelist:
                logger.error('Файл metadata.json в конфигурации %s не найден', file_path)
                raise Exception('metadata.json not found')

            with zip_ref.open('metadata.json') as file:
                with TextIOWrapper(file, encoding='utf-8') as text_file:
                    metadata = json.load(text_file)
            _filelist.remove('metadata.json')

            if 'common.json' in _filelist:
                with zip_ref.open('common.json') as file:
                    with TextIOWrapper(file, encoding='utf-8') as text_file:
                        _common_prop = [Property.from_config(prop, common=True) for prop in json.load(text_file)]
                _filelist.remove('common.json')

            for json_file in _filelist:
                with zip_ref.open(json_file) as file:
                    with TextIOWrapper(file, encoding='utf-8') as text_file:
                        _property_groups.append(PropertyGroup.from_config(json.load(text_file)))
                        _property_groups[-1].properties.extend(_common_prop)

        return cls(
            title=metadata.get('title', '-'),
            description=metadata.get('description', None),
            author=metadata.get('author', '-'),
            version=metadata.get('version', '-'),
            accepted_sources=metadata.get('accepted_sources', []),
            property_groups=_property_groups,
            common_properties=_common_prop,
            logger=logger
        )

    # def add_prop_from_config(self, config: dict) -> "ParserConfig":
    #     self.property_groups.append(PropertyGroup.from_config(config))
    #     return self

    def to_config(self) -> dict:
        return {
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'accepted_sources': self.accepted_sources,
            'property_groups': [group.dict for group in self.property_groups],
            'common_properties': [prop.dict for prop in self.common_properties]
        }

    @property
    def dict(self) -> dict:
        return self.to_config()

    def save(self, file_path: str) -> "ParserConfig":
        """
        Сохраняет конфигурацию группы свойств в файл.

        :param file_path: Путь к файлу для сохранения.
        :return: Ссылка на текущий экземпляр WebPageParser.
        """
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=9) as zip_ref:
            with zip_ref.open('metadata.json', 'w') as file:
                with TextIOWrapper(file, encoding='utf-8') as text_file:
                    json.dump(self.to_config(), text_file, indent=4, ensure_ascii=False)

            if self.common_properties:
                with zip_ref.open('common.json', 'w') as file:
                    with TextIOWrapper(file, encoding='utf-8') as text_file:
                        json.dump([prop.dict for prop in self.common_properties],
                                  text_file, indent=4, ensure_ascii=False)

            for group in self.property_groups:
                with zip_ref.open(f'{group.name}.json', 'w') as file:
                    with TextIOWrapper(file, encoding='utf-8') as text_file:
                        json.dump(group.to_config(exclude_common=True), text_file, indent=4, ensure_ascii=False)

        self._logger.debug("Конфигурация сохранена в файл: %s", file_path)
        return self


@dataclass
class Property:
    """Класс, представляющий отдельное свойство для парсинга."""
    name: str
    type: DataType
    signatures: list[Pattern]
    common: bool = False
    _logger: logging.Logger = logging.getLogger(__name__)

    def match(self, text: str) -> Optional[Any]:
        """
        Ищет значение свойства в тексте с использованием сигнатур.

        :param text: Текст для поиска.
        :return: Найденное значение с приведением к указанному типу или None.
        """
        for pattern in self.signatures:
            match = pattern.search(text)
            if match:
                value = match.group(1)
                self._logger.debug("Найдено совпадение для свойства '%s': %s", self.name, value)
                return self._convert_type(value)
        self._logger.debug("Совпадение для свойства '%s' не найдено.", self.name)
        return None

    def _convert_type(self, value: str):
        """
        Преобразует строковое значение в указанный тип.

        :param value: Строковое значение.
        :return: Значение нужного типа.
        """
        if self.type is None:
            return value

        if value is None:
            return None

        try:
            return self.type(value)
        except (ValueError, TypeError) as e:
            self._logger.error("Ошибка преобразования значения '%s' к типу '%s': %s", value, self.type, e)
            return None

    @classmethod
    def from_config(cls, config: dict, common: bool = False) -> 'Property':
        return cls(
            name=config.get('name', ''),
            type=get_datatype(config.get('type', "string")),
            signatures=[re.compile(sig) for sig in config.get('signatures', [])],
            common=common or config.get('common', False)
        )

    @property
    def dict(self) -> dict:
        res = {
            'name': self.name,
            'type': self.type.title,
            'signatures': [sig.pattern for sig in self.signatures]
        }

        if self.common:
            res['common'] = True

        return res


@dataclass
class PropertyGroup:
    """Класс, представляющий группу свойств для парсинга."""
    name: str
    properties: list[Property]

    @classmethod
    def from_config(cls, config: dict) -> 'PropertyGroup':
        """
        Создает экземпляр PropertyGroup из конфигурационного словаря.

        :param config: Словарь конфигурации.
        :return: Экземпляр PropertyGroup.
        """

        properties = [
            Property.from_config(prop) for prop in config.get('properties', [])
        ]
        return cls(name=config.get('name', ''), properties=properties)

    def to_config(self, exclude_common: bool = False) -> dict:
        """
        Преобразует текущую конфигурацию группы свойств в словарь.

        :return: Словарь конфигурации.
        """
        return {
            'name': self.name,
            'properties': [
                prop.dict for prop in self.properties if not (exclude_common and prop.common)
            ]
        }

    @property
    def dict(self) -> dict:
        return self.to_config()

    def pars(self, html: str, source: str) -> "ParseResult":
        _properties = []
        for prop in self.properties:
            _properties.append(PropertyResult(name=prop.name, value=prop.match(html), type=prop.type))

        return ParseResult(
            name=self.name,
            properties=_properties,
            source=source
        )


if __name__ == '__main__':
    def main():
        from pprint import pprint
        config = ParserConfig.load('../UI/cfg.zip')
        pprint(config.dict)
        config.save('cfg2.zip')


    main()
