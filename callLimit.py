import os    
from core import log
from core.database.bot import Admin
from core.database.user import User
from core.customPluginInstance import AmiyaBotPluginInstance
from core.database.group import GroupActive
from amiyabot import Message, Chain
from .frequencyControl import HeatBar

curr_dir = os.path.dirname(__file__)
user_hb = HeatBar()
group_hb = HeatBar()


class CallLimitPluginInstance(AmiyaBotPluginInstance):
    def install(self):
        Config.abandon_yaml('resource/plugins/callLimitConfig.yaml')
        Config.update()
        user_hb.setattr('inertia', Config.user_inertia)
        user_hb.setattr('moment', Config.user_moment)
        user_hb.setattr('cool', Config.user_cool)
        group_hb.setattr('inertia', Config.group_inertia)
        group_hb.setattr('moment', Config.group_moment)
        group_hb.setattr('cool', Config.group_cool)
        

bot = CallLimitPluginInstance(
    name='响应频率限制',
    version='2.3.18',
    plugin_id='kkss-call-limit',
    plugin_type='',
    description='限制唤起的频率',
    document=f'{curr_dir}/README.md',
    global_config_default=f'{curr_dir}/default.json',
    global_config_schema=f'{curr_dir}/schema.json',
)


class Config:
    if_reply = 'ONCE'
    white_groups = []
    white_users = []
    white_admin = True
    user_reply = ''
    group_reply = ''
    reply_no_prefix = True

    user_moment = 3
    user_inertia = 30
    user_cool = 120

    group_moment = 0
    group_inertia = 0
    group_cool = 0

    @staticmethod
    def update():
        try:
            Config.if_reply = str(bot.get_config('ifReply'))
            Config.white_groups = list(bot.get_config('whiteGroups'))
            Config.white_users = list(bot.get_config('whiteUsers'))
            Config.white_admin = bool(bot.get_config('whiteAdmin'))
            Config.user_reply = str(bot.get_config('userReply'))
            Config.group_reply = str(bot.get_config('groupReply'))
            Config.reply_no_prefix = bool(bot.get_config('replyNoPrefix'))

            user = bot.get_config('user')
            Config.user_moment = float(user.get('moment'))
            Config.user_inertia = int(user.get('inertia'))
            Config.user_cool = float(user.get('cool'))

            group = bot.get_config('group')
            Config.group_moment = float(group.get('moment'))
            Config.group_inertia = int(group.get('inertia'))
            Config.group_cool = float(group.get('cool'))

        except TypeError:
            log.warning('响应频率限制: 控制台配置有误, 请检查')


    @staticmethod
    def abandon_yaml(config_path: str):
        if os.path.exists(config_path):
            dir_name = os.path.splitext(config_path)[0] + '(已弃用).yaml'
            os.rename(config_path, dir_name)


def in_white_list(user_id:int=None, group_id:int=None):

    if bool(User.get_or_none(user_id=user_id, black=1)):
        return True

    if user_id and user_id in Config.white_users:
        return True

    is_sleep = bool(GroupActive.get_or_none(group_id=group_id, active=0))
    if group_id and (group_id in Config.white_groups or is_sleep): 
        return True

    if Config.white_admin and bool(Admin.get_or_none(account=user_id)):   
        return True


def get_notice(ban:int,group_id:int=0, user_id:int=0,):
    if_reply:str = Config.if_reply

    reply = ''
    if group_id:
        reply = Config.group_reply.replace('time%', str(ban))
    if user_id:
        reply = Config.user_reply.replace('time%', str(ban))
        
    reply = reply.replace('\\n','\n').replace('\\\n','\\n')

    if if_reply.startswith('ONCE'):
        if group_id in group_hb.release_number:
            group_hb.release_number.remove(group_id)
            return reply

        if user_id in user_hb.release_number:
            user_hb.release_number.remove(user_id)
            return reply
        
    if if_reply.startswith('EVERY'):
        return reply

    return None


@bot.timed_task(each=5)
async def _(_):
    Config.update()
    user_hb.setattr('inertia', Config.user_inertia)
    user_hb.setattr('moment', Config.user_moment)
    user_hb.setattr('cool', Config.user_cool)
    group_hb.setattr('inertia', Config.group_inertia)
    group_hb.setattr('moment', Config.group_moment)
    group_hb.setattr('cool', Config.group_cool)



async def listener(data: Message):
    group_id = data.channel_id
    user_id = data.user_id

    data.text_words.append('__HANDLE_WITH_LISTENER__')

    if in_white_list(user_id=user_id):
        return False

    if in_white_list(group_id=group_id):
        return False

    if not group_hb.check(group_id):
        if user_ban := user_hb.trigger(user_id):
            if text := get_notice(user_ban, user_id=user_id):
                await data.send(Chain(data, at=True).text(text))
            return True, 999

    if not user_hb.check(user_id):
        if group_ban := group_hb.trigger(group_id):
            if text := get_notice(group_ban, group_id=group_id):
                await data.send(Chain(data, at=False).text(text))
            return True, 999


@bot.on_message(verify=listener)
async def _(_): ...


@bot.message_before_handle
async def _(data: Message, factory_name: str, _):
    group_id = data.channel_id
    user_id = data.user_id

    if factory_name == 'amiyabot-hsyhhssyy-chatgpt':
        return True

    if '__HANDLE_WITH_LISTENER__' in data.text_words:
        return True

    if in_white_list(user_id=user_id):
        return True

    if in_white_list(group_id=group_id):
        return True        

    if not group_hb.check(group_id):
        if user_ban := user_hb.trigger(user_id):
            if Config.reply_no_prefix:
                if text := get_notice(user_ban, user_id=user_id):
                    await data.send(Chain(data, at=True).text(text))
            return False

    if not user_hb.check(user_id):
        if group_ban := group_hb.trigger(group_id):
            if Config.reply_no_prefix:
                if text := get_notice(group_ban, group_id=group_id):
                    await data.send(Chain(data, at=False).text(text))
            return False
    
    return True

    
        