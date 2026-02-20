import httpx
from typing import Any, Dict, Optional, List
from .config import load_config

class DocCompassClient:
    """Async HTTP backend client using httpx."""
    
    def __init__(self, backend_url: Optional[str] = None):
        if not backend_url:
            config = load_config()
            backend_url = config.get("backend_url", "http://localhost:8000")
        self.base_url = backend_url.rstrip("/")
        
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()
            
    # --- Ingestion ---
    
    async def start_ingestion(self, web_url: str, crawl_depth: Optional[int] = None, include_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None) -> Dict:
        payload = {"web_url": web_url}
        if crawl_depth is not None:
            payload["crawl_depth"] = crawl_depth
        if include_patterns:
            payload["include_patterns"] = include_patterns
        if exclude_patterns:
            payload["exclude_patterns"] = exclude_patterns
        return await self._request("POST", "/documentation/ingestion", json=payload)
        
    async def list_ingestion_jobs(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Dict]:
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        return await self._request("GET", "/documentation/ingestion", params=params)
        
    async def get_ingestion_job(self, job_id: str) -> Dict:
        return await self._request("GET", f"/documentation/ingestion/{job_id}")
        
    async def stop_ingestion_job(self, job_id: str) -> Dict:
        return await self._request("POST", "/documentation/ingestion/stop", json={"job_id": job_id})
        
    # --- Documentation ---
    
    async def list_documentation(self, skip: int = 0, limit: int = 100) -> Dict:
        params = {"offset": skip, "limit": limit}  # Based on MCP tool list_documentations which actually proxies to backend /documentation
        # Wait, the backend endpoint is /documentation -> let's map exactly to it.
        return await self._request("GET", "/documentation", params=params)
        
    async def search_documentation(self, doc_id: str, query: str) -> Dict:
        params = {"q": query}
        return await self._request("GET", f"/documentation/{doc_id}/search", params=params)
        
    async def get_documentation_tree(self, doc_id: str) -> Dict:
        return await self._request("GET", f"/documentation/{doc_id}/tree")
        
    async def get_section_content(self, doc_id: str, path: str) -> Dict:
        params = {"path": path}
        return await self._request("GET", f"/documentation/{doc_id}/content", params=params)

