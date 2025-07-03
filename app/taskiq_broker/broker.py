import logging

from taskiq_nats import PullBasedJetStreamBroker, NATSKeyValueScheduleSource
from taskiq.schedule_sources import LabelScheduleSource
from taskiq import TaskiqEvents, TaskiqState, TaskiqScheduler

from app.config_data.config import load_config, Config


config: Config = load_config()

broker = PullBasedJetStreamBroker(servers=config.nats.servers, queue="taskiq_queue")
nats_source = NATSKeyValueScheduleSource(config.nats.servers)
scheduler = TaskiqScheduler(
    broker=broker, sources=[LabelScheduleSource(broker), nats_source]
)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] #%(levelname)-8s %(filename)s:"
        "%(lineno)d - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting scheduler...")

    state.logger = logger


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    state.logger.info("Scheduler stopped")
