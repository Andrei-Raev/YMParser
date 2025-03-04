from typing import Callable, Any


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
        return self.title

    def decode(self, x: str) -> Any:
        return self.decoder(x)

    def encode(self, x: Any) -> str:
        return self.to_excel(x)

    def __call__(self, *args, **kwargs) -> Any:
        return self.decoder(*args, **kwargs)


def _EMPYT_ENCODER(x: Any) -> Any:
    return x


INT = DataType('int', int, _EMPYT_ENCODER)
FLOAT = DataType('float', float, _EMPYT_ENCODER)
STR = DataType('str', str, _EMPYT_ENCODER)
