from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas import Item, ItemCreate, ProfileRequest, ProfileResponse
from app.services import profile_service, store

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "project": settings.project_name,
    }


@router.get("/items", response_model=list[Item], tags=["Items"])
def list_items() -> list[Item]:
    return list(store.list_items())


@router.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item_in: ItemCreate) -> Item:
    return store.create_item(item_in)


@router.get("/items/{item_id}", response_model=Item, tags=["Items"])
def get_item(item_id: int) -> Item:
    item = store.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int) -> None:
    deleted = store.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.post("/profile", response_model=ProfileResponse, tags=["Profile"])
async def get_profile(request: ProfileRequest) -> ProfileResponse:
    """
    Get player profile by Riot ID and region.
    
    Flow:
    1. Queries Lambda function which checks DynamoDB for cached profile
    2. If found (200), returns the cached data
    3. If not found (404):
       - Calls get-uuid API to fetch profile data
       - Saves to DynamoDB asynchronously (fire-and-forget)
       - Returns profile information
    
    Args:
        request: ProfileRequest containing:
            - riot_id: Player's Riot ID (e.g., 'cant type#1998')
            - region: Server region (e.g., 'na1', 'euw1', 'kr')
    
    Returns:
        ProfileResponse with player profile information
        
    Example:
        POST /api/profile
        {
            "riot_id": "cant type#1998",
            "region": "na1"
        }
    """
    return await profile_service.get_profile(request)

