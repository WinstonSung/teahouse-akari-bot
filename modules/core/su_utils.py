import asyncio
import os
import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import ujson as json

from config import Config
from core.builtins import Bot, PrivateAssets, Image, Plain, ExecutionLockList, Temp, MessageTaskManager
from core.component import module
from core.loader import ModulesManager
from core.parser.message import remove_temp_ban
from core.tos import pardon_user, warn_user
from core.utils.cache import random_cache_path
from database import BotDBUtil

su = module('superuser', alias=['su'], developers=['OasisAkari', 'Dianliang233'], required_superuser=True)


@su.handle('add <user>')
async def add_su(message: Bot.MessageSession):
    user = message.parsed_msg['<user>']
    if not user.startswith(f'{message.target.senderFrom}|'):
        await message.finish(message.locale.t("core.superuser.message.invalid", prefix=message.prefixes[0]))
    if user:
        if BotDBUtil.SenderInfo(user).edit('isSuperUser', True):
            await message.finish(message.locale.t("core.superuser.message.add.success", user=user))


@su.handle('del <user>')
async def del_su(message: Bot.MessageSession):
    user = message.parsed_msg['<user>']
    if not user.startswith(f'{message.target.senderFrom}|'):
        await message.finish(message.locale.t("core.superuser.message.invalid", prefix=message.prefixes[0]))
    if user:
        if BotDBUtil.SenderInfo(user).edit('isSuperUser', False):
            await message.finish(message.locale.t("core.superuser.message.remove.success", user=user))


ana = module('analytics', required_superuser=True)


@ana.handle()
async def _(msg: Bot.MessageSession):
    if Config('enable_analytics'):
        first_record = BotDBUtil.Analytics.get_first()
        get_counts = BotDBUtil.Analytics.get_count()
        await msg.finish(msg.locale.t("core.analytics.message.counts", first_record=first_record.timestamp,
                         counts=get_counts))
    else:
        await msg.finish(msg.locale.t("core.analytics.message.disabled"))


@ana.handle('days [<name>]')
async def _(msg: Bot.MessageSession):
    if Config('enable_analytics'):
        first_record = BotDBUtil.Analytics.get_first()
        module_ = None
        if '<name>' in msg.parsed_msg:
            module_ = msg.parsed_msg['<name>']
        data_ = {}
        for d in range(30):
            new = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1) - timedelta(days=30 - d - 1)
            old = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1) - timedelta(days=30 - d)
            get_ = BotDBUtil.Analytics.get_count_by_times(new, old, module_)
            data_[old.day] = get_
        data_x = []
        data_y = []
        for x in data_:
            data_x.append(str(x))
            data_y.append(data_[x])
        plt.plot(data_x, data_y, "-o")
        plt.plot(data_x[-1], data_y[-1], "-ro")
        plt.xlabel('Days')
        plt.ylabel('Counts')
        plt.tick_params(axis='x', labelrotation=45, which='major', labelsize=10)

        plt.gca().yaxis.get_major_locator().set_params(integer=True)
        for xitem, yitem in np.nditer([data_x, data_y]):
            plt.annotate(yitem, (xitem, yitem), textcoords="offset points", xytext=(0, 10), ha="center")
        path = random_cache_path() + '.png'
        plt.savefig(path)
        plt.close()
        await msg.finish(
            [Plain(
                msg.locale.t("core.analytics.message.days", module=module_ if module_ is not None else "",
                             first_record=first_record.timestamp)),
                Image(path)])


set_ = module('set', required_superuser=True)


@set_.handle('modules <targetId> <modules> ...')
async def _(msg: Bot.MessageSession):
    target = msg.parsed_msg['<targetId>']
    if not target.startswith(f'{msg.target.targetFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    target_data = BotDBUtil.TargetInfo(target)
    if target_data.query is None:
        wait_confirm = await msg.waitConfirm(msg.locale.t("core.set.message.confirm.init"))
        if not wait_confirm:
            return
    modules = [m for m in [msg.parsed_msg['<modules>']] + msg.parsed_msg.get('...', [])
               if m in ModulesManager.return_modules_list_as_dict(msg.target.targetFrom)]
    target_data.enable(modules)
    await msg.finish(msg.locale.t("core.set.message.module.success") + ", ".join(modules))


@set_.handle('option <targetId> <k> <v>')
async def _(msg: Bot.MessageSession):
    target = msg.parsed_msg['<targetId>']
    k = msg.parsed_msg['<k>']
    v = msg.parsed_msg['<v>']
    if not target.startswith(f'{msg.target.targetFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    target_data = BotDBUtil.TargetInfo(target)
    if target_data.query is None:
        wait_confirm = await msg.waitConfirm(msg.locale.t("core.set.message.confirm.init"))
        if not wait_confirm:
            return
    if v.startswith(('[', '{')):
        v = json.loads(v)
    elif v.upper() == 'TRUE':
        v = True
    elif v.upper() == 'FALSE':
        v = False
    target_data.edit_option(k, v)
    await msg.finish(msg.locale.t("core.set.message.option.success", k=k, v=v))


ae = module('abuse', alias=['ae'], developers=['Dianliang233'], required_superuser=True)


@ae.handle('check <user>')
async def _(msg: Bot.MessageSession):
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    warns = BotDBUtil.SenderInfo(user).query.warns
    await msg.finish(msg.locale.t("core.abuse.message.check.warns", user=user, warns=warns))


@ae.handle('warn <user> [<count>]')
async def _(msg: Bot.MessageSession):
    count = int(msg.parsed_msg.get('<count>', 1))
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    warn_count = await warn_user(user, count)
    await msg.finish(msg.locale.t("core.abuse.message.warn.success", user=user, counts=count, warn_counts=warn_count))


@ae.handle('revoke <user> [<count>]')
async def _(msg: Bot.MessageSession):
    count = 0 - int(msg.parsed_msg.get('<count>', 1))
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    warn_count = await warn_user(user, count)
    await msg.finish(msg.locale.t("core.abuse.message.revoke.success", user=user, counts=count, warn_counts=warn_count))


@ae.handle('clear <user>')
async def _(msg: Bot.MessageSession):
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    await pardon_user(user)
    await msg.finish(msg.locale.t("core.abuse.message.clear.success", user=user))


@ae.handle('untempban <user>')
async def _(msg: Bot.MessageSession):
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    await remove_temp_ban(user)
    await msg.finish(msg.locale.t("core.abuse.message.untempban.success", user=user))


@ae.handle('ban <user>')
async def _(msg: Bot.MessageSession):
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    if BotDBUtil.SenderInfo(user).edit('isInBlockList', True):
        await msg.finish(msg.locale.t("core.abuse.message.ban.success", user=user))


@ae.handle('unban <user>')
async def _(msg: Bot.MessageSession):
    user = msg.parsed_msg['<user>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t("core.set.message.invalid"))
    if BotDBUtil.SenderInfo(user).edit('isInBlockList', False):
        await msg.finish(msg.locale.t("core.abuse.message.unban.success", user=user))


rst = module('restart', developers=['OasisAkari'], required_superuser=True)


def restart():
    sys.exit(233)


def write_version_cache(msg: Bot.MessageSession):
    update = os.path.abspath(PrivateAssets.path + '/cache_restart_author')
    write_version = open(update, 'w')
    write_version.write(json.dumps({'From': msg.target.targetFrom, 'ID': msg.target.targetId}))
    write_version.close()


restart_time = []


async def wait_for_restart(msg: Bot.MessageSession):
    get = ExecutionLockList.get()
    if datetime.now().timestamp() - restart_time[0] < 60:
        if len(get) != 0:
            await msg.sendMessage(msg.locale.t("core.restart.message.wait", count=len(get)))
            await asyncio.sleep(10)
            return await wait_for_restart(msg)
        else:
            await msg.sendMessage(msg.locale.t("core.restart.message.restarting"))
            get_wait_list = MessageTaskManager.get()
            for x in get_wait_list:
                for y in get_wait_list[x]:
                    if get_wait_list[x][y]['active']:
                        await get_wait_list[x][y]['original_session'].sendMessage(get_wait_list[x][y]['original_session'].locale.t("core.restart.message.prompt"))

    else:
        await msg.sendMessage(msg.locale.t("core.restart.message.timeout"))


@rst.handle()
async def restart_bot(msg: Bot.MessageSession):
    await msg.sendMessage(msg.locale.t("core.confirm"))
    confirm = await msg.waitConfirm()
    if confirm:
        restart_time.append(datetime.now().timestamp())
        await wait_for_restart(msg)
        write_version_cache(msg)
        restart()


upd = module('update', developers=['OasisAkari'], required_superuser=True)


def pull_repo():
    return os.popen('git pull', 'r').read()[:-1]


def update_dependencies():
    poetry_install = os.popen('poetry install').read()[:-1]
    if poetry_install != '':
        return poetry_install
    pip_install = os.popen('pip install -r requirements.txt').read()[:-1]
    if len(pip_install) > 500:
        return '...' + pip_install[-500:]
    return


@upd.handle()
async def update_bot(msg: Bot.MessageSession):
    await msg.sendMessage(msg.locale.t("core.confirm"))
    confirm = await msg.waitConfirm()
    if confirm:
        await msg.sendMessage(pull_repo())
        await msg.sendMessage(update_dependencies())


upds = module('update&restart', developers=['OasisAkari'], required_superuser=True, alias={'u&r': 'update&restart'})


@upds.handle()
async def update_and_restart_bot(msg: Bot.MessageSession):
    await msg.sendMessage(msg.locale.t("core.confirm"))
    confirm = await msg.waitConfirm()
    if confirm:
        restart_time.append(datetime.now().timestamp())
        await wait_for_restart(msg)
        write_version_cache(msg)
        await msg.sendMessage(pull_repo())
        await msg.sendMessage(update_dependencies())
        restart()


if Bot.FetchTarget.name == 'QQ':
    resume = module('resume', developers=['OasisAkari'], required_superuser=True)


    @resume.handle()
    async def resume_sending_group_message(msg: Bot.MessageSession):
        Temp.data['is_group_message_blocked'] = False
        if targets := Temp.data['waiting_for_send_group_message']:
            await msg.sendMessage(msg.locale.t("core.resume.message.processing", counts=len(targets)))
            for x in targets:
                await x['fetch'].sendDirectMessage(x['message'])
                Temp.data['waiting_for_send_group_message'].remove(x)
            await msg.sendMessage(msg.locale.t("core.resume.message.done"))
        else:
            await msg.sendMessage(msg.locale.t("core.resume.message.nothing"))

    @resume.handle('continue')
    async def resume_sending_group_message(msg: Bot.MessageSession):
        del Temp.data['waiting_for_send_group_message'][0]
        Temp.data['is_group_message_blocked'] = False
        if targets := Temp.data['waiting_for_send_group_message']:
            await msg.sendMessage(msg.locale.t("core.resume.message.skip", counts=len(targets)))
            for x in targets:
                await x['fetch'].sendDirectMessage(x['message'])
                Temp.data['waiting_for_send_group_message'].remove(x)
            await msg.sendMessage(msg.locale.t("core.resume.message.done"))
        else:
            await msg.sendMessage(msg.locale.t("core.resume.message.nothing"))

echo = module('echo', developers=['OasisAkari'], required_superuser=True)


@echo.handle('<display_msg>')
async def _(msg: Bot.MessageSession):
    await msg.finish(msg.parsed_msg['<display_msg>'])


say = module('say', developers=['OasisAkari'], required_superuser=True)


@say.handle('<display_msg>')
async def _(msg: Bot.MessageSession):
    await msg.finish(msg.parsed_msg['<display_msg>'], quote=False)


if Config('enable_eval'):
    _eval = module('eval', developers=['Dianliang233'], required_superuser=True)


    @_eval.handle('<display_msg>')
    async def _(msg: Bot.MessageSession):
        await msg.finish(str(eval(msg.parsed_msg['<display_msg>'], {'msg': msg})))
