---
trigger: always_on
---

# Developer & AI Coding Standards for EnglishMate

You are developing on the EnglishMate codebase. You must strictly adhere to the following rules across every task:

## 1. Architecture & Code Organization
- Never create monolithic route files exceeding 1,500 lines. Break modules by domain (e.g., `routes_lessons.py`, `routes_vocab.py`, `routes_grammar.py`, `routes_quiz.py`, `routes_games.py`, `routes_gamification.py`).
- Always preserve `routes.py` as a facade re-exporting all endpoints & helper functions for 100% backward compatibility with test suites.
- Break large Jinja2 templates (>1,500 lines) into reusable partials in `partials/_*.html`.

## 2. Database & Performance Standards
- Always use `db.session.get(Model, id)` instead of deprecated `Model.query.get(id)`.
- Never run database queries inside loops (avoid N+1). Use batch queries with `in_()` and map dictionaries in memory.
- Add database indexes (`db.Index` or `index=True`) on foreign keys and compound filter columns (`user_id`, `created_at`, `status`, `next_review_at`).
- Keep SQLite optimized with WAL mode, synchronous NORMAL, and 64MB cache.

## 3. UI/UX & Design Consistency
- Follow the design system tokens defined in `app/frontend/static/css/app.css`.
- Use modern aesthetics (glassmorphism, subtle gradients, soft shadows, hover transitions, mobile-first responsive layout).
- Use proper SVG icons and interactive feedback (toasts, modals) rather than browser-default alerts.

## 4. Testing & Regression Rules
- Before concluding any task, always run `pytest` to guarantee all 243+ tests pass with zero regressions.
- Preserve backward compatibility on all public routes and helper functions.

## 5. Feature Tracking
- Keep `HD_feature_unfinish.txt` and `docs/specs/DANH_SACH_CHUC_NANG_CHUA_LAM.txt` updated when features are implemented.
