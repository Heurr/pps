class PriceServiceError(Exception):
    pass


class EntityNotFoundError(PriceServiceError):
    pass


class ParserError(PriceServiceError):
    pass
