import uvicorn

from chore_master_api.config import get_chore_master_api_web_server_config
from chore_master_api.web_server.app import get_app
from modules.base.config import get_base_config

if __name__ == "__main__":
    base_config = get_base_config()
    chore_master_api_web_server_config = get_chore_master_api_web_server_config()
    uvicorn.run(
        f"{base_config.SERVICE_NAME}.entrypoints.{base_config.COMPONENT_NAME}:app",
        host="0.0.0.0",
        port=chore_master_api_web_server_config.PORT,
        reload=chore_master_api_web_server_config.UVICORN_AUTO_RELOAD,
        reload_dirs=["modules", f"{base_config.SERVICE_NAME}"],
    )
else:
    app = get_app()
