from pydantic import BaseModel


class CatDetected(BaseModel):
    description: str
    breed_guess: str
    position: str
    size: str


class CatDetectionResult(BaseModel):
    has_cats: bool
    cat_count: int
    confidence: float
    cats_detected: list[CatDetected] = []
    image_quality: str | None = "Medium"
    suitable_for_cat_spot: bool
    reasoning: str | None = None
    note: str | None = None
    filename: str | None = None
    file_size: int | None = None
    detected_by: str | None = None


class SafetyFactors(BaseModel):
    safe_from_traffic: bool
    has_shelter: bool
    food_source_nearby: bool
    water_access: bool
    escape_routes: bool


class SpotAnalysisResult(BaseModel):
    suitability_score: int
    safety_factors: SafetyFactors | None = None
    environment_type: str
    pros: list[str]
    cons: list[str]
    recommendations: list[str]
    best_times: list[str]
    note: str | None = None
    filename: str | None = None
    analyzed_by: str | None = None


class OverallRecommendation(BaseModel):
    suitable_for_cat_spot: bool
    confidence: float
    summary: str


class AnalysisMetadata(BaseModel):
    filename: str
    file_size: int
    analyzed_by: str


class CombinedAnalysisResult(BaseModel):
    cat_detection: CatDetectionResult
    spot_analysis: SpotAnalysisResult
    overall_recommendation: OverallRecommendation
    metadata: AnalysisMetadata
