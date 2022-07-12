from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.typing import T_State
from nonebot.params import State, ArgStr, CommandArg
from nonebot import on_command
from nonebot import on_keyword
from .data_source import DataGet, DataProcess
songpicker = on_keyword({'点歌'}, priority=5)

dataGet = DataGet()


@songpicker.handle()
async def _(event:Event, state: T_State = State()):
    content = str(event.get_message()).split(" ")
    if len(content) > 1:
        state["song_name"] = content[1]
        # TODO: add config option for default choice
    if len(content) > 2 and content[2].isdigit():
        state["choice"] = content[2]


@songpicker.got("song_name", prompt="小可爱要点什么歌呀？")
async def _(state: T_State = State()):
    song_name = state["song_name"]
    
    song_ids = await dataGet.song_ids(song_name=song_name)
    if not song_ids:
        await songpicker.reject("没有找到这首歌，请发送其它歌名哦！")
    song_infos = list()
    for song_id in song_ids:
        song_info = await dataGet.song_info(song_id=song_id)
        song_infos.append(song_info)

    song_infos = await DataProcess.mergeSongInfo(song_infos=song_infos)
    if not "choice" in state:
        await songpicker.send(song_infos)
    state["song_ids"] = song_ids


@songpicker.got("choice")
async def _(state: T_State = State()):
    song_ids = state["song_ids"]
    choice = state["choice"]
    content = str(choice)
    if content=='取消':
        await songpicker.finish('已取消')
    
    try:
        choice = int(content)
    except ValueError:
        await songpicker.reject("选项只能是数字，请重选或者取消")
    if choice >= len(song_ids):
        await songpicker.reject("选项超出可选范围，请重选或者取消")

    selected_song_id = song_ids[choice]
    await songpicker.send(MessageSegment.music("163", int(selected_song_id)))

    song_comments = await dataGet.song_comments(song_id=selected_song_id)
    song_comments = await DataProcess.mergeSongComments(song_comments=song_comments)
    song_comments = "下面为您播送热评：\n" + song_comments

    await songpicker.finish(song_comments)
