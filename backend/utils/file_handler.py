import os
import logging
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, upload_dir: str = "./uploads", max_age_hours: int = 336):  # Default: 2 weeks (336 hours)
        self.upload_dir = upload_dir
        self.max_age_hours = max_age_hours
        os.makedirs(upload_dir, exist_ok=True)
    
    def cleanup_old_files(self):
        """Remove files older than max_age_hours"""
        try:
            current_time = datetime.now()
            deleted_count = 0
            total_size_freed = 0
            
            if not os.path.exists(self.upload_dir):
                logger.warning(f"Upload directory does not exist: {self.upload_dir}")
                return 0
            
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age = current_time - file_time
                    
                    if age > timedelta(hours=self.max_age_hours):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size_freed += file_size
                            logger.info(f"Deleted old file: {file_path} (age: {age.days} days, size: {file_size / (1024*1024):.2f} MB)")
                        except Exception as e:
                            logger.warning(f"Could not delete file {file_path}: {str(e)}")
            
            logger.info(f"Cleanup completed. Deleted {deleted_count} old files. Total size freed: {total_size_freed / (1024*1024):.2f} MB")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {str(e)}", exc_info=True)
            return 0
    
    def cleanup_file(self, file_path: str):
        """Remove a specific file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {str(e)}")
            return False

