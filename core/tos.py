from config import Config
from core.builtins import MessageSession
from database import BotDBUtil


async def warn_target(msg: MessageSession, reason=None):
    current_warns = int(msg.target.senderInfo.query.warns) + 1
    msg.target.senderInfo.edit('warns', current_warns)
    warn_template = [msg.locale.t("tos.warning")]
    if reason is not None:
        warn_template.append(msg.locale.t("tos.reason") + reason)
    if current_warns < 5:
        warn_template.append(msg.locale.t('tos.warning.count', current_warns=current_warns))
    if current_warns <= 2:
        warn_template.append(msg.locale.t('tos.warning.appeal', issue_url=Config('issue_url')))
    if current_warns == 5:
        warn_template.append(msg.locale.t('tos.warning.last'))
    if current_warns > 5:
        msg.target.senderInfo.edit('isInBlockList', True)
        return
    await msg.sendMessage('\n'.join(warn_template))


async def pardon_user(user: str):
    BotDBUtil.SenderInfo(user).edit('warns', 0)


async def warn_user(user: str, count=1):
    current_warns = int(BotDBUtil.SenderInfo(user).query.warns) + count
    BotDBUtil.SenderInfo(user).edit('warns', current_warns)
    if current_warns > 5:
        BotDBUtil.SenderInfo(user).edit('isInBlockList', True)
    return current_warns
