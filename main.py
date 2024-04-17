"""
StrideSync UI Firebase Functions
Authors
-------
Patrick Walsh, Rosana Cho

Description
-----------
Firebase function that, when object transmitted to storage,
creates a video from the object and stores it in the same bucket.

Notes
-----
If on MacOS: make sure to add 'export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES' to
~/.zshrc or ~/.bashrc to avoid memory error issues.
"""

import os
from typing import Final
import pathlib
from datetime import datetime

from firebase_functions import storage_fn, options
from firebase_admin import initialize_app, storage

import graphical

# initialize firebase app
initialize_app()


def send_video_to_storage(userId: str, video_name: str, video_link: str) -> None:
    """
    Send video to storage
    Parameters
    ----------
    video_link : str
        Video link
    """
    storage.bucket().blob(
        f"/movies/users/{userId}/{video_name}.mp4"
    ).upload_from_filename(video_link)


@storage_fn.on_object_finalized(memory=options.MemoryOption.GB_1)
def create_video(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]):
    """
    Create video from object and store in same bucket
    Parameters
    ----------
    data : dict
        Event data
    context : google.cloud.functions.Context
        Event context
    """
    # get userId, filename
    # userId = event.data.userId
    # filename = event.data.filename
    # Get bucket and object
    bucket_name: str = event.data.bucket
    full_file_path: pathlib.Path = pathlib.PurePath(event.data.name)
    # return
    filenames = str(full_file_path).split("/")
    # bucket: str = filenames[0]
    userId: str = filenames[1]
    filename: str = filenames[2]
    if filenames[0] != "runs":
        print(f"Bucket {filenames[0]} is not runs")
        return
    # try to download file another way, currently getting SIGKILL
    blob = storage.bucket(bucket_name).blob(event.data.name)
    # download file
    blob.download_to_filename(f"/tmp/data.run")

    # Create video from object
    print(f"Creating video from {full_file_path}...")
    # graphical.create_video_from_file(LS=ls, LT=lt, RS=rs, RT=rt)
    now: datetime = datetime.now()
    date: str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    video_link: str = f"/tmp/movies/{date}.mp4"
    os.system(f"python graphical.py {video_link}")
    send_video_to_storage(userId, f"{date}", video_link)
