from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import shutil
from typing import Optional
import uuid
import logging

from utils.converter import CSVToXLSXConverter
from models.models import ConversionResult, ConversionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instantiate app
app = FastAPI(
    title="CSV to XLSX Converter API",
    description="Convert CSV files to XLSX format with automatic delimiter detection and error handling.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate converter
converter = CSVToXLSXConverter()

# Temporary storage for tracking conversions (will be moved to a DB)
conversions = {}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CSV to XLSX Converter API",
        "version": "1.0.0",
        "endpoints": {
            "convert": "POST /convert",
            "convert_with_options": "POST /convert_with_options",
            "status": "GET /status/{conversion_id}",
            "download": "GET /download/{conversion_id}"
        }
    }

@app.post("/convert", response_model=ConversionResult)
async def convert_csv(
    file: UploadFile = File(..., description="CSV file to convert"),
):
    """
    Convert a CSV file to XLSX format with automatic delimiter detection.

    Args:
        file: CSV file to upload and convert

    Returns:
        ConversionResult with conversion details and download URL
    """
    if not file.filename.endswith(('.csv', '.txt', '.tsv')):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV, TSV, or TXT file"
        )
    
    # Generate unique conversion ID
    conversion_id = str(uuid.uuid4())
    temp_dir = None
    file_extension = os.path.splitext(file.filename)[1]

    try:
        # Create a temporary directory for this conversion
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f"input_{conversion_id}.{file_extension}")
        output_path = os.path.join(temp_dir, f"output_{conversion_id}.xlsx")

        # Save uploaded file to temp directory
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing conversion {conversion_id}")

        # Perform conversion
        result: ConversionResult = converter.convert_csv_to_xlsx(input_path, output_path)

        if result.success:
            # Store conversion info
            conversions[conversion_id] = {
                "status": "completed",
                "output_path": output_path,
                "temp_dir": temp_dir,
                "result": result
            }

            return ConversionResult(
                conversion_id=conversion_id,
                success=True,
                message=f"Successfully converted {result.rows_processed} rows and {result.columns_processed} columns.",
                rows_processed=result.rows_processed,
                columns_processed=result.columns_processed,
                detected_delimiter=result.detected_delimiter,
                column_name=result.column_names,
                download_url=f"/download/{conversion_id}"
            )
        else:
            # Clean up on failure
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=result.error_message)
    
    except Exception as e:
        # Clean up on failure
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        logger.error(f"Conversion {conversion_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@app.post("/convert_with_options", response_model=ConversionResult)
async def convert_csv_with_options(
    file: UploadFile = File(..., description="CSV file to convert"),
    delimiter: Optional[str] = Form(None, description="Custom delimiter (auto-detected if None)"),
    encoding: str = Form("utf-8", description="File encoding"),
    sheet_name: str = Form("Main Sheet", description="Excel sheet name")
):
    """
    Convert a CSV file to XLSX format with custom options.

    Args:
        file: CSV file to upload and convert
        delimiter: Custom delimiter (auto-detected if None)
        encoding: File encoding
        sheet_name: Excel sheet name

    Returns:
        ConversionResult with conversion details and download URL
    """

    if not file.filename.endswith(('.csv', '.txt', '.tsv')):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV, TSV, or TXT file"
        )
    
    # Generate unique conversion ID
    conversion_id = str(uuid.uuid4())
    temp_dir = None

    try:
        # Handle delimiter representations
        if delimiter:
            delimiter = delimiter.replace("\\t", "\t").replace("\\n", "\n").replace("\\r", "\r").replace("\\s", "\s")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f"input_{conversion_id}.csv")
        output_path = os.path.join(temp_dir, f"output_{conversion_id}.xlsx")

        # Save uploaded file to temp directory
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing conversion {conversion_id} with custom options")

        # Perform conversion
        result: ConversionResult = converter.convert_csv_to_xlsx(
            input_file=input_path,
            output_file=output_path,
            delimiter=delimiter,
            encoding=encoding,
            sheet_name=sheet_name
        )

        if result.success:
            # Store conversion info
            conversions[conversion_id] = {
                "status": "completed",
                "output_path": output_path,
                "temp_dir": temp_dir,
                "result": result
            }

            return ConversionResult(
                conversion_id=conversion_id,
                success=True,
                message=f"Successfully converted {result.rows_processed} rows and {result.columns_processed} columns.",
                rows_processed=result.rows_processed,
                columns_processed=result.columns_processed,
                detected_delimiter=result.detected_delimiter,
                column_names=result.column_names,
                download_url=f"/download/{conversion_id}"
            )
        else:
            # Clean up on failure
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=result.error_message)

    except Exception as e:
        # Clean up on exception
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        logger.error(f"Conversion {conversion_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

        




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)