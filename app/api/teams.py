"""
團隊管理 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.team import Team, TeamCreate, TeamUpdate, TeamResponse
from app.models.database_models import Team as TeamDB
from app.services.lark_client import LarkClient

router = APIRouter(prefix="/teams", tags=["teams"])

def team_db_to_model(team_db: TeamDB) -> dict:
    """將資料庫團隊模型轉換為 API 回應字典"""
    from app.models.team import LarkRepoConfig, JiraConfig, TeamSettings
    
    lark_config = LarkRepoConfig(
        wiki_token=team_db.wiki_token,
        test_case_table_id=team_db.test_case_table_id
    )
    
    jira_config = None
    if team_db.jira_project_key:
        jira_config = JiraConfig(
            project_key=team_db.jira_project_key,
            default_assignee=team_db.default_assignee,
            issue_type=team_db.issue_type
        )
    
    settings = TeamSettings(
        enable_notifications=team_db.enable_notifications if team_db.enable_notifications is not None else True,
        auto_create_bugs=team_db.auto_create_bugs if team_db.auto_create_bugs is not None else False,
        default_priority=team_db.default_priority.value if team_db.default_priority else "Medium"
    )
    
    return {
        "id": team_db.id,
        "name": team_db.name,
        "description": team_db.description,
        "lark_config": lark_config.dict(),
        "jira_config": jira_config.dict() if jira_config else None,
        "settings": settings.dict(),
        "status": team_db.status.value if team_db.status else "active",
        "created_at": team_db.created_at,
        "updated_at": team_db.updated_at,
        "test_case_count": team_db.test_case_count or 0,
        "last_sync_at": team_db.last_sync_at,
        "is_lark_configured": bool(team_db.wiki_token and team_db.test_case_table_id),
        "is_jira_configured": bool(team_db.jira_project_key)
    }

def team_model_to_db(team: TeamCreate) -> TeamDB:
    """將 API 團隊模型轉換為資料庫模型"""
    return TeamDB(
        name=team.name,
        description=team.description,
        wiki_token=team.lark_config.wiki_token,
        test_case_table_id=team.lark_config.test_case_table_id,
        jira_project_key=team.jira_config.project_key if team.jira_config else None,
        default_assignee=team.jira_config.default_assignee if team.jira_config else None,
        issue_type=team.jira_config.issue_type if team.jira_config else "Bug",
        enable_notifications=team.settings.enable_notifications if team.settings else True,
        auto_create_bugs=team.settings.auto_create_bugs if team.settings else False,
        default_priority=team.settings.default_priority if team.settings else "Medium",
        status=team.status if team.status else "active"
    )

@router.get("/")
async def get_teams(db: Session = Depends(get_db)):
    """取得所有團隊列表"""
    try:
        teams_db = db.query(TeamDB).all()
        if not teams_db:
            return []
        return [team_db_to_model(team) for team in teams_db]
    except Exception as e:
        print(f"Error loading teams: {e}")
        return []

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """新增一個團隊"""
    # 創建資料庫模型
    team_db = team_model_to_db(team)
    
    # 儲存到資料庫
    db.add(team_db)
    db.commit()
    db.refresh(team_db)
    
    return team_db_to_model(team_db)

@router.post("/validate", response_model=dict)
async def validate_lark_repo(team: TeamCreate):
    """驗證 Lark Repo 的連線"""
    try:
        # 創建 Lark Client 來驗證連線
        lark_client = LarkClient(
            app_id="cli_a8d1077685be102f",
            app_secret="kS35CmIAjP5tVib1LpPIqUkUJjuj3pIt"
        )
        
        # 設定 wiki token
        lark_client.set_wiki_token(team.lark_config.wiki_token)
        
        # 嘗試獲取表格資訊來驗證連線
        fields = lark_client.get_table_fields(team.lark_config.test_case_table_id)
        
        return {
            "valid": True,
            "message": "Lark Repo 連線驗證成功"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Lark Repo 連線驗證失敗: {str(e)}"
        }

@router.get("/{team_id}")
async def get_team(team_id: int, db: Session = Depends(get_db)):
    """根據 ID 取得特定團隊"""
    team_db = db.query(TeamDB).filter(TeamDB.id == team_id).first()
    
    if not team_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到團隊 ID {team_id}"
        )
    
    return team_db_to_model(team_db)

@router.put("/{team_id}")
async def update_team(team_id: int, team_update: TeamUpdate, db: Session = Depends(get_db)):
    """更新指定的團隊"""
    team_db = db.query(TeamDB).filter(TeamDB.id == team_id).first()
    
    if not team_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到團隊 ID {team_id}"
        )
    
    # 更新資料庫模型
    if team_update.name is not None:
        team_db.name = team_update.name
    
    if team_update.description is not None:
        team_db.description = team_update.description
    
    if team_update.lark_config is not None:
        team_db.wiki_token = team_update.lark_config.wiki_token
        team_db.test_case_table_id = team_update.lark_config.test_case_table_id
    
    if team_update.jira_config is not None:
        team_db.jira_project_key = team_update.jira_config.project_key
        team_db.default_assignee = team_update.jira_config.default_assignee
        team_db.issue_type = team_update.jira_config.issue_type
    
    if team_update.settings is not None:
        team_db.enable_notifications = team_update.settings.enable_notifications
        team_db.auto_create_bugs = team_update.settings.auto_create_bugs
        team_db.default_priority = team_update.settings.default_priority
    
    if team_update.status is not None:
        team_db.status = team_update.status
    
    # 提交更新
    db.commit()
    db.refresh(team_db)
    
    return team_db_to_model(team_db)

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: int, db: Session = Depends(get_db)):
    """刪除指定的團隊"""
    team_db = db.query(TeamDB).filter(TeamDB.id == team_id).first()
    
    if not team_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到團隊 ID {team_id}"
        )
    
    db.delete(team_db)
    db.commit()