from core.builtins import Bot, Image
from core.component import module
from core.utils.image_table import image_table_render, ImageTable

ali = module('alias', required_admin=True, base=True)


@ali.command('add <alias> <command> {{core.alias.help.add}}', 'remove <alias> {{core.alias.help.remove}}',
             'reset {{core.alias.help.reset}}',
             'list {{core.alias.help.list}}')
async def set_alias(msg: Bot.MessageSession):
    alias = msg.options.get('command_alias')
    arg1 = msg.parsed_msg.get('<alias>', False)
    arg2 = msg.parsed_msg.get('<command>', False)
    if alias is None:
        alias = {}
    if 'add' in msg.parsed_msg:
        if arg1 not in alias:
            has_prefix = False
            for prefixes in msg.prefixes:
                if arg2.startswith(prefixes):
                    has_prefix = True
                    break
            if not has_prefix:
                await msg.sendMessage(msg.locale.t("core.alias.message.add.invalid_prefix"))
                return
            alias[arg1] = arg2
            msg.data.edit_option('command_alias', alias)
            await msg.sendMessage(msg.locale.t("core.alias.message.add.success", arg1=arg1, arg2=arg2))
        else:
            await msg.sendMessage(msg.locale.t("core.alias.message.add.already_in", arg1=arg1))
    elif 'remove' in msg.parsed_msg:
        if arg1 in alias:
            del alias[arg1]
            msg.data.edit_option('command_alias', alias)
            await msg.sendMessage(msg.locale.t("core.alias.message.remove.success", arg1=arg1))
        else:
            await msg.sendMessage(msg.locale.t("core.alias.message.remove.not_found", arg1=arg1))
    elif 'reset' in msg.parsed_msg:
        msg.data.edit_option('command_alias', {})
        await msg.sendMessage(msg.locale.t("core.alias.message.reset.success"))
    elif 'list' in msg.parsed_msg:
        if len(alias) == 0:
            await msg.sendMessage(msg.locale.t("core.alias.message.list.none"))
        else:
            table = ImageTable([[k, alias[k]] for k in alias],
                               [msg.locale.t("core.alias.message.list.table.header.alias"),
                                msg.locale.t("core.alias.message.list.table.header.command")])
            img = await image_table_render(table)
            if img:
                await msg.sendMessage([msg.locale.t("core.alias.message.list.lists"), Image(img)])
            else:
                await msg.sendMessage(f'{msg.locale.t("core.alias.message.list.lists")}\n'
                                      + '\n'.join([f'{k} -> {alias[k]}' for k in alias]))
