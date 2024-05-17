from typing import Type

from app.constants import Job
from app.jobs.base import BaseJob
from app.jobs.price_event import PriceEventJob
from app.jobs.price_publish import PublishingPriceJob

JOB_CLASS_MAP: dict[Job, Type[BaseJob]] = {
    Job.EVENT_PROCESSING: PriceEventJob,
    Job.PRICE_PUBLISH: PublishingPriceJob,
}
