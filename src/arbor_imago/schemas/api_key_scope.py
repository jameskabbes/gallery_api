from pydantic import BaseModel
from arbor_imago import custom_types


class ApiKeyScopeAdminUpdate(BaseModel):
    pass


class ApiKeyScopeAdminCreate(BaseModel):
    api_key_id: custom_types.ApiKeyScope.api_key_id
    scope_id: custom_types.ApiKeyScope.scope_id
