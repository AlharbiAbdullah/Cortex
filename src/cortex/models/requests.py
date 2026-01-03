"""
Pydantic request models for API endpoints.

This module contains all request/response models used by the API routers.
Uses Pydantic v2 with strict validation.
"""

from typing import Any

from pydantic import BaseModel, Field


# ==================== Q&A / Chat Models ====================
class QuestionRequest(BaseModel):
    """Request model for Q&A endpoint."""

    question: str = Field(..., min_length=1, description="The question to answer")
    context: str = Field(default="", description="Additional context for the question")
    use_rag: bool = Field(default=False, description="Whether to use RAG for context")
    model_name: str | None = Field(default=None, description="LLM model to use")


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, description="User message")
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in the conversation"
    )
    use_rag: bool = Field(default=True, description="Whether to use RAG for context")
    model_name: str | None = Field(default=None, description="LLM model to use")
    expert: str = Field(default="general", description="Expert persona to use")


# ==================== Web Scraping Models ====================
class ScrapeRequest(BaseModel):
    """Request model for web scraping endpoint."""

    url: str = Field(..., description="URL to scrape")
    name: str = Field(default="Custom Source", description="Name for the source")


# ==================== Media Agent Models ====================
class MediaSearchRequest(BaseModel):
    """Request model for media search endpoint."""

    query: str = Field(..., min_length=1, description="Search query")
    country: str = Field(default="israel", description="Country filter")
    max_sources: int = Field(default=5, ge=1, le=20, description="Maximum sources to return")


class SmartMediaChatRequest(BaseModel):
    """Request model for Smart Media conversational chat."""

    message: str = Field(..., min_length=1, description="User message")
    max_sources: int = Field(default=5, ge=1, le=20, description="Maximum sources to use")
    conversation_history: list[dict[str, Any]] | None = Field(
        default=None,
        description="Previous conversation history"
    )


# ==================== Router Management Models ====================
class CorrectClassificationRequest(BaseModel):
    """Request model for correcting document classification."""

    decision_id: int = Field(..., description="Routing decision ID to correct")
    corrected_classification: str = Field(..., min_length=1, description="Correct category")
    reviewer: str = Field(default="admin", description="Reviewer identifier")


class RelearnRequest(BaseModel):
    """Request model for re-learning document classification."""

    silver_key: str = Field(..., description="Document silver key")
    force_primary: str | None = Field(
        default=None,
        description="Force specific primary category"
    )
    force_categories: list[str] | None = Field(
        default=None,
        description="Force specific categories list"
    )


class FeedTheBrainRequest(BaseModel):
    """Request model for updating feed_the_brain tag."""

    silver_key: str = Field(..., description="Document silver key")
    feed_the_brain: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 to include in Q/A service, 0 to exclude"
    )


class TableurRequest(BaseModel):
    """Request model for updating tableur tag."""

    silver_key: str = Field(..., description="Document silver key")
    tableur: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 to process tabular data to Gold layer, 0 to skip"
    )


# ==================== Entity Intelligence Models ====================
class EntitySearchRequest(BaseModel):
    """Request model for entity search."""

    query: str = Field(..., min_length=1, description="Search query")
    entity_type: str | None = Field(default="Person", description="Entity type filter")
    query_type: str | None = Field(
        default="bio",
        description="Query type: bio, timeline, relationships, network, search"
    )


class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction from text."""

    text: str = Field(..., min_length=1, description="Text to extract entities from")
    silver_key: str | None = Field(default=None, description="Source document key")
    filename: str | None = Field(default=None, description="Source filename")


class EntityConnectionRequest(BaseModel):
    """Request model for finding entity connections."""

    entity1: str = Field(..., description="First entity name")
    entity2: str = Field(..., description="Second entity name")
    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum connection depth")


# ==================== Geospatial Models ====================
class GeocodeRequest(BaseModel):
    """Request model for geocoding a place name."""

    place_name: str = Field(..., min_length=1, description="Place name to geocode")
    country: str | None = Field(default=None, description="Country filter")


class ReverseGeocodeRequest(BaseModel):
    """Request model for reverse geocoding coordinates."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class SearchNearbyRequest(BaseModel):
    """Request model for searching nearby POIs."""

    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_km: float = Field(default=100, gt=0, description="Search radius in kilometers")
    poi_types: list[str] | None = Field(default=None, description="POI type filters")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


class CalculateDistanceRequest(BaseModel):
    """Request model for calculating distance between points."""

    point_a: Any = Field(..., description="First point: {lat, lon} or place name")
    point_b: Any = Field(..., description="Second point: {lat, lon} or place name")


class SearchByRegionRequest(BaseModel):
    """Request model for searching within a region."""

    region: Any = Field(
        ...,
        description="Region: name or {north, south, east, west} bounds"
    )
    poi_types: list[str] | None = Field(default=None, description="POI type filters")
    query: str | None = Field(default=None, description="Additional query filter")


class CreateMapDataRequest(BaseModel):
    """Request model for creating map data."""

    center: dict[str, float] = Field(..., description="Map center {lat, lon}")
    markers: list[dict[str, Any]] | None = Field(default=None, description="Map markers")
    zoom: int = Field(default=6, ge=1, le=20, description="Map zoom level")


# ==================== GeoIntel Chat Models ====================
class GeoIntelMarker(BaseModel):
    """A marker to display on the map."""

    id: str = Field(..., description="Unique marker ID")
    name: str = Field(..., description="Marker name/label")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    type: str = Field(
        ...,
        description="Marker type: airport, military, port, city, strategic, satellite, custom"
    )


class GeoIntelQuickAction(BaseModel):
    """A quick action button for follow-up queries."""

    action: str = Field(
        ...,
        description="Action type: satellite, nearby, copy, download, expand"
    )
    label: str = Field(..., description="Button label")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class GeoIntelLocationData(BaseModel):
    """Data for a single location."""

    name: str = Field(..., description="Location name")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    type: str | None = Field(default=None, description="Location type")
    distance_km: float | None = Field(default=None, ge=0, description="Distance in km")


class GeoIntelChatRequest(BaseModel):
    """Request model for GeoIntel chat endpoint."""

    message: str = Field(..., min_length=1, description="User message")
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation"
    )
    last_location: GeoIntelLocationData | None = Field(
        default=None,
        description="Last referenced location"
    )
    last_results: list[GeoIntelLocationData] | None = Field(
        default=None,
        description="Previous search results"
    )
    accumulated_markers: list[GeoIntelMarker] | None = Field(
        default=None,
        description="All markers from session"
    )
    session_id: str | None = Field(default=None, description="Session identifier")


class GeoIntelChatResponse(BaseModel):
    """Response model for GeoIntel chat endpoint."""

    success: bool = Field(..., description="Whether the request succeeded")
    type: str = Field(
        ...,
        description="Response type: coordinate, poi_list, satellite, distance, error, clarification"
    )
    message: str = Field(..., description="Response message")
    data: dict[str, Any] = Field(default_factory=dict, description="Response data")
    markers: list[GeoIntelMarker] = Field(default_factory=list, description="Map markers")
    quick_actions: list[GeoIntelQuickAction] = Field(
        default_factory=list,
        description="Available quick actions"
    )
    last_location: GeoIntelLocationData | None = Field(
        default=None,
        description="Last referenced location"
    )
    last_results: list[GeoIntelLocationData] = Field(
        default_factory=list,
        description="Current search results"
    )
    logs: list[str] = Field(default_factory=list, description="Processing logs")
    errors: list[str] = Field(default_factory=list, description="Error messages")
