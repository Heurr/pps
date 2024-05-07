from typing import Type

from app.constants import Job
from app.jobs.base import BaseJob
from app.jobs.price_event import PriceEventJob

JOB_CLASS_MAP: dict[Job, Type[BaseJob]] = {Job.EVENT_PROCESSING: PriceEventJob}
