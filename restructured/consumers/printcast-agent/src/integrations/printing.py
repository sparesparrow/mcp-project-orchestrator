"""
Print server integration for PrintCast Agent.

Handles printing operations using CUPS and PDF generation.
"""

import asyncio
import os
import tempfile
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import subprocess
import base64

import structlog
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from jinja2 import Template

logger = structlog.get_logger(__name__)


class PrintJob(BaseModel):
    """Represents a print job."""
    
    job_id: str
    session_id: str
    document_path: str
    printer_name: str
    status: str = "pending"
    pages: int = 0
    copies: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PrintManager:
    """
    Manages printing operations.
    
    Features:
    - CUPS integration for local/network printers
    - PDF generation from content
    - Print job queue management
    - Print preview generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize print manager.
        
        Args:
            config: Configuration including:
                - default_printer: Default printer name
                - cups_server: CUPS server address
                - temp_dir: Temporary directory for print files
                - pdf_settings: PDF generation settings
        """
        self.config = config
        self.default_printer = config.get("default_printer", "default")
        self.cups_server = config.get("cups_server", "localhost:631")
        self.temp_dir = Path(config.get("temp_dir", "/tmp/printcast"))
        self.pdf_settings = config.get("pdf_settings", {})
        
        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Print job tracking
        self.jobs: Dict[str, PrintJob] = {}
        self.job_counter = 0
        
        # Check if CUPS is available
        self.cups_available = False
        
        logger.info(
            "Print manager initialized",
            default_printer=self.default_printer,
            temp_dir=str(self.temp_dir)
        )
    
    async def initialize(self):
        """Initialize print manager and check CUPS availability."""
        try:
            # Check if CUPS is available
            result = await asyncio.create_subprocess_exec(
                "lpstat", "-p",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.cups_available = True
                logger.info("CUPS is available")
                
                # Parse available printers
                printers = []
                for line in stdout.decode().split("\n"):
                    if line.startswith("printer"):
                        parts = line.split()
                        if len(parts) >= 2:
                            printers.append(parts[1])
                
                logger.info(
                    "Available printers",
                    count=len(printers),
                    printers=printers
                )
            else:
                logger.warning("CUPS not available", stderr=stderr.decode())
                
        except Exception as e:
            logger.warning("Could not check CUPS availability", error=str(e))
            self.cups_available = False
    
    async def shutdown(self):
        """Cleanup resources."""
        # Cancel pending jobs
        for job in self.jobs.values():
            if job.status == "pending":
                job.status = "cancelled"
        
        logger.info("Print manager shutdown")
    
    def is_available(self) -> bool:
        """Check if printing is available."""
        return self.cups_available
    
    async def generate_pdf(
        self,
        content: str,
        title: str = "PrintCast Document",
        format: str = "A4",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate PDF from content.
        
        Args:
            content: Content to print (text, HTML, or markdown)
            title: Document title
            format: Page format
            output_path: Optional output path
        
        Returns:
            Path to generated PDF
        """
        try:
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.temp_dir / f"document_{timestamp}.pdf"
            else:
                output_path = Path(output_path)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading1']
            normal_style = styles['Normal']
            
            # Add title
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 12))
            
            # Add timestamp
            timestamp_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elements.append(Paragraph(timestamp_text, normal_style))
            elements.append(Spacer(1, 20))
            
            # Parse and add content
            if content.startswith("<html>"):
                # HTML content - parse and convert
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, "html.parser")
                
                for elem in soup.find_all(["h1", "h2", "h3", "p", "ul", "ol"]):
                    if elem.name.startswith("h"):
                        elements.append(Paragraph(elem.text, heading_style))
                    else:
                        elements.append(Paragraph(elem.text, normal_style))
                    elements.append(Spacer(1, 6))
                    
            elif content.startswith("#"):
                # Markdown content - convert to PDF elements
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("##"):
                        elements.append(Paragraph(line[2:].strip(), heading_style))
                    elif line.startswith("#"):
                        elements.append(Paragraph(line[1:].strip(), title_style))
                    elif line.strip():
                        elements.append(Paragraph(line, normal_style))
                    elements.append(Spacer(1, 6))
                    
            else:
                # Plain text - split by paragraphs
                paragraphs = content.split("\n\n")
                for para in paragraphs:
                    if para.strip():
                        elements.append(Paragraph(para, normal_style))
                        elements.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(elements)
            
            logger.info(
                "PDF generated",
                path=str(output_path),
                size=output_path.stat().st_size
            )
            
            return str(output_path)
            
        except Exception as e:
            logger.error("Failed to generate PDF", error=str(e))
            raise
    
    async def generate_preview(
        self,
        items: List[str],
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Generate print preview.
        
        Args:
            items: Content items to preview
            format: Preview format
        
        Returns:
            Preview information
        """
        try:
            # Generate preview document
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            preview_path = self.temp_dir / f"preview_{timestamp}.{format}"
            
            # Create preview content
            content = "# Print Preview\n\n"
            for i, item in enumerate(items, 1):
                content += f"## Item {i}\n{item}\n\n"
            
            # Generate document
            if format == "pdf":
                doc_path = await self.generate_pdf(
                    content,
                    title="Print Preview",
                    output_path=str(preview_path)
                )
            else:
                # HTML preview
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head><title>Print Preview</title></head>
                <body>
                    <h1>Print Preview</h1>
                    {''.join(f'<div>{item}</div>' for item in items)}
                </body>
                </html>
                """
                preview_path.write_text(html_content)
                doc_path = str(preview_path)
            
            # Get file info
            file_stat = preview_path.stat()
            
            # Estimate page count (rough)
            page_count = max(1, len(items) // 3)
            
            return {
                "url": f"file://{doc_path}",
                "path": doc_path,
                "pages": page_count,
                "size": file_stat.st_size,
                "format": format
            }
            
        except Exception as e:
            logger.error("Failed to generate preview", error=str(e))
            raise
    
    async def print_document(
        self,
        document_path: str,
        printer_name: Optional[str] = None,
        copies: int = 1,
        options: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Print a document.
        
        Args:
            document_path: Path to document
            printer_name: Printer to use
            copies: Number of copies
            options: Print options
        
        Returns:
            Print job ID
        """
        if not self.cups_available:
            logger.warning("CUPS not available, simulating print")
            return await self._simulate_print(document_path)
        
        try:
            printer = printer_name or self.default_printer
            
            # Create print job
            self.job_counter += 1
            job_id = f"job_{self.job_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            job = PrintJob(
                job_id=job_id,
                session_id="",
                document_path=document_path,
                printer_name=printer,
                copies=copies,
                status="pending"
            )
            
            self.jobs[job_id] = job
            
            # Build lpr command
            cmd = ["lpr", "-P", printer]
            
            if copies > 1:
                cmd.extend(["-#", str(copies)])
            
            if options:
                for key, value in options.items():
                    cmd.extend(["-o", f"{key}={value}"])
            
            cmd.append(document_path)
            
            # Execute print command
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                job.status = "printing"
                logger.info(
                    "Document sent to printer",
                    job_id=job_id,
                    printer=printer,
                    document=document_path
                )
                
                # Start monitoring job
                asyncio.create_task(self._monitor_print_job(job_id))
                
            else:
                job.status = "failed"
                logger.error(
                    "Failed to print document",
                    job_id=job_id,
                    error=stderr.decode()
                )
                raise RuntimeError(f"Print failed: {stderr.decode()}")
            
            return job_id
            
        except Exception as e:
            logger.error("Failed to print document", error=str(e))
            raise
    
    async def _simulate_print(self, document_path: str) -> str:
        """Simulate printing when CUPS is not available."""
        self.job_counter += 1
        job_id = f"sim_job_{self.job_counter}"
        
        job = PrintJob(
            job_id=job_id,
            session_id="",
            document_path=document_path,
            printer_name="simulated",
            status="simulated"
        )
        
        self.jobs[job_id] = job
        
        logger.info(
            "Print simulated",
            job_id=job_id,
            document=document_path
        )
        
        # Simulate processing delay
        await asyncio.sleep(2)
        job.status = "completed"
        job.completed_at = datetime.now()
        
        return job_id
    
    async def _monitor_print_job(self, job_id: str):
        """Monitor print job status."""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        try:
            # Poll job status
            for _ in range(60):  # Monitor for up to 60 seconds
                await asyncio.sleep(1)
                
                # Check job status using lpstat
                result = await asyncio.create_subprocess_exec(
                    "lpstat", "-W", "completed",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, _ = await result.communicate()
                
                # Simple check - in production would parse lpstat output properly
                if job_id in stdout.decode():
                    job.status = "completed"
                    job.completed_at = datetime.now()
                    logger.info("Print job completed", job_id=job_id)
                    break
                    
        except Exception as e:
            logger.error(
                "Error monitoring print job",
                job_id=job_id,
                error=str(e)
            )
            job.status = "error"
    
    async def cancel_print_job(self, job_id: str) -> bool:
        """
        Cancel a print job.
        
        Args:
            job_id: Job ID to cancel
        
        Returns:
            True if cancelled successfully
        """
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in ["completed", "cancelled", "failed"]:
            return False
        
        try:
            if self.cups_available:
                # Cancel using lprm
                result = await asyncio.create_subprocess_exec(
                    "lprm", "-P", job.printer_name, job_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await result.communicate()
            
            job.status = "cancelled"
            logger.info("Print job cancelled", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cancel print job",
                job_id=job_id,
                error=str(e)
            )
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get print job status."""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "printer": job.printer_name,
            "document": job.document_path,
            "created": job.created_at.isoformat(),
            "completed": job.completed_at.isoformat() if job.completed_at else None
        }
    
    async def get_printer_list(self) -> List[Dict[str, Any]]:
        """Get list of available printers."""
        printers = []
        
        if not self.cups_available:
            return [{
                "name": "simulated",
                "status": "ready",
                "default": True
            }]
        
        try:
            # Get printer list using lpstat
            result = await asyncio.create_subprocess_exec(
                "lpstat", "-p", "-d",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await result.communicate()
            output = stdout.decode()
            
            # Parse printer list
            default_printer = None
            for line in output.split("\n"):
                if line.startswith("printer"):
                    parts = line.split()
                    if len(parts) >= 2:
                        printer_name = parts[1]
                        status = "ready" if "enabled" in line else "offline"
                        
                        printers.append({
                            "name": printer_name,
                            "status": status,
                            "default": False
                        })
                elif line.startswith("system default"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        default_printer = parts[1].strip()
            
            # Mark default printer
            for printer in printers:
                if printer["name"] == default_printer:
                    printer["default"] = True
                    
        except Exception as e:
            logger.error("Failed to get printer list", error=str(e))
        
        return printers
    
    async def create_print_batch(
        self,
        documents: List[Dict[str, Any]],
        printer_name: Optional[str] = None
    ) -> List[str]:
        """
        Create a batch print job.
        
        Args:
            documents: List of documents to print
            printer_name: Printer to use
        
        Returns:
            List of job IDs
        """
        job_ids = []
        
        for doc in documents:
            try:
                # Generate PDF if needed
                if "content" in doc:
                    doc_path = await self.generate_pdf(
                        doc["content"],
                        title=doc.get("title", "Document")
                    )
                else:
                    doc_path = doc["path"]
                
                # Print document
                job_id = await self.print_document(
                    doc_path,
                    printer_name=printer_name,
                    copies=doc.get("copies", 1)
                )
                
                job_ids.append(job_id)
                
            except Exception as e:
                logger.error(
                    "Failed to print document in batch",
                    document=doc.get("title", "Unknown"),
                    error=str(e)
                )
        
        return job_ids