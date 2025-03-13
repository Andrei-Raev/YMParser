from typing import Any, Callable

class DataType:
    """
    Перечисление типов данных для форматирования.

    :var title: Название типа.
    :var decoder: Функция декодирования строки в тип.
    :var to_excel: Функция кодирования типа в строку.
    """
    title: str
    decoder: Callable[[str], Any]
    to_excel: Callable[[Any], str]

    def __init__(self, title: str, decoder: Callable[[str], Any], to_excel: Callable[[Any], str]) -> None:
        self.title = title
        self.decoder = decoder
        self.to_excel = to_excel

    def __str__(self) -> str:
        return f'{self.title.upper()}'

    def decode(self, x: str) -> Any:
        return self.decoder(x)

    def encode(self, x: Any) -> str:
        return self.to_excel(x)

    def __call__(self, x: str) -> Any:
        return self.decode(x)


def _EMPYT_ENCODER(x: Any) -> Any:
    return x


INTEGER = DataType('integer', int, _EMPYT_ENCODER)
NUMBER = DataType('number', int, _EMPYT_ENCODER)
FLOAT = DataType('float', float, _EMPYT_ENCODER)
STRING = DataType('string', str, _EMPYT_ENCODER)
BOOLEAN = DataType('boolean', bool, _EMPYT_ENCODER)


def get_datatype(title: str) -> DataType:
    _all_types = globals()
    _type = list(
        filter(
            lambda x: isinstance(x[1], DataType) and x[1].title == title.lower().strip(),
            _all_types.items()
        )
    )

    return _type[0][1] if _type else None


def get_all_datatypes() -> list[DataType]:
    _all_types = globals()
    _types = list(
        filter(
            lambda x: isinstance(x[1], DataType),
            _all_types.items()
        )
    )

    return [x[1].__class__.__name__ for x in _types]


__all__ = ['DataType', 'get_datatype', *get_all_datatypes()]
if __name__ == '__main__':
    def main():
        print(get_datatype('string'))


    main()
