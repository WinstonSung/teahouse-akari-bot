from core.builtins import Bot, Url
from core.component import module
from core.logger import Logger
from .mcbbs_news import news

mcbbs_news = module(
    bind_prefix='mcbbs_news',
    alias=['mn', 'mcbbsnews'],
    developers=['Dianliang233']
)


@mcbbs_news.handle('{{mcbbs_news.help}}')
async def main(msg: Bot.MessageSession):
    res = await news(msg)
    Logger.debug('res' + str(res))
    if res is None:
        message = msg.locale.t('mcbbs_news.message.not_found')
    else:
        lst = []
        for i in res:
            lst += [f'{i["count"]}. [{i["category"]}] {i["title"]} - {i["author"]} @ {i["time"]}\n{i["url"]}']
        message = '\n'.join(lst) + '\n' + msg.locale.t('mcbbs_news.message.more') + \
                  Url('https://www.mcbbs.net/forum-news-1.html').url
    await msg.finish(message)
