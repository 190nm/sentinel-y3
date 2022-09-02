cards = """
    SELECT
        cards.id,
        cards.name,
        cards.nickname,
        cards.potential_gift_text,
        cards.rarity,
        cards.element,
        characters.name            AS character_name,
        cards.limit_break_reward_text,
        leader_skill.name         AS "leader_skill",
        leader_skill.detail       AS "ls_detail",
    	active_skill.name         AS "active_skill",
        active_skill.detail       AS "as_detail",
        active_skill.cost         AS "as_cost",
        active_skill.cool_time    AS "as_cool_time",
        active_skill.part_1_min   AS "as_p1_min",
        active_skill.part_1_max   AS "as_p1_max",
        active_skill.part_2_min   AS "as_p2_min",
        active_skill.part_2_max   AS "as_p2_max",
        active_skill.part_3_min   AS "as_p3_min",
        active_skill.part_3_max   AS "as_p3_max",
        active_skill.part_4_min   AS "as_p4_min",
        active_skill.part_4_max   AS "as_p4_max",
        active_skill.part_5_min   AS "as_p5_min",
        active_skill.part_5_max   AS "as_p5_max",
        active_skill.part_6_min   AS "as_p6_min",
        active_skill.part_6_max   AS "as_p6_max",
        active_skill.part_7_min   AS "as_p7_min",
        active_skill.part_7_max   AS "as_p7_max",
        active_skill.part_8_min   AS "as_p8_min",
        active_skill.part_8_max   AS "as_p8_max",
        active_skill.part_9_min   AS "as_p9_min",
        active_skill.part_9_max   AS "as_p9_max",
        active_skill.part_10_min  AS "as_p10_min",
        active_skill.part_10_max  AS "as_p10_max",
    	support_skill.name        AS "support_skill",
        support_skill.detail      AS "ss_detail",
        support_skill.part_1_min  AS "ss_p1_min",
        support_skill.part_1_max  AS "ss_p1_max",
        support_skill.part_2_min  AS "ss_p2_min",
        support_skill.part_2_max  AS "ss_p2_max",
        support_skill.part_3_min  AS "ss_p3_min",
        support_skill.part_3_max  AS "ss_p3_max",
        support_skill.part_4_min  AS "ss_p4_min",
        support_skill.part_4_max  AS "ss_p4_max",
        support_skill.part_5_min  AS "ss_p5_min",
        support_skill.part_5_max  AS "ss_p5_max",
        support_skill.part_6_min  AS "ss_p6_min",
        support_skill.part_6_max  AS "ss_p6_max",
        support_skill.part_7_min  AS "ss_p7_min",
        support_skill.part_7_max  AS "ss_p7_max",
        support_skill.part_8_min  AS "ss_p8_min",
        support_skill.part_8_max  AS "ss_p8_max",
        support_skill.part_9_min  AS "ss_p9_min",
        support_skill.part_9_max  AS "ss_p9_max",
        support_skill.part_10_min AS "ss_p10_min",
        support_skill.part_10_max AS "ss_p10_max"
    FROM
        cards
    LEFT JOIN
        skills.passive_skill leader_skill  ON cards.leader_skill_id = leader_skill.id
    LEFT JOIN
        skills.active_skill  active_skill  ON cards.active_skill_id = active_skill.id
    LEFT JOIN
        skills.passive_skill support_skill ON cards.support_skill_id = support_skill.id
    LEFT JOIN
        characters.characters characters ON cards.character_id = characters.id
    WHERE
        cards.id IN ({param});"""

accessories = """
    SELECT
        accessories.id,
        accessories.name,
        accessories.rarity,
        accessories.element,
        accessories.min_cost,
        accessories.max_cost,
        accessories.min_hit_point,
        accessories.max_hit_point,
        accessories.min_attack,
        accessories.max_attack,
        support_skill.name        AS "support_skill",
        support_skill.detail      AS "ss_detail",
        support_skill.part_1_min  AS "ss_p1_min",
        support_skill.part_1_max  AS "ss_p1_max",
        support_skill.part_2_min  AS "ss_p2_min",
        support_skill.part_2_max  AS "ss_p2_max",
        support_skill.part_3_min  AS "ss_p3_min",
        support_skill.part_3_max  AS "ss_p3_max",
        support_skill.part_4_min  AS "ss_p4_min",
        support_skill.part_4_max  AS "ss_p4_max",
        support_skill.part_5_min  AS "ss_p5_min",
        support_skill.part_5_max  AS "ss_p5_max",
        support_skill.part_6_min  AS "ss_p6_min",
        support_skill.part_6_max  AS "ss_p6_max",
        support_skill.part_7_min  AS "ss_p7_min",
        support_skill.part_7_max  AS "ss_p7_max",
        support_skill.part_8_min  AS "ss_p8_min",
        support_skill.part_8_max  AS "ss_p8_max",
        support_skill.part_9_min  AS "ss_p9_min",
        support_skill.part_9_max  AS "ss_p9_max",
        support_skill.part_10_min AS "ss_p10_min",
        support_skill.part_10_max AS "ss_p10_max"
    FROM
        accessories
    LEFT JOIN
        skills.passive_skill support_skill ON accessories.skill_id = support_skill.id
    WHERE
        accessories.id IN ({param});"""

adventure_books = """
    SELECT
        id,
        category,
        chapter_name,
        episode,
        sub_category,
        label,
        display_name
    FROM
        adventure_books
    WHERE
        adventure_books.id IN ({param});"""

brave_system_components = """
    SELECT
        id,
        name,
        description
    FROM
        brave_system_components
    WHERE
        brave_system_components.id IN ({param});"""

# bingo_sheets = """
#     SELECT
#         bingo_sheets.id,
#     	cartoon_chapters.title,
#     	start_at
#     FROM
#     	bingo_sheets
#     LEFT JOIN cartoon_chapters ON
#     	bingo_sheets.id = cartoon_chapters.id
#     WHERE
#         bingo_sheets.id IN ({param});"""

cartoon_stories = """
    SELECT
        cartoon_stories.id,
        cartoon_chapters.title AS chapter_title,
        cartoon_stories.title AS story_title,
    	bingo_sheets.start_at
    FROM
    	cartoon_stories
    LEFT JOIN cartoon_chapters ON
    	cartoon_stories.cartoon_chapter_id = cartoon_chapters.id
    LEFT JOIN bingo_sheets ON
        cartoon_stories.cartoon_chapter_id = bingo_sheets.id
    WHERE
        cartoon_stories.id IN ({param});"""

characters = """
    SELECT
        id,
        name,
        cv_name
    FROM
        characters
    WHERE
        characters.id IN ({param});"""

club_orders = """
    SELECT
        club_orders.id,
        club_orders.title,
        description,
        rarity,
        duration,
        reward_1.title AS reward_1,
        reward_2.title AS reward_2,
        reward_3.title AS reward_3,
        familiarity_exp,
        expired_at
    FROM
        club_orders
    LEFT JOIN 
        club_order_reward_boxes reward_1 ON club_orders.reward_box_1_id = reward_1.id
    LEFT JOIN 
        club_order_reward_boxes reward_2 ON club_orders.reward_box_2_id = reward_2.id
    LEFT JOIN 
        club_order_reward_boxes reward_3 ON club_orders.reward_box_3_id = reward_3.id
    WHERE
        club_orders.id IN ({param});"""


noodle_cooking_characters = """
    SELECT
        noodle_cooking_characters.id,
        target.name AS target_character,
        target_message,
        target_special_message,
        cooking.name AS cooking_character,
        cooking_message,
        cooking_special_message
    FROM
        noodle_cooking_characters
    LEFT JOIN 
        characters.characters target ON noodle_cooking_characters.target_character_id = target.id
    LEFT JOIN 
        characters.characters cooking ON noodle_cooking_characters.cooking_character_id = cooking.id
    WHERE
        noodle_cooking_characters.id IN ({param});"""

event_items = """
    SELECT
        event_items.id,
        special_chapters.name AS chapter,
        event_items.content_id,
        event_items.name,
        event_items.rarity
    FROM
        event_items
    LEFT JOIN
        special_chapters ON event_items.special_chapter_id = special_chapters.id
    WHERE
        event_items.id IN ({param});"""

special_attack_characters = """
    SELECT
        special_attack_characters.id,
        chapter.name AS chapter,
        character.name AS character,
        special_attack_characters.start_at,
        special_attack_characters.end_at
    FROM
        special_attack_characters
	LEFT JOIN
		special_chapters chapter ON special_attack_characters.special_chapter_id = chapter.id
    LEFT JOIN
        characters.characters character ON special_attack_characters.character_id = character.id
    WHERE
        special_attack_characters.id IN ({param});"""

special_episode_conditions = """
    SELECT
        special_episode_conditions.id,
		special_chapters.name AS chapter,
        special_episodes.name AS episode,
        special_episode_conditions.start_at,
        special_episode_conditions.end_at
    FROM
        special_episode_conditions
    LEFT JOIN
        special_episodes ON special_episode_conditions.special_episode_id = special_episodes.id
    LEFT JOIN
        special_chapters ON special_episodes.special_chapter_id = special_chapters.id
    WHERE
        special_episode_conditions.id IN ({param});"""

gachas = """
    SELECT
    	gachas.id,
    	gachas.name,
    	gachas.description,
    	gachas.kind,
    	gachas.step_up_loop,
    	gachas.special_get,
        gachas.special_get_count,
        gachas.special_save_rarity,
        gachas.special_select_gacha,
        gachas.select_count,
        gachas.special_select,
        gachas.min_user_level,
        gachas.max_user_level,
        gachas.count_down_gacha,
        gachas.start_at,
        gachas.end_at,
        gachas.skip_type
    FROM
    	gachas
    WHERE
        gachas.id IN ({param});"""

gacha_tickets = """
    SELECT
        gacha_tickets.id,
        gacha_tickets.name AS ticket,
        gacha_tickets.gacha_kind,
        gacha_tickets.consumption_resource_id,
        gachas.name AS gacha_name,
        gachas.description AS gacha_description
    FROM
        gacha_tickets
    LEFT JOIN
        gachas ON gachas.id = gacha_tickets.gacha_id
    WHERE
        gacha_tickets.id IN ({param});"""

gifts = """
    SELECT
        gifts.id,
        gifts.title,
        gifts.quantity
    FROM
	    gifts
    WHERE
        gifts.id IN ({param});"""

title_items = """
    SELECT
        title_items.id,
        title_items.name,
        title_items.description
    FROM
	    title_items
    WHERE
        title_items.id IN ({param});"""

login_bonus_sheets = """
    SELECT
        login_bonus_sheets.id,
        login_bonus_sheets.start_at,
        login_bonus_sheets.end_at,
        login_bonus_sheets.next_sheet_id,
        login_bonus_sheets.comeback_date
    FROM
        login_bonus_sheets
    WHERE
        login_bonus_sheets.id IN ({param});"""

episodes = """
    SELECT
        episodes.id,
        chapter.name AS chapter,
        episodes.name AS episode
    FROM
        episodes
    LEFT JOIN
		chapters chapter ON episodes.chapter_id = chapter.id
    WHERE
        episodes.id IN ({param});"""

active_skill = """
    SELECT
        active_skill.id,
    	active_skill.name       AS active_skill,
        active_skill.detail     AS as_detail,
        active_skill.cost       AS as_cost,
        active_skill.cool_time  AS as_cool_time,
        active_skill.part_1_min AS as_p1_min,
        active_skill.part_1_max AS as_p1_max,
        active_skill.part_2_min AS as_p2_min,
        active_skill.part_2_max AS as_p2_max,
        active_skill.part_3_min AS as_p3_min,
        active_skill.part_3_max AS as_p3_max,
        active_skill.part_4_min AS as_p4_min,
        active_skill.part_4_max AS as_p4_max,
        active_skill.part_5_min AS as_p5_min,
        active_skill.part_5_max AS as_p5_max,
        active_skill.part_6_min AS as_p6_min,
        active_skill.part_6_max AS as_p6_max,
        active_skill.part_7_min AS as_p7_min,
        active_skill.part_7_max AS as_p7_max,
        active_skill.part_8_min AS as_p8_min,
        active_skill.part_8_max AS as_p8_max,
        active_skill.part_9_min AS as_p9_min,
        active_skill.part_9_max AS as_p9_max,
        active_skill.part_10_min AS as_p10_min,
        active_skill.part_10_max AS as_p10_max
    FROM
        active_skill
    WHERE
        active_skill.id IN ({param});"""

area_skill = """
    SELECT
        area_skill.id,
    	area_skill.name     AS area_skill,
        area_skill.detail   AS as_detail,
        area_skill.area_type,
        skill_part.name     AS skill_part,
        area_skill.part_min AS as_p1_min,
        area_skill.part_max AS as_p1_max
    FROM
        area_skill
    LEFT JOIN
        skill_part ON area_skill.id = skill_part.id
    WHERE
        area_skill.id IN ({param});"""

passive_skill = """
    SELECT
        support_skill.id,
    	support_skill.name AS support_skill,
        support_skill.detail AS ss_detail,
        support_skill.part_1_min AS ss_p1_min,
        support_skill.part_1_max AS ss_p1_max,
        support_skill.part_2_min AS ss_p2_min,
        support_skill.part_2_max AS ss_p2_max,
        support_skill.part_3_min AS ss_p3_min,
        support_skill.part_3_max AS ss_p3_max,
        support_skill.part_4_min AS ss_p4_min,
        support_skill.part_4_max AS ss_p4_max,
        support_skill.part_5_min AS ss_p5_min,
        support_skill.part_5_max AS ss_p5_max,
        support_skill.part_6_min AS ss_p6_min,
        support_skill.part_6_max AS ss_p6_max,
        support_skill.part_7_min AS ss_p7_min,
        support_skill.part_7_max AS ss_p7_max,
        support_skill.part_8_min AS ss_p8_min,
        support_skill.part_8_max AS ss_p8_max,
        support_skill.part_9_min AS ss_p9_min,
        support_skill.part_9_max AS ss_p9_max,
        support_skill.part_10_min AS ss_p10_max,
        support_skill.part_10_max AS ss_p10_max
    FROM
        passive_skill support_skill
    WHERE
        support_skill.id IN ({param});"""

skill_part = """
    SELECT
        skill_part.id,
        skill_part.name,
        skill_part.part_type,
        skill_part.attribute,
        skill_part.add_sp_attribute,
        skill_part.add_sp_value,
        skill_part.attack_type,
        skill_part.character_type,
        skill_part.rarity_type,
        skill_part.area_type,
        skill_part.target_side,
        skill_part.buff_type,
        skill_part.buff_status,
        skill_part.value_type,
        skill_part.value,
        skill_part.hit_min,
        skill_part.hit_max,
        skill_part.width,
        skill_part.height,
        skill_part.angle,
        skill_part.move_x,
        skill_part.effect_time,
        skill_part.zoon_id,
        skill_part.area_id
    FROM
        skill_part
    WHERE
        skill_part.id IN ({param});"""

zoon_skill = """
    SELECT
        zoon_skill.id,
        zoon_skill.name AS zoon_skill,
        zoon_skill.detail,
		skill_part.name AS part,
        zoon_skill.part_min,
        zoon_skill.part_max
    FROM
        zoon_skill
    LEFT JOIN
        skill_part ON zoon_skill.part = skill_part.id
    WHERE
       zoon_skill.id IN ({param});"""