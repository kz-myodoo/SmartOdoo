import httpx
from typing import List, Optional

class DockerHubFetcher:
    """Asynchroniczny klient do odpytywania Docker Hub V2 API.
    Pozwala na bezzwłoczne ładowanie tagów bez wielowątkowości (threading).
    """
    def __init__(self, base_url: str = "https://hub.docker.com/v2/repositories"):
        self.base_url = base_url

    async def get_odoo_tags(self, limit: int = 50) -> List[str]:
        """Pobiera listę tagów dla oficjalnego obrazu Odoo z Docker Hub."""
        url = f"{self.base_url}/library/odoo/tags"
        params = {"page_size": limit}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Zwraca nazwy tagów filtrując brakujące lub zepsute odpowiedzi.
                tags = [item["name"] for item in data.get("results", []) if "name" in item]
                return tags
            except httpx.RequestError as e:
                # Bezpieczne łapanie połączęń - w wypadku braku internetu nie wywala głównego procesu
                return []
            except httpx.HTTPStatusError as e:
                return []
