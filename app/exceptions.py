class PriceServiceError(Exception):
    pass


class EntityNotFoundError(PriceServiceError):
    pass


class ParserError(PriceServiceError):
    pass


class WorkerError(PriceServiceError):
    pass


class WorkerFailedParseMsgError(WorkerError):
    pass
