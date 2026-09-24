# Database Schema

Schema extracted from `instance/englishmate.db` (SQLite). Notation: `PK` = primary key, `NN` = NOT NULL.

## audit_log
- `id` INTEGER PK
- `user_id` INTEGER
- `action` VARCHAR(100) NN
- `target_type` VARCHAR(50)
- `target_id` VARCHAR(50)
- `details` TEXT
- `ip_address` VARCHAR(45)
- `created_at` DATETIME NN

## badge
- `id` INTEGER PK
- `code` VARCHAR(50) NN
- `name` VARCHAR(100) NN
- `description` VARCHAR(255) NN
- `icon` VARCHAR(50) NN
- `category` VARCHAR(50) NN, default `GENERAL`
- `xp_reward` INTEGER NN, default `50`
- `req_type` VARCHAR(50) NN
- `req_value` INTEGER NN, default `1`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## challenge
- `id` INTEGER PK
- `code` VARCHAR(50) NN
- `title` VARCHAR(150) NN
- `description` VARCHAR(255) NN
- `icon` VARCHAR(50) NN, default `🎯`
- `action_type` VARCHAR(50) NN
- `target` INTEGER NN, default `1`
- `xp_reward` INTEGER NN, default `30`
- `period` VARCHAR(20) NN, default `DAILY`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## daily_activity
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `activity_date` DATE NN
- `completed_lessons` INTEGER NN
- `goal_completed` BOOLEAN NN

## exam
- `id` INTEGER PK NN
- `category` VARCHAR(50) NN
- `title` VARCHAR(255) NN
- `duration` INTEGER NN
- `is_active` BOOLEAN
- `created_at` DATETIME NN
- `duration_minutes` INTEGER, default `15`
- `difficulty` VARCHAR(20), default `Medium`
- `question_bank` VARCHAR(80), default `General`
- `selection_type` VARCHAR(20), default `random`
- `selected_question_ids` TEXT
- `question_count` INTEGER, default `10`
- `is_published` BOOLEAN, default `1`
- `updated_at` DATETIME

## exam_answer_detail
- `id` INTEGER PK NN
- `submission_id` INTEGER NN
- `question_id` INTEGER NN
- `user_response` JSON
- `is_correct` BOOLEAN
- `score` FLOAT NN

## exam_question
- `id` INTEGER PK NN
- `exam_id` INTEGER NN
- `skill` VARCHAR(50)
- `part` VARCHAR(50)
- `type` VARCHAR(50) NN
- `question_text` TEXT
- `option_a` VARCHAR(255)
- `option_b` VARCHAR(255)
- `option_c` VARCHAR(255)
- `option_d` VARCHAR(255)
- `correct_answer` VARCHAR(255)
- `media_info` JSON
- `transcript` TEXT
- `explanation` TEXT

## exam_submission
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `exam_id` INTEGER NN
- `total_score` FLOAT NN
- `status` VARCHAR(50) NN
- `created_at` DATETIME NN
- `completed_at` DATETIME

## flashcard_item
- `id` INTEGER PK NN
- `set_id` INTEGER NN
- `term` VARCHAR(500) NN
- `definition` TEXT NN
- `image_url` VARCHAR(500)
- `order` INTEGER NN

## flashcard_progress
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `item_id` INTEGER NN
- `is_known` BOOLEAN NN
- `review_count` INTEGER NN
- `last_reviewed_at` DATETIME NN
- `srs_level` INTEGER NN, default `1`
- `next_review_at` DATETIME, default `CURRENT_TIMESTAMP`

## flashcard_set
- `id` INTEGER PK NN
- `title` VARCHAR(200) NN
- `description` TEXT
- `is_public` BOOLEAN NN
- `user_id` INTEGER NN
- `created_at` DATETIME NN
- `updated_at` DATETIME NN

## game_session
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `session_id` VARCHAR(64) NN
- `game_type` VARCHAR(50) NN
- `total_questions` INTEGER NN
- `correct_answers` INTEGER NN
- `accuracy_rate` FLOAT NN
- `duration_seconds` INTEGER NN
- `created_at` DATETIME NN

## grammar_error_log
- `id` INTEGER PK
- `user_id` INTEGER NN
- `question_id` INTEGER NN
- `attempt_id` INTEGER
- `user_answer` VARCHAR(1) NN
- `correct_answer` VARCHAR(1) NN
- `is_resolved` BOOLEAN NN, default `0`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`
- `updated_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## grammar_exercise_attempt
- `id` INTEGER PK
- `user_id` INTEGER NN
- `topic_id` INTEGER
- `difficulty` VARCHAR(20) NN, default `Easy`
- `question_count` INTEGER NN, default `10`
- `score` INTEGER NN, default `0`
- `total_questions` INTEGER NN, default `10`
- `duration_seconds` INTEGER NN, default `0`
- `completed_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## grammar_progress
- `id` INTEGER PK
- `user_id` INTEGER NN
- `topic_id` INTEGER NN
- `is_completed` BOOLEAN NN, default `0`
- `is_favorite` BOOLEAN NN, default `0`
- `completed_at` DATETIME
- `updated_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## grammar_rule
- `id` INTEGER PK
- `title` VARCHAR(160) NN
- `category` VARCHAR(80) NN
- `summary` VARCHAR(280) NN
- `explanation` TEXT NN
- `examples` TEXT NN
- `exceptions` TEXT
- `common_errors` TEXT
- `quick_table_html` TEXT
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`
- `updated_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## grammar_rule_bookmark
- `id` INTEGER PK
- `user_id` INTEGER NN
- `rule_id` INTEGER NN
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## grammar_topic
- `id` INTEGER PK
- `title` VARCHAR(160) NN
- `category` VARCHAR(80) NN
- `level` VARCHAR(2) NN
- `difficulty` VARCHAR(20) NN, default `Easy`
- `summary` VARCHAR(280) NN
- `rule_explanation` TEXT NN
- `examples_json` TEXT NN
- `common_mistakes` TEXT
- `tips_tricks` TEXT
- `related_topic_ids` VARCHAR(100)
- `is_active` BOOLEAN NN, default `1`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`
- `updated_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## lesson
- `id` INTEGER PK NN
- `title` VARCHAR(160) NN
- `level` VARCHAR(2) NN
- `skill` VARCHAR(30) NN
- `short_description` VARCHAR(280) NN
- `content` TEXT NN
- `examples` TEXT NN
- `is_active` BOOLEAN NN
- `created_at` DATETIME NN
- `updated_at` DATETIME NN
- `thumbnail_url` VARCHAR(255)
- `view_count` INTEGER NN, default `0`

## lesson_bookmark
- `id` INTEGER PK
- `user_id` INTEGER NN
- `lesson_id` INTEGER NN
- `section_index` INTEGER NN, default `1`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## lesson_favorite
- `id` INTEGER PK
- `user_id` INTEGER NN
- `lesson_id` INTEGER NN
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## lesson_note
- `id` INTEGER PK
- `user_id` INTEGER NN
- `lesson_id` INTEGER NN
- `content` TEXT NN
- `updated_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## lesson_progress
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `lesson_id` INTEGER NN
- `completed_at` DATETIME NN

## lesson_report
- `id` INTEGER PK
- `user_id` INTEGER NN
- `lesson_id` INTEGER NN
- `reason` VARCHAR(100) NN
- `details` TEXT
- `status` VARCHAR(20) NN, default `PENDING`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## permission
- `id` INTEGER PK
- `name` VARCHAR(64) NN
- `description` VARCHAR(255)
- `category` VARCHAR(50) NN, default `General`

## question
- `id` INTEGER PK NN
- `question_text` VARCHAR(500) NN
- `option_a` VARCHAR(200) NN
- `option_b` VARCHAR(200) NN
- `option_c` VARCHAR(200) NN
- `option_d` VARCHAR(200) NN
- `correct_option` VARCHAR(1) NN
- `explanation` VARCHAR(500) NN
- `level` VARCHAR(2) NN
- `topic` VARCHAR(80) NN
- `created_at` DATETIME NN

## quiz
- `id` INTEGER PK
- `title` VARCHAR(160) NN
- `category` VARCHAR(80) NN
- `level` VARCHAR(2) NN
- `skill` VARCHAR(30) NN
- `difficulty` VARCHAR(20) NN, default `Medium`
- `description` VARCHAR(280) NN
- `question_count` INTEGER NN, default `10`
- `duration_minutes` INTEGER NN, default `15`
- `view_count` INTEGER NN, default `0`
- `is_active` BOOLEAN NN, default `1`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`
- `updated_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## quiz_attempt
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `level` VARCHAR(2) NN
- `topic` VARCHAR(80) NN
- `score` INTEGER NN
- `total_questions` INTEGER NN
- `created_at` DATETIME NN
- `duration_seconds` INTEGER NN, default `0`

## quiz_attempt_answer
- `id` INTEGER PK NN
- `attempt_id` INTEGER NN
- `question_id` INTEGER NN
- `selected_option` VARCHAR(1)
- `is_correct` BOOLEAN NN

## role
- `id` INTEGER PK
- `name` VARCHAR(50) NN
- `description` VARCHAR(255)
- `is_custom` BOOLEAN NN, default `0`
- `parent_id` INTEGER

## role_permission
- `id` INTEGER PK
- `role_id` INTEGER NN
- `permission_id` INTEGER NN

## toeic_attempt
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `test_id` INTEGER NN
- `score` INTEGER NN
- `total_questions` INTEGER NN
- `time_spent` INTEGER NN
- `created_at` DATETIME NN
- `completed_at` DATETIME
- `is_submitted` BOOLEAN NN

## toeic_attempt_answer
- `id` INTEGER PK NN
- `attempt_id` INTEGER NN
- `question_id` INTEGER NN
- `selected_option` VARCHAR(1)
- `is_correct` BOOLEAN NN

## toeic_passage
- `id` INTEGER PK NN
- `test_id` INTEGER NN
- `part` INTEGER NN
- `passage_text` TEXT NN

## toeic_question
- `id` INTEGER PK NN
- `test_id` INTEGER NN
- `passage_id` INTEGER
- `part` INTEGER NN
- `question_number` INTEGER NN
- `question_text` VARCHAR(500)
- `option_a` VARCHAR(200) NN
- `option_b` VARCHAR(200) NN
- `option_c` VARCHAR(200) NN
- `option_d` VARCHAR(200) NN
- `correct_option` VARCHAR(1) NN
- `explanation` TEXT NN

## toeic_test
- `id` INTEGER PK NN
- `title` VARCHAR(160) NN
- `created_at` DATETIME NN

## user
- `id` INTEGER PK NN
- `username` VARCHAR(40) NN
- `email` VARCHAR(120) NN
- `password_hash` VARCHAR(255) NN
- `role` VARCHAR(10) NN
- `is_active` BOOLEAN NN
- `created_at` DATETIME NN
- `updated_at` DATETIME NN
- `current_streak` INTEGER NN, default `0`
- `longest_streak` INTEGER NN, default `0`
- `last_activity_date` DATE
- `is_email_verified` BOOLEAN NN, default `0`
- `email_verification_code` VARCHAR(6)
- `email_verification_expiry` DATETIME
- `oauth_provider` VARCHAR(20)
- `oauth_id` VARCHAR(100)
- `failed_login_attempts` INTEGER NN, default `0`
- `lockout_until` DATETIME
- `last_login_at` DATETIME
- `reset_token` VARCHAR(100)
- `reset_token_expiry` DATETIME
- `full_name` VARCHAR(100)
- `avatar` VARCHAR(255), default `default_avatar.png`
- `pending_email` VARCHAR(120)
- `pending_email_otp` VARCHAR(6)
- `pending_email_expiry` DATETIME
- `daily_vocab_goal` INTEGER NN, default `20`
- `vocab_review_priority` VARCHAR(20) NN, default `due_date`
- `vocab_auto_play_audio` BOOLEAN NN, default `1`
- `vocab_accent` VARCHAR(10) NN, default `en-US`
- `vocab_display_mode` VARCHAR(20) NN, default `flashcard`
- `vocab_review_time` VARCHAR(20) NN, default `anytime`
- `vocab_srs_algorithm` VARCHAR(20) NN, default `standard`
- `vocab_notify_review_due` BOOLEAN NN, default `1`
- `exam_default_type` VARCHAR(50) NN, default `TOEIC`
- `exam_default_time_limit` INTEGER NN, default `120`
- `exam_show_timer` BOOLEAN NN, default `1`
- `exam_allow_pause` BOOLEAN NN, default `1`
- `exam_show_realtime_score` BOOLEAN NN, default `0`
- `exam_auto_submit` BOOLEAN NN, default `1`
- `exam_sound_effects` BOOLEAN NN, default `1`
- `xp` INTEGER NN, default `0`
- `level` INTEGER NN, default `1`
- `daily_goal_xp` INTEGER NN, default `50`
- `daily_reward_claimed_date` DATE
- `level_start_date` DATE

## user_badge
- `id` INTEGER PK
- `user_id` INTEGER NN
- `badge_id` INTEGER NN
- `unlocked_at` DATETIME NN, default `CURRENT_TIMESTAMP`

## user_challenge
- `id` INTEGER PK
- `user_id` INTEGER NN
- `challenge_id` INTEGER NN
- `current_progress` INTEGER NN, default `0`
- `is_completed` BOOLEAN NN, default `0`
- `is_claimed` BOOLEAN NN, default `0`
- `period_date` DATE NN
- `completed_at` DATETIME

## user_role
- `id` INTEGER PK
- `user_id` INTEGER NN
- `role_id` INTEGER NN
- `expires_at` DATETIME
- `created_at` DATETIME NN

## user_session
- `id` VARCHAR(64) PK
- `user_id` INTEGER NN
- `ip_address` VARCHAR(45)
- `user_agent` VARCHAR(255)
- `device_info` VARCHAR(100)
- `last_activity` DATETIME NN
- `created_at` DATETIME NN
- `is_active` BOOLEAN NN, default `1`

## vocabulary
- `id` INTEGER PK NN
- `word` VARCHAR(100) NN
- `pronunciation` VARCHAR(100) NN
- `part_of_speech` VARCHAR(30) NN
- `meaning_vi` VARCHAR(200) NN
- `example_en` VARCHAR(300) NN
- `example_vi` VARCHAR(300) NN
- `topic` VARCHAR(80) NN
- `level` VARCHAR(2) NN
- `created_at` DATETIME NN
- `updated_at` DATETIME NN
- `image_url` VARCHAR(255)
- `collocations` VARCHAR(300)
- `synonyms` VARCHAR(200)
- `antonyms` VARCHAR(200)

## vocabulary_progress
- `id` INTEGER PK NN
- `user_id` INTEGER NN
- `vocabulary_id` INTEGER NN
- `learned_count` INTEGER NN
- `review_count` INTEGER NN
- `last_reviewed_at` DATETIME NN
- `is_favorite` BOOLEAN NN, default `0`
- `is_skipped` BOOLEAN NN, default `0`
- `srs_level` INTEGER NN, default `1`
- `next_review_at` DATETIME, default `CURRENT_TIMESTAMP`
- `personal_notes` TEXT
- `custom_example` TEXT

## word_report
- `id` INTEGER PK
- `user_id` INTEGER NN
- `vocabulary_id` INTEGER NN
- `reason` VARCHAR(255) NN
- `status` VARCHAR(20) NN, default `PENDING`
- `created_at` DATETIME NN, default `CURRENT_TIMESTAMP`
