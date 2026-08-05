from fastapi import FastAPI

from api.environments import router as environments_router
from api.health import router as health_router
from api.releases import router as releases_router
from api.runs import router as runs_router
from api.artifacts import router as artifacts_router
from api.baselines import router as baselines_router
from api.lineage import router as lineage_router
from api.difference import router as difference_router
from errors import install_error_handlers

app = FastAPI()
app.include_router(health_router)
app.include_router(releases_router)
app.include_router(environments_router)
app.include_router(runs_router)
app.include_router(artifacts_router)
app.include_router(baselines_router)
app.include_router(lineage_router)
app.include_router(difference_router)
install_error_handlers(app)
