from google.adk.tools import google_search
from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool
from research_pipeline.config.settings import settings


def build_search_tools() -> list:
    tools = [google_search]

    if settings.vertex_search_engine_id:
        vertex_search = VertexAiSearchTool(
            data_store_id=f"projects/{settings.google_cloud_project}/locations/global/collections/default_collection/dataStores/{settings.vertex_search_engine_id}"
        )
        tools.insert(0, vertex_search)

    return tools
