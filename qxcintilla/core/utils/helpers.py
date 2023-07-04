from typing import Any, Tuple, Type
from typing_extensions import Self
import weakref
from qtpy.QtCore import QTimer


class DelayJobRunner:
    """
    Utility class for running job after a certain delay. If a new request is
    made during this delay, the previous request is dropped and the timer is
    restarted for the new request.
    We use this to implement a cooldown effect that prevents jobs from being
    executed while the IDE is not idle.
    A job is a simple callable.
    """

    def __init__(self, delay=500):
        """
        :param delay: Delay to wait before running the job. This delay applies
        to all requests and cannot be changed afterwards.
        """
        self._timer = QTimer()
        self.delay = delay
        self._timer.timeout.connect(self._exec_requested_job)
        self._args = []
        self._kwargs = {}
        self._job = lambda x: None

    def request_job(self, job, *args, **kwargs):
        """
        Request a job execution. The job will be executed after the delay
        specified in the DelayJobRunner contructor elapsed if no other job is
        requested until then.
        :param job: job.
        :type job: callable
        :param args: job's position arguments
        :param kwargs: job's keyworded arguments
        """
        self.cancel_requests()
        self._job = job
        self._args = args
        self._kwargs = kwargs
        self._timer.start(self.delay)

    def cancel_requests(self):
        """
        Cancels pending requests.
        """
        self._timer.stop()
        self._job = None
        self._args = None
        self._kwargs = None

    def _exec_requested_job(self):
        """
        Execute the requested job after the timer has timeout.
        """
        self._timer.stop()
        self._job(*self._args, **self._kwargs)


__all__ = ["DelayJobRunner"]