import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from smartodoo.core.docker_hub import DockerHubFetcher

@pytest.mark.asyncio
async def test_get_odoo_tags_success(mocker):
    """Sprawdzenie czy fetcher poprawnie transformuje strukturę jsona po udanym strzale do API"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"name": "16.0"}, {"name": "17.0"}, {"name": "latest"}]
    }
    mock_response.raise_for_status.return_value = None
    
    mock_get = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.get", new=mock_get)
    
    fetcher = DockerHubFetcher()
    tags = await fetcher.get_odoo_tags()
    
    assert len(tags) == 3
    assert "17.0" in tags
    # Sprawdzenie czy do URL doklejane jest library/odoo:
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "library/odoo/tags" in args[0]

@pytest.mark.asyncio
async def test_get_odoo_tags_failure(mocker):
    """Sprawdzenie czy błąd API nie wywala konsoli, a zwraca po prostu pustą listę"""
    mock_get = AsyncMock(side_effect=httpx.RequestError("No Internet", request=MagicMock()))
    mocker.patch("httpx.AsyncClient.get", new=mock_get)
    
    fetcher = DockerHubFetcher()
    tags = await fetcher.get_odoo_tags()
    
    assert tags == []
