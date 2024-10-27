import pandas as pd
from logger import logger

class FileProcessor:
    @staticmethod
    def process_csv(local_path):
        """Process CSV file by filtering rows with status 'ok'"""
        try:
            df = pd.read_csv(local_path, low_memory=False)
            initial_count = len(df)
            
            df_cleaned = df[df['status'] == 'ok']
            final_count = len(df_cleaned)
            
            df_cleaned.to_csv(local_path, index=False)
            
            logger.info({
                'message': 'File processed successfully',
                'initial_records': initial_count,
                'final_records': final_count,
                'records_removed': initial_count - final_count
            })
            
            return True
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            return False