import argparse
import json
import re
import sqlite3
import types
from enum import Enum, auto
from functools import partial
from pathlib import Path

from sentinel.helpers import PathHelper
from rich.console import Console

from sentinel.classes import Queries

console = Console(record=True)

PART_REGEX = re.compile(r'(?:\[part_(\d+)_value])')
PRCT_REGEX = re.compile(r'(?:\[part_(\d+)_value\|div100\|minus1\|abs\|percent])')
PCT2_REGEX = re.compile(r'(?:\[part_(\d+)_value\|percent])')
COST_REGEX = re.compile(r'(?:\[cost\|div10])')
COOL_REGEX = re.compile(r'(?:\[cool_time])')

class Rarity(Enum):
    R   = 200
    SR  = 300
    MR  = 350
    SSR = 400
    UR  = 500

class Element(Enum):
    def __new__(cls, value, en):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.en = en
        return obj
  
    赤 = (1, "Red")
    青 = (2, "Blue")
    緑 = (3, "Green")
    黄 = (4, "Yellow")
    紫 = (5, "Purple")

class MasterDB(Enum):
    def __new__(cls, query, attached_db1=None, attached_db2=None, describe_func=None):
        obj = object.__new__(cls)
        obj._value_ = auto()
        obj.query = query
        obj.attached_db1 = attached_db1
        obj.attached_db2 = attached_db2
        if describe_func:
            obj.describe = types.MethodType(describe_func, obj)
        return obj

    def __repr__(self):
        return '<%a>' % self.__class__.__name__
    @property
    def is_ignored(self):
        return not bool(self.query) #enum members/tables with a None query are not displayed
        
    @property
    def attached_db1_path(self):
        return f"{PathHelper.CURRENT_PATH}/{self.attached_db1}.db" # pylint: disable=maybe-no-member
    
    @property
    def attached_db2_path(self):
        return f"{PathHelper.CURRENT_PATH}/{self.attached_db2}.db" # pylint: disable=maybe-no-member

    @classmethod
    def get_previous_path(cls):
        return f"{PathHelper.PREVIOUS_PATH}/{cls.__name__.lower()}.db" # pylint: disable=maybe-no-member
    
    @classmethod
    def get_current_path(cls):
        return f"{PathHelper.CURRENT_PATH}/{cls.__name__.lower()}.db" # pylint: disable=maybe-no-member

    @classmethod
    def get_new_path(cls):
        return f"{PathHelper.NEW_PATH}/{cls.__name__.lower()}.db" # pylint: disable=maybe-no-member

    @classmethod
    def has_key(cls, name):
        return (name in cls.__members__) #True/False
    
    def view_ids(self, *ids, embed=None):
        connection = sqlite3.connect(self.get_new_path())
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        if self.attached_db1:
            cursor.execute('ATTACH DATABASE ? AS ?', (self.attached_db1_path, self.attached_db1))
        if self.attached_db2:
            cursor.execute('ATTACH DATABASE ? AS ?', (self.attached_db2_path, self.attached_db2))
        cursor.execute(
            self.query.format(param=','.join(['?']*len(ids))),
            ids
        )
        for row in cursor:
            if embed:
                self.describe_embed(embed, row)
            else:
                self.describe(row) # pylint: disable=E1102
        connection.close()

    def describe_embed(self, embed, *ids):
        #do the thing to attach text to the discord embed lol
        pass

    def describe(self, row): # pylint: disable=E0202
        console.print(f"ID: {row['id']}", dict(row))

    def active_skill_re(self, row) -> str:
        as_detail_sub = re.sub(PART_REGEX,
            lambda x: f"[{row[f'as_p{x.group(1)}_min']} — {row[f'as_p{x.group(1)}_max']}]", #forgive me for these horrible lambdas
            row['as_detail']
        )
        as_detail_sub = re.sub(PRCT_REGEX,
            lambda x: f"[{100 - row[f'as_p{x.group(1)}_min']} — {100 - row[f'as_p{x.group(1)}_max']}]",
            as_detail_sub
        )
        as_detail_sub = re.sub(PCT2_REGEX, #there's two different cases for this, somehow
            lambda x: f"[{100 - row[f'as_p{x.group(1)}_min']} — {100 - row[f'as_p{x.group(1)}_max']}]",
            as_detail_sub
        )
        as_detail_sub = re.sub(COST_REGEX,
            str(row['as_cost']//10),
            as_detail_sub
        )
        as_detail_sub = re.sub(COOL_REGEX,
            str(row['as_cool_time']),
            as_detail_sub
        )
        return as_detail_sub

    def support_skill_re(self, row) -> str:
        ss_detail_sub = re.sub(PART_REGEX,
            lambda x: f"[{row[f'ss_p{x.group(1)}_min']} — {row[f'ss_p{x.group(1)}_max']}]",
            row['ss_detail']
        )
        ss_detail_sub = re.sub(PRCT_REGEX,
            lambda x: f"[{100 - row[f'ss_p{x.group(1)}_min']} — {100 - row[f'ss_p{x.group(1)}_max']}]",
            ss_detail_sub
        )
        ss_detail_sub = re.sub(PCT2_REGEX, #there's two different cases for this, somehow
            lambda x: f"[{100 - row[f'ss_p{x.group(1)}_min']} — {100 - row[f'ss_p{x.group(1)}_max']}]",
            ss_detail_sub
        )
        return ss_detail_sub

class Accessories(MasterDB):

    def describe(self, row):
        # accessory_name = ENAccessoryName(row['accessory_id']).name #TODO accesory names?
        console.print(f"\nAccessory: {Rarity(row['rarity']).name} {row['name']} ({Element(row['element']).name})") # pylint: disable=E1120
        console.print(f"\nPassive Skill: {row['support_skill']}\n{self.support_skill_re(row)}")

    accessories = (Queries.accessories, 'skills')

class Adventure_Books(MasterDB):

    def describe(self, row):
        console.print(f"\nAdventure Book: {row['category']}")
        console.print(f"    Chapter: {row['chapter_name']} {row['episode']}:")
        # console.print(f"    Title: {row['sub_category']}")
        # console.print(f"    Label: {row['label']}")
        console.print(f"    Name: {row['display_name']}")

    adventure_books = (Queries.adventure_books)

class Brave_System(MasterDB):

    def describe(self, row):
        console.print(f"\nBrave System: {row['name']}")
        console.print(f"\n    {row['description']}")

    brave_system_components = (Queries.brave_system_components)
    
class Cards(MasterDB):

    def describe(self, row):
        # card_name = ENCharacterName(row['character_id']).name
        console.print(f"\nCard: {Rarity(row['rarity']).name} {row['nickname']} {row['character_name']} ({Element(row['element']).name})") # pylint: disable=E1120
        if row['ls_detail']:
            console.print(f"    Leader Skill: {row['leader_skill']}\n    {row['ls_detail']}")
        if row['as_detail']:
            console.print(f"    Active Skill: {row['active_skill']}\n    {self.active_skill_re(row)}")
        if row['ss_detail']:
            console.print(f"    Support Skill: {row['support_skill']}\n    {self.support_skill_re(row)}")
        if row['potential_gift_text']:
            console.print(f"    Potential Gift: {row['potential_gift_text']}")
        if row['limit_break_reward_text']:
            console.print(f"    Limit Break Reward: {row['limit_break_reward_text']}")

    cards = (Queries.cards, 'skills', 'characters')
    evolution_recipes = (None)
    special_attack_cards = (None)

class Cartoons(MasterDB):

    def describe(self, row):
        console.print(f"\n4Koma Chapter: {row['chapter_title']}")
        console.print(f"    Story Title: {row['story_title']}")
        console.print(f"    Start Date: {row['start_at']}")

    bingo_rewards = (None)
    bingo_sheets = (None)
    bingo_squares = (None)
    cartoon_chapters = (None)
    cartoon_frames = (None)
    cartoon_stories = (Queries.cartoon_stories)

class Characters(MasterDB):

    def describe(self, row):
        console.print(f"\nCharacter: {row['name']}")

    characters = (Queries.characters) #sensitive
    familiarity_levels = (None)

class Club_Workings(MasterDB):

    def describe(self, row):
        console.print(f"\nClub Order: {Rarity(row['rarity']).name} {row['title']}")
        console.print(f"    Description: {row['description']}")
        console.print(f"    Duration: {str(row['duration']//60//60)} hrs, Expires: {row['expired_at']}") # 1800 min -> 0.5 hrs
        console.print(f"    Potential Rewards: {row['reward_1']} {row['reward_2']} {row['reward_3']}")
        console.print(f"    Familiarity Exp: {row['familiarity_exp']}")

    club_orders = (Queries.club_orders)
    club_order_reward_boxes = (None)

class Enhancement(MasterDB):

    def describe(self, row):
        console.print(f"\nNoodle Cooking Result:")
        console.print(f"    Target: {row['target_character']}")
        console.print(f"    Target Line: {row['target_message']}")
        console.print(f"    Special Target Line: {row['target_special_message']}")
        console.print(f"    Cook: {row['cooking_character']}")
        console.print(f"    Cook Line: {row['cooking_message']}")
        console.print(f"    Special Cook Line: {row['cooking_special_message']}")

    noodle_cooking_characters = (Queries.noodle_cooking_characters, 'characters')
    # noodle_cookings = (Queries.noodle_cookings, 'characters')

class Event_Stories(MasterDB):

    def describe(self, row):
        pass #shouldn't be used
    
    def describe_event_items(self, row):
        console.print(f"\nEvent Item: {Rarity(row['rarity']).name} {row['name']}")
        console.print(f"    Chapter: {row['chapter']}")
    
    def describe_special_attack_characters(self, row):
        console.print(f"\nSpecial Attack Character: {row['character']}")
        console.print(f"    Chapter: {row['chapter']}")
        console.print(f"    Start Date: {row['start_at']}")
        console.print(f"    End_Date: {row['end_at']}")
    
    def describe_special_episode_conditions(self, row):
        console.print(f"\nSpecial Episode: {row['chapter']} {row['episode']}")
        console.print(f"    Start Date: {row['start_at']}")
        console.print(f"    End_Date: {row['end_at']}")

    event_items = (Queries.event_items, None, None, describe_event_items)
    special_attack_characters = (Queries.special_attack_characters, 'characters', None, describe_special_attack_characters)
    special_episode_conditions = (Queries.special_episode_conditions, None, None, describe_special_episode_conditions)
    special_episode_difficulties = (None) #TBD maybe
    special_episodes = (None)
    special_stage_battles = (None)
    special_stage_conditions = (None)
    special_stages = (None)

class Gachas(MasterDB):
    def describe_gacha_tickets(self, row):
        console.print(f"\nGacha Ticket: {row['ticket']}")
        # console.print(f"    Gacha: {row['gacha_name']}")
        console.print(f"    Description: {row['gacha_description']}")

    gacha_boxes = (None)
    gacha_contents = (None)
    gacha_lineups = (None)
    gacha_tickets = (Queries.gacha_tickets, None, None, describe_gacha_tickets)
    gachas = (None)

class Items(MasterDB):

    def describe(self, row):
        pass #shouldn't be used

    def describe_gifts(self, row):
        console.print(f"\nGift: {row['title']} x{row['quantity']}")

    def describe_title_items(self, row):
        console.print(f"\nTitle Item: {row['name']}")
        console.print(f"Description: {row['description']}")

    # activity_request_sheets = (None)
    bingo_open_items = (None)
    gifts = (None) #(Queries.gifts, None, None, describe_gifts)
    package_items = (None)
    title_items = (Queries.title_items, None, None, describe_title_items)

class Login_Bonus(MasterDB):

    def describe(self, row):
        console.print(f"\nLogin Bonus:")
        console.print(f"    Start Date: {row['start_at']}")
        console.print(f"    End Date: {row['end_at']}")
        console.print(f"    Comeback Date: {row['comeback_date']}")

    login_bonus_sheet_columns = (None)
    login_bonus_sheets = (Queries.login_bonus_sheets)

class Quests(MasterDB):

    def describe(self, row):
        console.print(f"\nChapter: {row['chapter']}")
        console.print(f"    Episode: {row['episode']}")

    battle_limit_entries = (None)
    chapter_release_conditions = (None)
    chapters = (None) #sensitive
    episode_difficulties = (None)
    episode_release_conditions = (None)
    episodes = (Queries.episodes, None, None) #sensitive
    stage_battles = (None)
    stage_release_conditions = (None)
    stages = (None)

class Skills(MasterDB):

    def describe_active_skill(self, row):
        if row['as_detail']:
            console.print(f"\nActive Skill: {row['active_skill']}\n{self.active_skill_re(row)}")

    def describe_passive_skill(self, row):
        if row['ss_detail']:
            console.print(f"\nPassive Skill: {row['support_skill']}\n{self.support_skill_re(row)}")
    
    def describe_area_skill(self, row):
        if row['detail']:
            console.print(f"\nArea Skill: {row['area_skill']}\n{self.active_skill_re(row)}")
            console.print(f"    Skill Part: {row['skill_part']}")

    def describe_skill_part(self, row):
        console.print(f"\nSkill Part: {row['name']}")
    
    def describe_zoon_skill(self, row):
        console.print(f"\nZone(?) Skill: {row['zoon_skill']}\n {row['detail']}")
        if row['part']:
            console.print(f"    Part(?): {row['part']}")

    active_skill = (Queries.active_skill, None, None, describe_active_skill)
    area_skill = (Queries.area_skill, None, None, describe_area_skill)
    passive_skill = (Queries.passive_skill, None, None, describe_passive_skill)
    skill_part = (Queries.skill_part, None, None, describe_skill_part)
    zoon_skill = (Queries.zoon_skill, None, None, describe_zoon_skill)

class Stack_Point_Event(MasterDB):
    stack_point_event_rewards = (None)

class User_Levels(MasterDB):
    user_levels = (None)

class Y3MasterDatabase:
    def __init__(self, platform, previous_version, is_english=None):
        PathHelper.set_vars(platform, previous_version)
        self.IS_ENG = is_english

    @staticmethod
    def _id_factory_(cursor, row):
        return row[0] #first column of result

    @staticmethod
    def _name_factory_(cursor, row):
        # workaround because pragma functions doesnt work with attached databases, as per an ancient bug apparently?
        # http://sqlite.1065341.n5.nabble.com/pragma-table-info-on-a-table-in-attached-db-td40362.html
        return row[1] #second column of result
    
    def make_changelog(self, update_name):
        new_path = Path("y3/exports/new_master_data")
        new_path.mkdir(parents=True, exist_ok=True)
        new_mdbs = [child.stem for child in new_path.iterdir() if child.is_file()]
        to_diff = [mdb for mdb in MasterDB.__subclasses__() if mdb.__name__.lower() in new_mdbs]
        if not new_mdbs:
            print("[red]something went wrong[/red]")
            return
        # print(to_diff)
        console.print(f"[red]<<< MDB CHANGELOG FOR {update_name} >>>[/red]")
        for database in to_diff:
            self.diff_mdb(database)
        console.print("\n[red]<<< MDB CHANGELOG END >>>[/red]")
        extracted_path = Path(f"y3/exports/extracted/changelog_{update_name}.txt")
        extracted_path.parent.mkdir(parents=True, exist_ok=True)
        console.save_text(extracted_path)

    def connect_mdb(self, database:Enum) -> object:
        """Returns an sqlite cursor connected to the target database. Boilerplate shortcut.
        """
        db_path = database.get_current_path()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("ATTACH DATABASE ? AS current_db;", (db_path,))
        return cursor
        

    def diff_mdb(self, database:Enum, embed=None) -> None:
        """Opens the previous version of the target database as `main`, and the current version as `current_db`
        to log new tables, columns, and rows to the console.
        """
        db_name = database.__name__.lower()
        previous_db = database.get_previous_path()
        current_db = database.get_current_path()
        console.print(f'\n////////// [yellow]{db_name}[/yellow] //////////')
        connection = sqlite3.connect(previous_db)
        cursor = connection.cursor()
        cursor.execute("ATTACH DATABASE ? AS current_db;", (current_db,))
        # retrieve first element (which should always be 'id') for single column select statements, but in this case it's the table name from the schema
        cursor.row_factory = self._id_factory_
        previous_tables = cursor.execute("SELECT name from main.sqlite_master WHERE type='table'").fetchall()
        current_tables = cursor.execute("SELECT name from current_db.sqlite_master WHERE type='table'").fetchall()

        cursor.row_factory = self._name_factory_ # change to access the name for PRAGMAs
        if previous_tables != current_tables:
            new_tables = [table for table in current_tables if table not in previous_tables]
            new_tables.sort()
            console.print(f'\nNew [green]tables[/green] in [yellow]{db_name}[/yellow]:\n[green]{new_tables}[/green]')
            for table in new_tables:
                new_columns = cursor.execute(f'PRAGMA current_db.table_info({table})').fetchall()
                new_columns.sort()
                console.print(f'\nNew [magenta]columns[/magenta] in [yellow]{db_name}[/yellow].[green]{table}[/green]:\n[magenta]{new_columns}[/magenta]')

        for table in previous_tables:
            cursor.row_factory = self._name_factory_
            previous_columns = cursor.execute(f"PRAGMA main.table_info({table});").fetchall()
            current_columns  = cursor.execute(f"PRAGMA current_db.table_info({table});").fetchall()

            cursor.row_factory = self._id_factory_ # reset to normal for SELECT statements
            if previous_columns != current_columns:
                new_columns = [column for column in current_columns if column not in previous_columns]
                new_columns.sort()
                console.print(f'\nNew [magenta]columns[/magenta] in [yellow]{db_name}[/yellow].[green]{table}[/green]:\n[magenta]{new_columns}[/magenta]')
            if database is Cards and table == 'cards': #special case because the database is gross and cards have a ton of redundant ids for the different levels... of the same card
                query = f'SELECT DISTINCT base_card_id FROM current_db.{table} WHERE base_card_id NOT IN (SELECT base_card_id FROM main.{table})'
            else:
                query = f'SELECT id FROM current_db.{table} WHERE id NOT IN (SELECT id FROM main.{table})'
            new_ids = cursor.execute(query).fetchall()
            if new_ids:
                new_ids.sort()
                if database.has_key(table) and not database[table].is_ignored:
                    console.print(f'\nNew [blue]IDs[/blue] in [yellow]{db_name}[/yellow].[green]{table}[/green]:') #\n{new_ids}
                    database[table].view_ids(*new_ids)
                else:
                    console.print(f"\nSkipping low importance table: [yellow]{db_name}[/yellow].[green]{table}[/green]")
                # else:
                #     cursor.row_factory = self._name_factory_
                #     column_ = cursor.execute(f"PRAGMA main.table_info({table});").fetchmany(3) #fetches up to the first three column names which should do a decent job of describing tables that dont have a specific query written.
                #     query = f"SELECT {', '.join(column_)} FROM current_db.{table} WHERE current_db.{table}.id IN ({','.join(['?']*len(new_ids))});"
                #     cursor.row_factory = sqlite3.Row
                #     result_rows = cursor.execute(query, new_ids).fetchall()
                #     for row in result_rows:
                #         console.print(dict(zip(column_, row)))
            # else:
            #     console.print(f'\nNo new IDs in [yellow]{db_name}[/yellow].[green]{table}[/green].')
        connection.close()

# def init_arguments() -> argparse.ArgumentParser: #TODO: could probably use a less stupid implementation... https://docs.python.org/3/library/argparse.html#action
#     parser = argparse.ArgumentParser(
#         usage="%(prog)s [OPTION]...",
#         description="does stuff"
#     )
#     group = parser.add_mutually_exclusive_group(required=False)
#     group.add_argument("-a", "--android", action="store_const", const="android")
#     group.add_argument("-i", "--iOS", action="store_const", const="iOS")
#     group.add_argument("-w", "--WebGL", action="store_const", const="WebGL")
#     return parser.parse_args()

# if __name__ == "__main__":
#     __args__ = init_arguments()
#     PLATFORM = __args__.android or __args__.iOS or __args__.WebGL
