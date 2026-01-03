"""
Pydantic models for requests and responses.

This module exports all request/response models used by the API.
"""

from cortex.models.requests import (
    CalculateDistanceRequest,
    ChatMessage,
    ChatRequest,
    CorrectClassificationRequest,
    CreateMapDataRequest,
    EntityConnectionRequest,
    EntityExtractionRequest,
    EntitySearchRequest,
    FeedTheBrainRequest,
    GeocodeRequest,
    GeoIntelChatRequest,
    GeoIntelChatResponse,
    GeoIntelLocationData,
    GeoIntelMarker,
    GeoIntelQuickAction,
    MediaSearchRequest,
    QuestionRequest,
    RelearnRequest,
    ReverseGeocodeRequest,
    ScrapeRequest,
    SearchByRegionRequest,
    SearchNearbyRequest,
    SmartMediaChatRequest,
    TableurRequest,
)

__all__ = [
    # Q&A / Chat
    "QuestionRequest",
    "ChatMessage",
    "ChatRequest",
    # Web Scraping
    "ScrapeRequest",
    # Media Agent
    "MediaSearchRequest",
    "SmartMediaChatRequest",
    # Router Management
    "CorrectClassificationRequest",
    "RelearnRequest",
    "FeedTheBrainRequest",
    "TableurRequest",
    # Entity Intelligence
    "EntitySearchRequest",
    "EntityExtractionRequest",
    "EntityConnectionRequest",
    # Geospatial
    "GeocodeRequest",
    "ReverseGeocodeRequest",
    "SearchNearbyRequest",
    "CalculateDistanceRequest",
    "SearchByRegionRequest",
    "CreateMapDataRequest",
    # GeoIntel Chat
    "GeoIntelMarker",
    "GeoIntelQuickAction",
    "GeoIntelLocationData",
    "GeoIntelChatRequest",
    "GeoIntelChatResponse",
]
