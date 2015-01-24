__author__ = 'wallsr'

from twisted.python import log

from ..BTProtocol import BTClientProtocol, BTServerProtocol
from .explorebase import EventExecuteExplore
from .fsm import utilities
from simple import TimeoutBase


class ExploreAndRefineBase(EventExecuteExplore):
    """
    Let's iterate and explore the model.

    """

    exp_args = None

    def __init__(self):
        EventExecuteExplore.__init__(self)
        self.USE_RAND_RESPONSES = True
        self.EXPLORE_AFTER_GOAL = True
        self.SKIP_RESPONSES = True

    def finishHandshake(self):

        if not self.exp_args or not 'model_path' in self.exp_args:
            raise Exception("Model path is empty or None")

        log.msg('Info: Using model {0}'.format(self.exp_args["model_path"]))

        model = utilities.dot_to_fsm(self.exp_args["model_path"])

        # Pick a random event from the model and set that as the destination
        dest_event = utilities.get_random_event(model)

        # if there are not event to pick it will return none
        if dest_event is not None:
            log.msg('Info: Destination {0}'.format(dest_event))

            self._dest_event_models[dest_event] = model
            self._remaining_goals = self._dest_event_models.keys()

        EventExecuteExplore.finishHandshake(self)


class ExploreAndRefine(ExploreAndRefineBase, BTClientProtocol):
    """

    """


class ExploreAndRefineSvr(ExploreAndRefineBase, BTServerProtocol):
    """

    """