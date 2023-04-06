import os
from collections.abc import MutableMapping
from string import Template
from typing import TypedDict

import ujson as json

from .text import remove_suffix

from config import Config


# Load all locale files into memory

# We might change this behavior in the future and read them on demand as
# locale files get too large
locale_cache = {}


# From https://stackoverflow.com/a/6027615
def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def load_locale_file():
    locales_path = os.path.abspath('./locales')
    locales = os.listdir(locales_path)
    for l in locales:
        with open(f'{locales_path}/{l}', 'r', encoding='utf-8') as f:
            locale_cache[remove_suffix(l, '.json')] = flatten(json.load(f))
    modules_path = os.path.abspath('./modules')
    for m in os.listdir(modules_path):
        if os.path.isdir(f'{modules_path}/{m}'):
            if os.path.exists(f'{modules_path}/{m}/locales'):
                locales_m = os.listdir(f'{modules_path}/{m}/locales')
                for lm in locales_m:
                    with open(f'{modules_path}/{m}/locales/{lm}', 'r', encoding='utf-8') as f:
                        if remove_suffix(lm, '.json') in locale_cache:
                            locale_cache[remove_suffix(lm, '.json')].update(flatten(json.load(f)))
                        else:
                            locale_cache[remove_suffix(lm, '.json')] = flatten(json.load(f))


load_locale_file()


class LocaleFile(TypedDict):
    key: str
    string: str


class Locale:
    def __init__(self, locale: str, fallback_lng=None):
        """Language code deprecation"""
        deprecated_lngs = {
            'en_us': 'en',
            'zh_cn': 'zh-hans',
            'zh_tw': 'zh-hant',
        }
        locale = deprecated_lngs[locale] or locale

        """创建一个本地化对象"""

        if fallback_lng is None:
            fallback_lng = ['zh-hans', 'zh-hant', 'en']
        self.locale = locale
        self.data: LocaleFile = locale_cache[locale]
        self.fallback_lng = fallback_lng

    def __getitem__(self, key: str):
        return self.data[key]

    def __contains__(self, key: str):
        return key in self.data

    def t(self, key: str, fallback_failed_prompt=True, *args, **kwargs) -> str:
        '''获取本地化字符串'''
        localized = self.get_string_with_fallback(key, fallback_failed_prompt)
        return Template(localized).safe_substitute(*args, **kwargs)

    def get_string_with_fallback(self, key: str, fallback_failed_prompt) -> str:
        value = self.data.get(key, None)
        if value is not None:
            return value  # 1. 如果本地化字符串存在，直接返回
        fallback_lng = list(self.fallback_lng)
        fallback_lng.insert(0, self.locale)
        for lng in fallback_lng:
            if lng in locale_cache:
                string = locale_cache[lng].get(key, None)
                if string is not None:
                    return string  # 2. 如果在 fallback 语言中本地化字符串存在，直接返回
        if fallback_failed_prompt:
            return f'{{{key}}}' + self.t("i18n.prompt.fallback.failed", url=Config('bug_report_url'))
        else:
            return key
        # 3. 如果在 fallback 语言中本地化字符串不存在，返回 key

def get_available_locales():
    return list(locale_cache.keys())


__all__ = ['Locale', 'load_locale_file', 'get_available_locales']
