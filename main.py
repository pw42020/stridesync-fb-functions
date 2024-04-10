"""
StrideSync UI Firebase Functions
Authors
-------
Patrick Walsh, Rosana Cho

Description
-----------
Firebase function that, when object transmitted to storage,
creates a video from the object and stores it in the same bucket.
"""

from firebase_functions import storage_fn
from firebase_admin import initialize_app, storage

# initialize firebase app
initialize_app()


@storage_fn
def create_video(data, context):
    """
    Create video from object and store in same bucket
    Parameters
    ----------
    data : dict
        Event data
    context : google.cloud.functions.Context
        Event context
    """
    # Get bucket and object
    bucket = data["bucket"]
    object_name = data["name"]

    # Create video from object
    print(f"Creating video from {object_name}...")
