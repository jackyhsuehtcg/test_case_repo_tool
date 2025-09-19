# Task List

## 1. User Model
- [ ] 1.1 在 `app/models/database_models.py` 中新增 `Role` ORM 模型，欄位：
  - `id`: Integer, primary key, autoincrement。
  - `name`: String(50), unique, nullable=False – 角色名稱（如 SUPER_ADMIN）。
  - `description`: String(200) – 角色說明。
- [ ] 1.2 定義 `User` ORM 模型：
  - `id`: Integer, primary key, autoincrement。
  - `lark_id`: String(255), unique, indexed, nullable=False – 用於對應 Lark contact。
  - `hashed_password`: String(128), nullable=False – bcrypt 雜湊值。
  - `role_id`: Integer, ForeignKey('roles.id'), nullable=False – 角色外鍵。
  - `team_id`: Integer, ForeignKey('teams.id'), nullable=True – 允許 Super Admin 無團隊限制，並在關聯中設置 `relationship('Team', back_populates='users')`。
  - `created_at`: DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False – 建立時間。
- [ ] 1.3 在 `database_models.py` 中加入 `__repr__` 與 `to_dict()` 方法，方便日誌與 API 輸出。
- [ ] 1.4 為 `User` 模型新增索引：`ix_user_lark_id`（唯一）與 `ix_user_team_id`（非唯一）。

## 1.5 Role Table
- [ ] 1.5.1 建立 `Role` ORM 模型，欄位：`id` (Integer, PK), `name` (String, unique), `description` (String)。
- [ ] 1.5.2 在 `User` 模型中加入 `role_id` ForeignKey('roles.id') 並建立關聯 `relationship('Role', back_populates='users')`。
- [ ] 1.5.3 為 `Role` 模型新增索引：`ix_role_name`（唯一）。

## 2. Migration
- [ ] 2.1 撰寫 Alembic migration：
  - `upgrade()`：先創建 `roles` 表（id, name, description），再創建 `users` 表，包含上述欄位、索引（`ix_user_lark_id`, `ix_user_team_id`）以及外鍵約束到 `teams.id` 與 `roles.id`。
  - `downgrade()`：刪除 `users` 表後再刪除 `roles` 表，確保在回滾時不影響其他表。
- [ ] 2.2 在 migration 檔案中加入 `depends_on` 或 `revision` 設定，並在 `env.py` 中設定 `target_metadata` 為 `database_models.Base.metadata`，以自動偵測模型變更。

## 3. Dependencies
- [ ] 3.1 安裝依賴：starlette-session, bcrypt, starlette-csrf
- [ ] 3.2 更新 requirements.txt 並執行 pip install

## 4. Auth Service
- [ ] 4.1 實作 `auth_service.py`：
  - login(username,password)
  - logout(session_id)
  - get_current_user(session_id)
  - hash_password(password)
  - verify_password(hash, password)
- [ ] 4.2 在 `auth_service.py` 中加入失敗次數鎖定邏輯（5 次失敗 15 分鐘）

## 5. Auth API
- [ ] 5.1 新增 auth API：/api/auth/login, /api/auth/logout, /api/auth/session

## 6. Session Middleware
- [ ] 6.1 在 `app/main.py` 加入 session middleware（starlette-session）
- [ ] 6.2 在 `app/main.py` 設定 session 儲存位置（檔案或 Redis）

## 7. API Role Checks
- [ ] 7.1 修改 test_cases API：
  - 在所有 CRUD 路由中加入 `Depends(get_current_user)`。
  - 使用 `check_role([Role.USER, Role.ADMIN, Role.SUPER_ADMIN])` 以允許 User、Admin、Super Admin。
  - 對更新與刪除路由使用 `check_role([Role.ADMIN, Role.SUPER_ADMIN])`。
- [ ] 7.2 針對其他受保護 API（test_runs, teams 等）做相同修改：
  - test_runs：CRUD 允許 User、Admin、Super Admin；讀取僅允許 Viewer。
  - teams：僅允許 Admin（屬於該團隊）或 Super Admin 執行管理操作，Viewer 只能查看。
  - attachments、jira 等需加入 `Depends(get_current_user)` 並根據角色限制存取。
- [ ] 7.3 修改 test_run_items API：
  - CRUD 允許 User、Admin、Super Admin；讀取僅允許 Viewer。
  - 限制更新/刪除僅 Admin 或 Super Admin。
- [ ] 7.4 修改 test_run_configs API：
  - 讀取允許所有角色；修改/新增/刪除僅 Admin 或 Super Admin。
- [ ] 7.5 修改 attachments API：
  - 上傳/刪除僅允許擁有者、Admin 或 Super Admin。
  - 下載允許所有已授權使用者；Viewer 只能下載。
- [ ] 7.6 修改 jira API：
  - 只實作票號查詢與搜尋（GET /api/jira/ticket/{ticket_id}、GET /api/jira/search）。
  - 不提供建立/更新/刪除或附件下載功能。

## 8. Templates
- [ ] 8.1 建立 login.html 模板：表單、CSRF token、錯誤訊息區域
- [ ] 8.2 在 base.html 加入 JS 以檢查 session，未登入時重導至 /login

## 9. JS Module
- [ ] 9.1 新增 auth.js：
  - fetch session info
  - hide/show UI 元件根據 role
  - 提供 logout 按鈕功能

## 10. Tests
- [ ] 10.1 撰寫單元測試：auth_service.login_success, login_fail, password_hash
- [ ] 10.2 撰寫整合測試：登入流程、session 續存、權限檢查

## 11. Role Permission Logic
- [ ] 11.1 定義 RolePermission enum，映射每個角色可執行的操作（CRUD、管理等）
- [ ] 11.2 實作 get_current_user 依賴：從 session 取得 user_id，查詢 User 模型並回傳；若不存在則拋出 HTTPException 401
- [ ] 11.3 實作 check_role(required_roles) 依賴：使用 get_current_user，檢查使用者角色是否在 required_roles，否則拋出 403
- [ ] 11.4 更新 test_cases API：對 CRUD 操作使用 Depends(check_role([Role.USER, Role.ADMIN, Role.SUPER_ADMIN]))；對刪除/更新僅允許 ADMIN 或 SUPER_ADMIN
- [ ] 11.5 更新 test_runs API：類似 11.4，確保 User 可 CRUD，Viewer 只能讀取
- [ ] 11.6 更新 team 管理 API：僅允許 ADMIN（屬於該團隊）或 SUPER_ADMIN 執行；其他角色 403
- [ ] 11.7 前端 auth.js 擴充：根據 session.role 隱藏/顯示 CRUD 按鈕、編輯欄位、分享功能

## 12. Team Visibility
- [ ] 12.1 修改 team 列表 API：僅回傳使用者所在團隊或已共享的團隊；若 Admin 不是該團隊，則不顯示其卡片
- [ ] 12.2 前端更新：在渲染團隊卡片時檢查是否有權限，否則不渲染或顯示「無權限」提示
