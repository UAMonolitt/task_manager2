from pydantic import BaseModel, Field

class SGetBestPrice(BaseModel):
    search: str| None = None
    max_results: int| None = None

class SSAveToList(BaseModel):
    user_id: int 
    bearer: str
    task_ids: list[tuple[int,int]] #tasks_ids = [(5095, 2), (2109, 1)] where 5095 and 2109 is ids and 2 and 1 is quantity
    note: str|None = None
