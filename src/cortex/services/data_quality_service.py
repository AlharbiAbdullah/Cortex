"""
Data Quality Assessment Service.

Provides automated data quality profiling, completeness scoring,
consistency checks, and anomaly detection for tabular data.
"""

import logging
import statistics
from collections import Counter
from datetime import datetime
from functools import lru_cache
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class DataQualitySettings(BaseSettings):
    """Data quality service configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    completeness_threshold: float = 0.95
    uniqueness_threshold: float = 0.99
    consistency_threshold: float = 0.90
    anomaly_std_threshold: float = 3.0
    max_sample_rows: int = 10000


@lru_cache()
def get_data_quality_settings() -> DataQualitySettings:
    """Get cached data quality settings."""
    return DataQualitySettings()


class ColumnProfile(BaseModel):
    """Profile for a single column."""

    column_name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Detected data type")
    total_count: int = Field(..., description="Total row count")
    null_count: int = Field(default=0, description="Count of null values")
    null_percentage: float = Field(default=0.0, description="Null percentage")
    unique_count: int = Field(default=0, description="Count of unique values")
    unique_percentage: float = Field(default=0.0, description="Unique percentage")
    min_value: Any = Field(default=None, description="Minimum value")
    max_value: Any = Field(default=None, description="Maximum value")
    mean_value: float | None = Field(default=None, description="Mean (numeric only)")
    std_value: float | None = Field(default=None, description="Std dev (numeric only)")
    top_values: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Most common values",
    )
    sample_values: list[Any] = Field(
        default_factory=list,
        description="Sample values",
    )
    issues: list[str] = Field(default_factory=list, description="Detected issues")


class DataQualityScore(BaseModel):
    """Overall data quality score."""

    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality 0-1")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Data completeness")
    uniqueness_score: float = Field(..., ge=0.0, le=1.0, description="Data uniqueness")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Data consistency")
    validity_score: float = Field(..., ge=0.0, le=1.0, description="Data validity")
    grade: str = Field(..., description="Quality grade: A, B, C, D, F")


class AnomalyResult(BaseModel):
    """Detected data anomaly."""

    column: str = Field(..., description="Column name")
    anomaly_type: str = Field(..., description="Type of anomaly")
    description: str = Field(..., description="Anomaly description")
    affected_rows: int = Field(default=0, description="Number of affected rows")
    severity: str = Field(default="medium", description="Severity: low, medium, high")
    sample_values: list[Any] = Field(
        default_factory=list,
        description="Sample anomalous values",
    )


class DataQualityReport(BaseModel):
    """Complete data quality report."""

    dataset_name: str = Field(..., description="Dataset identifier")
    assessed_at: str = Field(..., description="Assessment timestamp")
    row_count: int = Field(..., description="Total row count")
    column_count: int = Field(..., description="Total column count")
    quality_score: DataQualityScore = Field(..., description="Quality scores")
    column_profiles: list[ColumnProfile] = Field(
        default_factory=list,
        description="Per-column profiles",
    )
    anomalies: list[AnomalyResult] = Field(
        default_factory=list,
        description="Detected anomalies",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Improvement recommendations",
    )
    summary: str = Field(default="", description="Executive summary")


class DataQualityService:
    """
    Service for assessing data quality.

    Provides:
    - Completeness scoring (null/missing analysis)
    - Uniqueness analysis (duplicate detection)
    - Consistency checks (format validation)
    - Anomaly detection (outliers, patterns)
    - Data profiling (statistics, distributions)
    """

    def __init__(self):
        """Initialize the data quality service."""
        self._settings = get_data_quality_settings()

    async def assess(
        self,
        df: pd.DataFrame,
        dataset_name: str = "dataset",
    ) -> DataQualityReport:
        """
        Perform comprehensive data quality assessment.

        Args:
            df: DataFrame to assess.
            dataset_name: Identifier for the dataset.

        Returns:
            DataQualityReport with all quality metrics.
        """
        if df.empty:
            return DataQualityReport(
                dataset_name=dataset_name,
                assessed_at=datetime.now().isoformat(),
                row_count=0,
                column_count=0,
                quality_score=DataQualityScore(
                    overall_score=0.0,
                    completeness_score=0.0,
                    uniqueness_score=0.0,
                    consistency_score=0.0,
                    validity_score=0.0,
                    grade="F",
                ),
                summary="Dataset is empty.",
            )

        # Sample if too large
        if len(df) > self._settings.max_sample_rows:
            df_sample = df.sample(n=self._settings.max_sample_rows, random_state=42)
            sampled = True
        else:
            df_sample = df
            sampled = False

        # Profile columns
        column_profiles = []
        for col in df_sample.columns:
            profile = self._profile_column(df_sample, col)
            column_profiles.append(profile)

        # Calculate scores
        completeness_score = self._calculate_completeness(df_sample, column_profiles)
        uniqueness_score = self._calculate_uniqueness(df_sample)
        consistency_score = self._calculate_consistency(column_profiles)
        validity_score = self._calculate_validity(column_profiles)

        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.3
            + uniqueness_score * 0.2
            + consistency_score * 0.25
            + validity_score * 0.25
        )

        grade = self._score_to_grade(overall_score)

        quality_score = DataQualityScore(
            overall_score=round(overall_score, 4),
            completeness_score=round(completeness_score, 4),
            uniqueness_score=round(uniqueness_score, 4),
            consistency_score=round(consistency_score, 4),
            validity_score=round(validity_score, 4),
            grade=grade,
        )

        # Detect anomalies
        anomalies = self._detect_anomalies(df_sample, column_profiles)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            quality_score,
            column_profiles,
            anomalies,
        )

        # Generate summary
        summary = self._generate_summary(
            dataset_name,
            df,
            quality_score,
            anomalies,
            sampled,
        )

        return DataQualityReport(
            dataset_name=dataset_name,
            assessed_at=datetime.now().isoformat(),
            row_count=len(df),
            column_count=len(df.columns),
            quality_score=quality_score,
            column_profiles=column_profiles,
            anomalies=anomalies,
            recommendations=recommendations,
            summary=summary,
        )

    def _profile_column(self, df: pd.DataFrame, col: str) -> ColumnProfile:
        """Profile a single column."""
        series = df[col]
        total_count = len(series)

        # Null analysis
        null_count = series.isna().sum()
        null_percentage = null_count / total_count if total_count > 0 else 0.0

        # Unique analysis
        unique_count = series.nunique()
        unique_percentage = unique_count / total_count if total_count > 0 else 0.0

        # Detect data type
        data_type = self._detect_data_type(series)

        # Statistics
        min_value = None
        max_value = None
        mean_value = None
        std_value = None

        non_null = series.dropna()
        if len(non_null) > 0:
            if data_type in ("numeric", "integer", "float"):
                try:
                    min_value = float(non_null.min())
                    max_value = float(non_null.max())
                    mean_value = float(non_null.mean())
                    std_value = float(non_null.std()) if len(non_null) > 1 else 0.0
                except (ValueError, TypeError):
                    pass
            elif data_type == "datetime":
                try:
                    min_value = str(non_null.min())
                    max_value = str(non_null.max())
                except Exception:
                    pass
            else:
                try:
                    min_value = str(non_null.min())
                    max_value = str(non_null.max())
                except Exception:
                    pass

        # Top values
        top_values = []
        try:
            value_counts = series.value_counts().head(5)
            for val, count in value_counts.items():
                top_values.append({
                    "value": str(val) if val is not None else "NULL",
                    "count": int(count),
                    "percentage": round(count / total_count * 100, 2),
                })
        except Exception:
            pass

        # Sample values
        sample_values = []
        try:
            samples = non_null.head(5).tolist()
            sample_values = [str(v) for v in samples]
        except Exception:
            pass

        # Detect issues
        issues = []
        if null_percentage > 0.5:
            issues.append("High null rate (>50%)")
        elif null_percentage > 0.1:
            issues.append("Moderate null rate (>10%)")

        if unique_percentage < 0.01 and unique_count > 1:
            issues.append("Low cardinality")
        if unique_percentage > 0.99 and unique_count < total_count:
            issues.append("Near-unique values (possible ID column)")

        return ColumnProfile(
            column_name=col,
            data_type=data_type,
            total_count=total_count,
            null_count=int(null_count),
            null_percentage=round(null_percentage, 4),
            unique_count=int(unique_count),
            unique_percentage=round(unique_percentage, 4),
            min_value=min_value,
            max_value=max_value,
            mean_value=round(mean_value, 4) if mean_value is not None else None,
            std_value=round(std_value, 4) if std_value is not None else None,
            top_values=top_values,
            sample_values=sample_values,
            issues=issues,
        )

    def _detect_data_type(self, series: pd.Series) -> str:
        """Detect the semantic data type of a series."""
        # Check pandas dtype first
        dtype = str(series.dtype)

        if "int" in dtype:
            return "integer"
        elif "float" in dtype:
            return "float"
        elif "datetime" in dtype:
            return "datetime"
        elif "bool" in dtype:
            return "boolean"

        # For object types, sample and analyze
        non_null = series.dropna()
        if len(non_null) == 0:
            return "unknown"

        sample = non_null.head(100)

        # Check if numeric
        try:
            pd.to_numeric(sample)
            return "numeric"
        except (ValueError, TypeError):
            pass

        # Check if datetime
        try:
            pd.to_datetime(sample)
            return "datetime"
        except (ValueError, TypeError):
            pass

        # Check if boolean-like
        unique_vals = set(str(v).lower() for v in sample.unique())
        if unique_vals.issubset({"true", "false", "yes", "no", "1", "0", "y", "n"}):
            return "boolean"

        return "string"

    def _calculate_completeness(
        self,
        df: pd.DataFrame,
        profiles: list[ColumnProfile],
    ) -> float:
        """Calculate overall completeness score."""
        if not profiles:
            return 0.0

        total_cells = len(df) * len(df.columns)
        null_cells = sum(p.null_count for p in profiles)

        return 1.0 - (null_cells / total_cells) if total_cells > 0 else 0.0

    def _calculate_uniqueness(self, df: pd.DataFrame) -> float:
        """Calculate uniqueness score (inverse of duplicate rate)."""
        if len(df) == 0:
            return 0.0

        duplicate_count = df.duplicated().sum()
        return 1.0 - (duplicate_count / len(df))

    def _calculate_consistency(self, profiles: list[ColumnProfile]) -> float:
        """Calculate consistency score based on format uniformity."""
        if not profiles:
            return 0.0

        scores = []
        for profile in profiles:
            # Penalize mixed types and high null rates
            score = 1.0
            if profile.null_percentage > 0.2:
                score -= 0.2
            if len(profile.issues) > 0:
                score -= 0.1 * len(profile.issues)
            scores.append(max(0.0, score))

        return sum(scores) / len(scores)

    def _calculate_validity(self, profiles: list[ColumnProfile]) -> float:
        """Calculate validity score based on value distributions."""
        if not profiles:
            return 0.0

        scores = []
        for profile in profiles:
            score = 1.0

            # Check for concerning patterns
            if profile.unique_percentage < 0.001:
                score -= 0.3  # Too many duplicates
            if "High null rate" in " ".join(profile.issues):
                score -= 0.2

            scores.append(max(0.0, score))

        return sum(scores) / len(scores)

    def _detect_anomalies(
        self,
        df: pd.DataFrame,
        profiles: list[ColumnProfile],
    ) -> list[AnomalyResult]:
        """Detect data anomalies."""
        anomalies = []

        for profile in profiles:
            col = profile.column_name

            # Null anomalies
            if profile.null_percentage > 0.5:
                anomalies.append(
                    AnomalyResult(
                        column=col,
                        anomaly_type="high_null_rate",
                        description=f"Column has {profile.null_percentage:.1%} null values",
                        affected_rows=profile.null_count,
                        severity="high",
                    )
                )

            # Outliers for numeric columns
            if profile.data_type in ("numeric", "integer", "float"):
                if profile.mean_value is not None and profile.std_value is not None:
                    if profile.std_value > 0:
                        series = pd.to_numeric(df[col], errors="coerce")
                        z_scores = (series - profile.mean_value) / profile.std_value
                        outlier_mask = z_scores.abs() > self._settings.anomaly_std_threshold
                        outlier_count = outlier_mask.sum()

                        if outlier_count > 0:
                            outlier_values = series[outlier_mask].head(5).tolist()
                            anomalies.append(
                                AnomalyResult(
                                    column=col,
                                    anomaly_type="statistical_outliers",
                                    description=(
                                        f"Found {outlier_count} values beyond "
                                        f"{self._settings.anomaly_std_threshold} std devs"
                                    ),
                                    affected_rows=int(outlier_count),
                                    severity="medium",
                                    sample_values=[str(v) for v in outlier_values],
                                )
                            )

            # Constant columns
            if profile.unique_count == 1 and profile.total_count > 10:
                anomalies.append(
                    AnomalyResult(
                        column=col,
                        anomaly_type="constant_column",
                        description="Column has only one unique value",
                        affected_rows=profile.total_count,
                        severity="low",
                    )
                )

        return anomalies

    def _generate_recommendations(
        self,
        score: DataQualityScore,
        profiles: list[ColumnProfile],
        anomalies: list[AnomalyResult],
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if score.completeness_score < self._settings.completeness_threshold:
            high_null_cols = [
                p.column_name for p in profiles if p.null_percentage > 0.1
            ]
            if high_null_cols:
                recommendations.append(
                    f"Address missing values in columns: {', '.join(high_null_cols[:5])}"
                )

        if score.uniqueness_score < self._settings.uniqueness_threshold:
            recommendations.append(
                "Review and remove duplicate records to improve data uniqueness"
            )

        if score.consistency_score < self._settings.consistency_threshold:
            recommendations.append(
                "Standardize data formats and validate data entry processes"
            )

        # Anomaly-based recommendations
        outlier_anomalies = [a for a in anomalies if a.anomaly_type == "statistical_outliers"]
        if outlier_anomalies:
            recommendations.append(
                f"Investigate outliers in columns: "
                f"{', '.join(a.column for a in outlier_anomalies[:3])}"
            )

        null_anomalies = [a for a in anomalies if a.anomaly_type == "high_null_rate"]
        if null_anomalies:
            recommendations.append(
                "Consider imputation strategies for high-null columns or review data collection"
            )

        if not recommendations:
            recommendations.append("Data quality is good. Continue monitoring for changes.")

        return recommendations

    def _generate_summary(
        self,
        dataset_name: str,
        df: pd.DataFrame,
        score: DataQualityScore,
        anomalies: list[AnomalyResult],
        sampled: bool,
    ) -> str:
        """Generate executive summary."""
        summary_parts = [
            f"Data quality assessment for '{dataset_name}':",
            f"- Overall score: {score.overall_score:.1%} (Grade: {score.grade})",
            f"- Dataset size: {len(df):,} rows x {len(df.columns)} columns",
        ]

        if sampled:
            summary_parts.append(
                f"  (Note: Analysis based on sample of {self._settings.max_sample_rows:,} rows)"
            )

        if score.completeness_score < 0.9:
            summary_parts.append(
                f"- Completeness: {score.completeness_score:.1%} (needs improvement)"
            )
        else:
            summary_parts.append(f"- Completeness: {score.completeness_score:.1%} (good)")

        if anomalies:
            high_severity = [a for a in anomalies if a.severity == "high"]
            summary_parts.append(
                f"- Anomalies detected: {len(anomalies)} "
                f"({len(high_severity)} high severity)"
            )

        return " ".join(summary_parts)

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def quick_check(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Perform a quick quality check without full profiling.

        Args:
            df: DataFrame to check.

        Returns:
            Dict with basic quality metrics.
        """
        if df.empty:
            return {
                "row_count": 0,
                "column_count": 0,
                "quality_score": 0.0,
                "grade": "F",
            }

        total_cells = len(df) * len(df.columns)
        null_cells = df.isna().sum().sum()
        duplicate_rows = df.duplicated().sum()

        completeness = 1.0 - (null_cells / total_cells) if total_cells > 0 else 0.0
        uniqueness = 1.0 - (duplicate_rows / len(df)) if len(df) > 0 else 0.0

        overall = (completeness + uniqueness) / 2

        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "null_cells": int(null_cells),
            "duplicate_rows": int(duplicate_rows),
            "completeness": round(completeness, 4),
            "uniqueness": round(uniqueness, 4),
            "quality_score": round(overall, 4),
            "grade": self._score_to_grade(overall),
        }


# Singleton instance
_data_quality_service: DataQualityService | None = None


def get_data_quality_service() -> DataQualityService:
    """Get or create the singleton data quality service."""
    global _data_quality_service
    if _data_quality_service is None:
        _data_quality_service = DataQualityService()
    return _data_quality_service
