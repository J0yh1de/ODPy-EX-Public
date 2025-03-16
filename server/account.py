import json
from os.path import exists
from virtualtime import time
from copy import deepcopy
from base64 import b64encode
from hashlib import md5
from flask import request
from datetime import datetime

from constants import (
    USER_JSON_PATH,
    CONFIG_PATH,
    EX_CONFIG_PATH,
    BATTLE_REPLAY_JSON_PATH,
    SYNC_DATA_TEMPLATE_PATH,
    CRISIS_V2_JSON_BASE_PATH,
    MAILLIST_PATH,
    SQUADS_PATH,
    get_memory
)
from utils import read_json, write_json
import uuid

def accountLogin():
    try:
        uid = uuid.UUID(request.headers.get("Uid"))
    except Exception:
        uid = uuid.uuid4()

    data = request.data
    data = {
        "result": 0,
        "uid": str(uid),
        "secret": "yostar",
        "serviceLicenseVersion": 0
    }

    return data


def accountSyncData():
    a = datetime.now()
    if not exists(USER_JSON_PATH):
        write_json({}, USER_JSON_PATH)

    saved_data = read_json(USER_JSON_PATH, encoding="utf-8")
    mail_data = read_json(MAILLIST_PATH, encoding="utf-8")
    player_data = read_json(SYNC_DATA_TEMPLATE_PATH, encoding="utf-8")
    config = read_json(CONFIG_PATH)
    exconfig = read_json(EX_CONFIG_PATH)

    # Load newest data
    data_skin = get_memory("skin_table")
    character_table = get_memory("character_table")
    equip_table = get_memory("uniequip_table")
    battle_equip_table = get_memory("battle_equip_table")
    display_meta_table = get_memory("display_meta_table")
    retro_table = get_memory("retro_table")
    charm_table = get_memory("charm_table")
    activity_table = get_memory("activity_table")
    charword_table = get_memory("charword_table")
    stage_table = get_memory("stage_table")
    story_table = get_memory("story_table")
    addon_table = get_memory("handbook_info_table")
    story_review_table = get_memory("story_review_table")
    story_review_meta_table = get_memory("story_review_meta_table")
    enemy_handbook_table = get_memory("enemy_handbook_table")
    medal_table = get_memory("medal_table")

    ts = round(time())
    cnt = 0
    cntInstId = 1
    tempSkinTable = {}
    myCharList = {}
    charGroup = {}
    buildingChars = {}

    # charRotation
    default_char_rotation = {
        "current": "1",
        "preset": {
            "1": {
                "background": "bg_rhodes_day",
                "homeTheme": "tm_rhodes_day",
                "name": "未命名的配置",
                "profile": "char_171_bldsk@witch#1",
                "profileInst": "171",
                "slots": [
                    {
                        "charId": "char_171_bldsk",
                        "skinId": "char_171_bldsk@witch#1"
                    }
                ]
            }
        }
    }
    player_data["user"].setdefault("charRotation", default_char_rotation)
    saved_data["user"]["charRotation"] = player_data["user"]["charRotation"]
    target_current = player_data["user"]["charRotation"]["current"]
    use_profile = player_data["user"]["charRotation"]["preset"][target_current]["profile"]
    for slots in player_data["user"]["charRotation"]["preset"][target_current]["slots"]:
        if slots.get("skinId") == use_profile:
            use_charid = slots.get("charId")
            break
    player_data["user"]["status"]["secretary"] = use_charid
    player_data["user"]["status"]["secretarySkinId"] = use_profile
    player_data["user"]["background"]["selected"] = player_data["user"]["charRotation"]["preset"][target_current]["background"]


    # Tamper Skins
    # 初始化玩家数据中的皮肤数据
    player_data["user"]["skin"]["characterSkins"] = {}
    # 初始化临时皮肤表
    tempSkinTable = {}

    # 遍历皮肤数据
    for skin_key, character_skin in data_skin["charSkins"].items():
        # 如果皮肤键中不包含@符号，则跳过
        if "@" not in skin_key:
            continue

        # 将皮肤键添加到玩家数据中的皮肤数据中
        player_data["user"]["skin"]["characterSkins"][skin_key] = 1
        # 获取角色ID
        char_id = character_skin["charId"]
        # 获取当前皮肤显示的年份
        current_year = character_skin["displaySkin"]["onYear"]

        # 如果角色ID不在临时皮肤表中，则将皮肤键添加到临时皮肤表中
        if char_id not in tempSkinTable:
            tempSkinTable[char_id] = skin_key
        # 如果角色ID已经在临时皮肤表中，则比较当前皮肤显示的年份和已有皮肤显示的年份，将年份较新的皮肤键添加到临时皮肤表中
        else:
            existing_year = data_skin["charSkins"][tempSkinTable[char_id]]["displaySkin"]["onYear"]
            if current_year > existing_year:
                tempSkinTable[char_id] = skin_key

    # Tamper Operators
    edit_json = config["charConfig"]

    cnt = 0
    operatorKeys = list(character_table.keys())
    equip_keys = set(equip_table["charEquip"].keys())
    player_data_keys = set(player_data["user"]["troop"]["chars"].keys())

    for operatorKey in operatorKeys:
        if "char" not in operatorKey:
            continue

        charGroup.update({operatorKey: {"favorPoint": 25570}})

    # 预定义常量
    EXCLUDED_SKIN_OPERATORS = {
        "char_508_aguard", "char_509_acast", 
        "char_510_amedic", "char_511_asnipe"
    }
    SPECIAL_INST_IDS = {609, 610, 611, 612, 613, 614, 615}
    AMIYA_TEMPLATES = {
        "char_002_amiya": {
            "skills": ["skcom_magic_rage[3]", "skchr_amiya_2", "skchr_amiya_3"],
            "skin": "char_002_amiya@test#1",
            "default_index": 2
        },
        "char_1001_amiya2": {
            "skills": ["skchr_amiya2_1", "skchr_amiya2_2"],
            "skin": "char_1001_amiya2@casc#1",
            "default_index": 1
        },
        "char_1037_amiya3": {
            "skills": ["skchr_amiya3_1", "skchr_amiya3_2"],
            "skin": "char_1001_amiya2@casc#1",
            "default_index": 1
        }
    }

    for operator_key, char_id in zip(operatorKeys, character_table):
        inst_id = int(operator_key.split("_")[1])
        # 跳过非角色键
        if "char" not in operator_key:
            continue
        
        if exconfig["useExistingCharData"]:
            # 存在已有角色数据的情况
            if str(inst_id) in player_data_keys:
                myCharList[inst_id] = player_data["user"]["troop"]["chars"][str(inst_id)]
        else:
            # ---------- 角色创建逻辑 ---------- 
            # 语音语言处理
            voice_lan = charword_table["charDefaultTypeDict"].get(operator_key, "JP")
            
            # 进化阶段计算
            evolve_phase = edit_json["evolvePhase"]
            max_phase = len(character_table[char_id]["phases"]) - 1
            evolve_phase = min(evolve_phase, max_phase) if evolve_phase != -1 else max_phase
            
            # 等级计算
            level = (
                edit_json["level"] if edit_json["level"] != -1 
                else character_table[char_id]["phases"][evolve_phase]["maxLevel"]
            )
            
            # 基础角色结构
            inst_id = int(operator_key.split("_")[1])
            operator = {
                "instId": inst_id,
                "charId": operator_key,
                "favorPoint": edit_json["favorPoint"],
                "potentialRank": edit_json["potentialRank"],
                "mainSkillLvl": edit_json["mainSkillLvl"],
                "skin": f"{operator_key}#1",
                "level": level,
                "exp": 0,
                "evolvePhase": evolve_phase,
                "defaultSkillIndex": len(character_table[char_id]["skills"]) - 1,
                "gainTime": int(time()),
                "skills": [],
                "voiceLan": voice_lan,
                "currentEquip": None,
                "equip": {},
                "starMark": 0,
            }

            # ---------- 技能处理 ----------
            for skill in character_table[char_id]["skills"]:
                operator["skills"].append({
                    "skillId": skill["skillId"],
                    "unlock": 1,
                    "state": 0,
                    "specializeLevel": (
                        edit_json["skillsSpecializeLevel"] 
                        if skill["levelUpCostCond"] 
                        else 0
                    ),
                    "completeUpgradeTime": -1
                })

            # ---------- 模组处理 ----------
            if operator_key in equip_table["charEquip"]:
                equip_list = equip_table["charEquip"][operator_key]
                operator["equip"] = {
                    equip: {
                        "hide": 0,
                        "locked": 0,
                        "level": (
                            len(battle_equip_table[equip]["phases"]) 
                            if equip in battle_equip_table 
                            else 1
                        )
                    } for equip in equip_list
                }
                operator["currentEquip"] = equip_list[-1]

            # ---------- 皮肤处理 ----------
            # 精二皮肤
            if (operator_key not in EXCLUDED_SKIN_OPERATORS and 
                operator["evolvePhase"] == 2 and 
                inst_id not in SPECIAL_INST_IDS):
                operator["skin"] = f"{operator_key}#2"
            
            # 角色最新皮肤覆盖
            if operator_key in tempSkinTable:
                operator["skin"] = tempSkinTable[operator_key]

            # ---------- 自定义数据覆盖 ----------
            if custom_data := edit_json["customUnitInfo"].get(operator_key):
                for key, value in custom_data.items():
                    if key == "skills":
                        for idx, sl in enumerate(value):
                            operator["skills"][idx]["specializeLevel"] = sl
                    else:
                        operator[key] = value

            # ---------- 特殊角色处理 ----------
            # 阿米娅特殊形态
            if operator_key == "char_002_amiya":
                operator.update({
                    "defaultSkillIndex": -1,
                    "skills": [],
                    "currentTmpl": "char_002_amiya",
                    "tmpl": {
                        key: {
                            "skinId": val["skin"],
                            "defaultSkillIndex": val["default_index"],
                            "skills": [{
                                "skillId": skill,
                                "unlock": 1,
                                "state": 0,
                                "specializeLevel": edit_json["skillsSpecializeLevel"],
                                "completeUpgradeTime": -1
                            } for skill in val["skills"]],
                            "currentEquip": None,
                            "equip": {}
                        } for key, val in AMIYA_TEMPLATES.items()
                    }
                })
                # 处理阿米娅模组
                char_equip_cache = equip_table["charEquip"]
                for tmpl in AMIYA_TEMPLATES.keys() & char_equip_cache.keys():
                        equip_list = char_equip_cache[tmpl]
                        operator["tmpl"][tmpl]["equip"] = {
                            equip: {
                                "hide": 0,
                                "locked": 0,
                                "level": (
                                    len(battle_equip_table[equip]["phases"]) 
                                    if equip in battle_equip_table 
                                    else 1
                                )
                            } for equip in equip_list
                        }
                        operator["tmpl"][tmpl]["currentEquip"] = equip_list[-1]
            elif operator_key == "char_512_aprot":
                operator["skin"] = "char_512_aprot#1"

            # ---------- 基建数据处理 ----------
            buildingChars[inst_id] = {
                "charId": operator_key,
                "lastApAddTime": round(time()) - 3600,
                "ap": 8640000,
                "roomSlotId": "",
                "index": -1,
                "changeScale": 0,
                "bubble": {
                    "normal": {"add": -1, "ts": 0},
                    "assist": {"add": -1, "ts": 0}
                },
                "workTime": 0
            }

            # ---------- 最终数据存储 ----------
            myCharList[inst_id] = operator
            player_data["user"]["dexNav"]["character"][operator_key] = {
                "charInstId": inst_id,
                "count": 6
            }

    cntInstId = 10000

    dupe_characters = edit_json["duplicateUnits"]
    for dupeChar in dupe_characters:
        tempChar = {}
        char_id_index = {
            char["charId"]: inst_id 
            for inst_id, char in myCharList.items()
        }
        for dupeChar in dupe_characters:
            if inst_id := char_id_index.get(dupeChar):
                tempChar = deepcopy(myCharList[inst_id])
                break

        tempChar["instId"] = int(cntInstId)
        myCharList[int(cntInstId)] = tempChar
        cntInstId += 1

    player_data["user"]["troop"]["chars"] = myCharList
    player_data["user"]["troop"]["charGroup"] = charGroup
    player_data["user"]["troop"]["curCharInstId"] = cntInstId

    # Tamper story
    myStoryList = {"init": 1}
    for story in story_table:
        myStoryList.update({story:1})

    player_data["user"]["status"]["flags"] = myStoryList

    # Tamper Stages
    myStageList = {}
    
    for stage in stage_table["stages"]:
        myStageList.update({
            stage: {
                "completeTimes": 1,
                "hasBattleReplay": 0,
                "noCostCnt": 0,
                "practiceTimes": 0,
                "stageId": stage_table["stages"][stage]["stageId"],
                "startTimes": 1,
                "state": 3
            }
        })
    
    player_data["user"]["dungeon"]["stages"] = myStageList

    # Tamper addon [paradox&records]
    addonList = {}
    for charId in addon_table["handbookDict"]:
        addonList[charId] = {"story":{}}
        story = addon_table["handbookDict"][charId]["handbookAvgList"]
        for i,j in zip(story,range(len(story))):
            if "storySetId" in i:
                addonList[charId]["story"].update({
                    addon_table["handbookDict"][charId]["handbookAvgList"][j]["storySetId"]: {
                        "fts": 1649232340,
                        "rts": 1649232340
                    }
                })

    for stage in addon_table["handbookStageData"]:
        addonList[stage].update({
            "stage": {
                addon_table["handbookStageData"][stage]["stageId"]: {
                    "startTimes": 0,
                    "completeTimes": 1,
                    "state": 3,
                    "fts": 1624284657,
                    "rts": 1624284657,
                    "startTime": 2
                }
            }
        }) 

    player_data["user"]["troop"]["addon"].update(addonList) # TODO: I might try MongoDB in the future.

    # Tamper Side Stories and Intermezzis
    block = {}
    for retro in retro_table["retroActList"]:
        block.update({
            retro: {
                "locked": 0,
                "open": 1
            }
        })
    player_data["user"]["retro"]["block"] = block

    trail = {}
    for retro in retro_table["retroTrailList"]:
        trail.update({retro:{}})
        for trailReward in retro_table["retroTrailList"][retro]["trailRewardList"]:
            trail.update({
                retro: {
                    trailReward["trailRewardId"]: 1
                }
            })
    player_data["user"]["retro"]["trail"] = trail

    # Tamper Anniliations
    for stage in stage_table["stages"]:
        if stage.startswith("camp"):
            player_data["user"]["campaignsV2"]["instances"].update({
                stage: {
                    "maxKills": 400,
                    "rewardStatus": [1, 1, 1, 1, 1, 1, 1, 1]
                }
            })

            player_data["user"]["campaignsV2"]["sweepMaxKills"].update({stage: 400})
            player_data["user"]["campaignsV2"]["open"]["permanent"].append(stage)
            player_data["user"]["campaignsV2"]["open"]["training"].append(stage)

    # Tamper Avatars and Backgrounds
    avatar_icon = {}
    for avatar in display_meta_table["playerAvatarData"]["avatarList"]:
        avatar_icon.update({
            avatar["avatarId"]: {
                "ts": round(time()),
                "src": "initial" if avatar["avatarId"].startswith("avatar_def") else "other"
            }
        })
    player_data["user"]["avatar"]["avatar_icon"] = avatar_icon

    bgs = {}
    for bg in display_meta_table["homeBackgroundData"]["homeBgDataList"]:
        bgs.update({
            bg["bgId"]: {
                "unlock": round(time())
            }
        })
    player_data["user"]["background"]["bgs"] = bgs

    if "themeList" in display_meta_table["homeBackgroundData"]:
        themes = {}
        for theme in display_meta_table["homeBackgroundData"]["themeList"]:
            themes[theme["id"]] = {"unlock": 1691670000}
        player_data["user"]["homeTheme"]["themes"] = themes

    # Update charms
    for charm in charm_table["charmList"]:
        player_data["user"]["charm"]["charms"].update({charm["id"]: 1})

    # Update battle bus
    if "carData" in activity_table:
        for car_gear in activity_table["carData"]["carDict"]:
            player_data["user"]["car"]["accessories"].update({
                car_gear: {
                    "id": car_gear,
                    "num": len(activity_table["carData"]["carDict"][car_gear]["posList"])
                }
            })

    # Update Stultifera Navis
    deep_sea = player_data["user"]["deepSea"]
    activity_data = activity_table["activity"]["TYPE_ACT17SIDE"]["act17side"]
    deep_sea.update({
        "places": {place:2 for place in activity_data["placeDataMap"]},
        "nodes": {node:2 for node in activity_data["nodeInfoDataMap"]},
        "choices": {
            k: [2]*len(v["optionList"]) 
            for k,v in activity_data["choiceNodeDataMap"].items()
        }
    })

    for event in activity_data["eventDataMap"]:
        player_data["user"]["deepSea"]["events"].update({event: 1})

    for treasure in activity_data["treasureNodeDataMap"]:
        player_data["user"]["deepSea"]["treasures"].update({treasure: 1})

    for story in activity_data["storyNodeDataMap"]:
        player_data["user"]["deepSea"]["stories"].update(
            {activity_data["storyNodeDataMap"][story]["storyKey"]: 1}
        )

    for tech in activity_data["techTreeDataMap"]:
        player_data["user"]["deepSea"]["techTrees"].update({
            tech: {
                "state": 2,
                "branch": activity_data["techTreeDataMap"][tech]["defaultBranchId"]
            }
        })

    for log in activity_data["archiveItemUnlockDataMap"]:
        if not log.startswith("act17side_log_"):
            continue

        chapter = activity_data["archiveItemUnlockDataMap"][log]["chapterId"]
        if chapter in player_data["user"]["deepSea"]["logs"].keys():
            player_data["user"]["deepSea"]["logs"][chapter].append(log)
        else:
            player_data["user"]["deepSea"]["logs"].update({chapter:[log]})

    # Check if mail exists
    received_set = set(mail_data["recievedIDs"])
    deleted_set = set(mail_data["deletedIDs"])
    all_mails = set(mail_data["mailList"].keys())
    if not all_mails - (received_set | deleted_set):
        player_data["user"]["pushFlags"]["hasGifts"] = 1

    # Update timestamps
    current_ts = int(time())
    ts_fields = [
        "lastRefreshTs", "lastApAddTime", "registerTs", "lastOnlineTs"
    ]
    for field in ts_fields:
        player_data["user"]["status"][field] = current_ts
    player_data["user"]["crisis"]["lst"] = ts
    player_data["user"]["crisis"]["nst"] = ts + 3600
    player_data["ts"] = ts

    replay_data = read_json(BATTLE_REPLAY_JSON_PATH)
    replay_data["currentCharConfig"] = md5(b64encode(json.dumps(edit_json).encode())).hexdigest()
    write_json(replay_data, BATTLE_REPLAY_JSON_PATH)

    # Enable battle replays
    if replay_data["currentCharConfig"] in list(replay_data["saved"].keys()):
        for replay in replay_data["saved"][replay_data["currentCharConfig"]]:
            if replay in player_data["user"]["dungeon"]["stages"]:
                player_data["user"]["dungeon"]["stages"][replay]["hasBattleReplay"] = 1

    squads_data = read_json(SQUADS_PATH)
    charId2instId = {}
    for character_index, character in player_data["user"]["troop"]["chars"].items():
        charId2instId[character["charId"]] = character["instId"]
    for i in squads_data:
        j = 0
        for slot in squads_data[i]["slots"]:
            if j == 12:
                break
            charId = slot["charId"]
            del slot["charId"]
            if charId in charId2instId:
                instId = charId2instId[charId]
                slot["charInstId"] = instId
                if (
                    slot["currentEquip"]
                    not in player_data["user"]["troop"]["chars"][instId]["equip"]
                ):
                    slot["currentEquip"] = None
            else:
                squads_data[i]["slots"][j] = None
            j += 1
        for k in range(j, 12):
            squads_data[i]["slots"].append(None)
        squads_data[i]["slots"] = squads_data[i]["slots"][:12]

    player_data["user"]["troop"]["squads"] = squads_data

    secretarySkinId = config["userConfig"]["secretarySkinId"]
    theme = config["userConfig"]["theme"]

    if "user" in saved_data and config["userConfig"]["restorePreviousStates"]["ui"]:
        secretarySkinId = saved_data["user"]["status"]["secretarySkinId"]
        theme = saved_data["user"]["homeTheme"]["selected"]

    if (current_preset := player_data["user"]["charRotation"]["preset"].get(
        player_data["user"]["charRotation"]["current"]
    )):
        player_data["user"]["status"]["secretary"] = current_preset["profileInst"]
        player_data["user"]["background"]["selected"] = current_preset["background"]

    player_data["user"]["status"]["secretarySkinId"] = secretarySkinId
    player_data["user"]["homeTheme"]["selected"] = theme

    season = config["towerConfig"]["season"]

    player_data["user"]["tower"]["season"]["id"] = season

    story_review_groups = {}
    for i in story_review_table:
        story_review_groups[i] = {"rts": 1700000000, "stories": [], "trailRewards": []}
        for j in story_review_table[i]["infoUnlockDatas"]:
            story_review_groups[i]["stories"].append(
                {"id": j["storyId"], "uts": 1695000000, "rc": 1}
            )
        if i in story_review_meta_table["miniActTrialData"]["miniActTrialDataMap"]:
            for j in story_review_meta_table["miniActTrialData"]["miniActTrialDataMap"][
                i
            ]["rewardList"]:
                story_review_groups[i]["trailRewards"].append(j["trialRewardId"])
    player_data["user"]["storyreview"]["groups"] = story_review_groups

    enemies = {}
    if "enemyData" in enemy_handbook_table:
        for i in enemy_handbook_table["enemyData"]:
            enemies[i] = 1
    else:
        for i in enemy_handbook_table:
            enemies[i] = 1
    player_data["user"]["dexNav"]["enemy"]["enemies"] = enemies

    for i in activity_table["activity"]:
        if i not in player_data["user"]["activity"]:
            player_data["user"]["activity"][i] = {}
        for j in activity_table["activity"][i]:
            if j not in player_data["user"]["activity"][i]:
                player_data["user"]["activity"][i][j] = {}

    player_data["user"]["medal"] = {"medals": {}}
    for i in medal_table["medalList"]:
        medalId = i["medalId"]
        player_data["user"]["medal"]["medals"][medalId] = {
            "id": medalId,
            "val": [],
            "fts": 1695000000,
            "rts": 1695000000,
        }

    rlv2_table = get_memory("roguelike_topic_table")
    for theme in player_data["user"]["rlv2"]["outer"]:
        if theme in rlv2_table["details"]:
            player_data["user"]["rlv2"]["outer"][theme]["record"]["stageCnt"] = {
                i: 1 for i in rlv2_table["details"][theme]["stages"]
            }

    selected_crisis = config["crisisV2Config"]["selectedCrisis"]
    if selected_crisis:
        rune = read_json(
            f"{CRISIS_V2_JSON_BASE_PATH}{selected_crisis}.json", encoding="utf-8"
        )
        season = rune["info"]["seasonId"]
        player_data["user"]["crisisV2"]["current"] = season

    write_json(player_data, USER_JSON_PATH, encoding="utf-8")

    b = datetime.now()
    print(f"syncdata耗时: {b - a}")
    return player_data


def accountSyncStatus():
    
    data = request.data
    data = {
        "ts": round(time()),
        "result": {},
        "playerDataDelta": {
            "modified": {},
            "deleted": {}
        }
    }

    return data


def accountYostarAuthRequest():

    data = request.data
    data = {}

    return data


def accountYostarAuthSubmit():

    data = request.data
    data = {
        "result": 0,
        "yostar_account": "1234567890@123.com",
        "yostar_token": "a",
        "yostar_uid": "10000023"
    }

    return data

def syncPushMessage():

    # 数据同步参数，不做处理

    return {
        "code": 200,
        "msg": "OK",
    }
