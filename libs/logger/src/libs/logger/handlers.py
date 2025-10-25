"""Custom logging handlers with archiving support."""

import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path


class ArchivingRotatingFileHandler(RotatingFileHandler):
    """Rotating file handler that archives old log files.

    When a log file rotates, old files are moved to the archive directory
    instead of remaining in the same directory with .1, .2 suffixes.
    """

    def __init__(
        self,
        filename: Path,
        archive_dir: Path,
        max_bytes: int,
        backup_count: int = 10,
        encoding: str = "utf-8",
    ):
        """Initialize the archiving handler.

        Args:
            filename: Path to the log file
            archive_dir: Directory where archived logs will be stored
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            encoding: File encoding
        """
        self.archive_dir = archive_dir
        self.log_filename = filename

        # Ensure directories exist
        filename.parent.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Initialize parent RotatingFileHandler
        super().__init__(
            filename=str(filename),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )

    def doRollover(self) -> None:  # noqa: N802
        """Perform rollover and archive old log file."""
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore[assignment]

        # Generate archive filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = self.log_filename.stem
        archive_name = f"{base_name}_{timestamp}.log"
        archive_path = self.archive_dir / archive_name

        # Move current log to archive
        if self.log_filename.exists():
            shutil.move(str(self.log_filename), str(archive_path))

        # Clean up old archives if exceeding backup count
        self._cleanup_old_archives(base_name)

        # Open new log file
        self.stream = self._open()

    def _cleanup_old_archives(self, base_name: str) -> None:
        """Remove oldest archived files if exceeding backup count.

        Args:
            base_name: Base name of the log file (without extension)
        """
        # Get all archived files for this log
        pattern = f"{base_name}_*.log"
        archived_files = sorted(self.archive_dir.glob(pattern))

        # Remove oldest files if we exceed backup count
        if len(archived_files) > self.backupCount:
            files_to_remove = archived_files[: -self.backupCount]
            for old_file in files_to_remove:
                old_file.unlink()
