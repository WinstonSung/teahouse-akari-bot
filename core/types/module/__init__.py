from typing import Callable, Union, Dict, List

from apscheduler.triggers.combining import AndTrigger, OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .component_matches import *


def convert2lst(elements: Union[str, list, tuple]) -> list:
    if isinstance(elements, str):
        return [elements]
    elif isinstance(elements, tuple):
        return list(elements)
    return elements


class Module:
    def __init__(self,
                 bind_prefix: str,
                 alias: Union[str, list, tuple, dict] = None,
                 desc: str = None,
                 recommend_modules: Union[str, list, tuple] = None,
                 developers: Union[str, list, tuple] = None,
                 required_admin: bool = False,
                 base: bool = False,
                 required_superuser: bool = False,
                 available_for: Union[str, list, tuple] = '*',
                 exclude_from: Union[str, list, tuple] = '',
                 support_languages: Union[str, list, tuple] = None):
        self.bind_prefix: str = bind_prefix
        if isinstance(alias, str):
            alias = {alias: bind_prefix}
        elif isinstance(alias, (tuple, list)):
            alias = {x: bind_prefix for x in alias}
        self.alias: Dict[str, str] = alias
        self.desc: str = desc
        self.recommend_modules: List[str] = convert2lst(recommend_modules)
        self.developers: List[str] = convert2lst(developers)
        self.required_admin: bool = required_admin
        self.base: bool = base
        self.required_superuser: bool = required_superuser
        self.available_for: List[str] = convert2lst(available_for)
        self.exclude_from: List[str] = convert2lst(exclude_from)
        self.support_languages: List[str] = convert2lst(support_languages)
        self.command_list = CommandMatches()
        self.regex_list = RegexMatches()
        self.schedule_list = ScheduleMatches()


__all__ = ["Module", "AndTrigger", "OrTrigger", "DateTrigger",
           "CronTrigger", "IntervalTrigger"]
