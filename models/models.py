from pydantic import BaseModel
from typing import Optional, List

class ConverstionResult(BaseModel):
    """API response model for conversion result"""
    conversion_id: str
    success: bool
    message: str
    rows_processed: int = 0
    columns_processed: int = 0
    detected_delimiter: Optional[str] = None
    column_names: List[str] = []
    download_url: Optional[str] = None


class ConversionStatus(BaseModel):
    """API response model for conversion status"""
    conversion_id: str
    status: str
    success: bool
    message: str
    rows_processed: int = 0
    columns_processed: int = 0