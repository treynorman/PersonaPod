from utils.cloud import *

"""
    Tests for interacting with podcast cloud repo
"""

# List all files in podcast cloud repo
def test_list_cloud_files():
    cloud_files = list_existing_s3_files()

    print("Files on podcast cloud repo:")
    
    for file in cloud_files:
        print(file)

# Upload a local file to podcast cloud repo
def test_upload_to_cloud(local_file_path):
    upload_to_s3(local_file_path)