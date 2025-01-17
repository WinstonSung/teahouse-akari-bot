import json
import re

from google_play_scraper import app as google_play_scraper

from core.builtins import ErrorMessage
from core.logger import Logger
from core.utils.http import get_url, post_url
from core.utils.ip import IP


async def mcv(msg):
    try:
        data = json.loads(await get_url('https://piston-meta.mojang.com/mc/game/version_manifest.json', 200))
        message1 = msg.locale.t("mcv.mcv.message.message1", release=data['latest']['release'], snapshot=data['latest']['snapshot'])
    except (ConnectionError, OSError):  # Probably...
        message1 = msg.locale.t("mcv.mcv.message.message1.failed")
    try:
        mojira = json.loads(await get_url('https://bugs.mojang.com/rest/api/2/project/10400/versions', 200))
        release = []
        prefix = ' | '
        for v in mojira:
            if not v['archived']:
                release.append(v['name'])
        message2 = prefix.join(release)
    except Exception:
        message2 = msg.locale.t("mcv.mcv.message.message2.failed")
    return msg.locale.t("mcv.mcv.message", message1=message1, message2=message2)


async def mcbv(msg):
    play_store_version = None
    if IP.country != 'China':
        try:  # play store
            play_store_version = google_play_scraper('com.mojang.minecraftpe')['version']
        except Exception:
            pass
    ms_store_version = None
    try:
        fetch_ = await post_url('https://store.rg-adguard.net/api/GetFiles',
                                status_code=200,
                                fmt='text',
                                data={'type': 'url', 'url': 'https://www.microsoft.com/store/productId/9NBLGGH2JHXJ',
                                      'ring': 'RP', 'lang': 'zh-CN'})
        if fetch_:
            ms_store_version = re.findall(r'.*Microsoft.MinecraftUWP_(.*?)_.*', fetch_, re.M | re.I)[0]
    except Exception:
        pass
    try:
        data = json.loads(await get_url('https://bugs.mojang.com/rest/api/2/project/10200/versions', 200))
    except (ConnectionError, OSError):  # Probably...
        return ErrorMessage(msg.locale.t('mcv.error.server'))
    beta = []
    preview = []
    release = []
    for v in data:
        if not v['archived']:
            if re.match(r".*Beta$", v["name"]):
                beta.append(v["name"])
            elif re.match(r".*Preview$", v["name"]):
                preview.append(v["name"])
            else:
                if v["name"] != "Future Release":
                    release.append(v["name"])
    fix = " | "
    msg2 = f'Beta: {fix.join(beta)}\nPreview: {fix.join(preview)}\nRelease: {fix.join(release)}'
    return \
(f"""{msg.locale.t("mcv.mcbv.message.play_store")}
{play_store_version if play_store_version is not None else msg.locale.t('mcv.mcbv.message.failed')}，
""" if IP.country != 'China' else '') + \
f"""{msg.locale.t("mcv.mcbv.message.ms_store")}
{ms_store_version if ms_store_version is not None else msg.locale.t('mcv.mcbv.message.failed')}，
""" +\
msg.locale.t("mcv.mcbv.message", msg2=msg2)


async def mcdv(msg):
    try:
        data = json.loads(await get_url('https://bugs.mojang.com/rest/api/2/project/11901/versions', 200))
    except (ConnectionError, OSError):  # Probably...
        return ErrorMessage(msg.locale.t('mcv.error.server'))
    release = []
    for v in data:
        if not v['archived']:
            release.append(v["name"])
    return msg.locale.t('mcv.mcdv.message', mcdversion=" | ".join(release))


async def mcev(msg):
    try:
        data = await get_url('https://meedownloads.blob.core.windows.net/win32/x86/updates/Updates.txt', 200)
        Logger.debug(data)
        version = re.search(r'(?<=\[)(.*?)(?=])', data)[0]
        Logger.debug(version)
    except (ConnectionError, OSError):  # Probably...
        return ErrorMessage(msg.locale.t('mcv.error.server'))
    return f'{msg.locale.t("mcv.mcev.message")}{version}'
