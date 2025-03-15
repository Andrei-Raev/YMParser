import enum


class StatusbarVariants(str, enum.Enum):
    need_config: str = 'Ожидает загрузки конфигурации'
    config_loading: str = 'Загрузка конфигурации...'
    config_loaded: str = 'Конфигурация загружена'
    config_loading_error: str = 'Ошибка загрузки конфигурации'