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
import shutil
from typing import Final
import pathlib
from datetime import datetime

import google
from firebase_functions import storage_fn, options
from firebase_admin import initialize_app, storage, firestore

from build_plots import generate_average_stride_plots, generate_cadence_plot
import filter_run_data

# initialize firebase app
initialize_app()


def send_video_to_storage(userId: str, video_name: str, video_link: str) -> str:
    """
    Send video to storage
    Parameters
    ----------
    video_link : str
        Video link

    Returns
    -------
    str
        Video link
    """
    storage.bucket().blob(
        f"/movies/users/{userId}/{video_name}.mp4"
    ).upload_from_filename(video_link)

    return storage.bucket().blob(f"/movies/users/{userId}/{video_name}.mp4").public_url


def send_image_to_storage(userId: str, image_name: str, image_link: str) -> str:
    """
    Send image to storage
    Parameters
    ----------
    image_link : str
        Image link

    Returns
    -------
    str
        Image link
    """
    storage.bucket().blob(
        f"/thumbnails/users/{userId}/{image_name}.png"
    ).upload_from_filename(image_link)

    return (
        storage.bucket().blob(f"/thumbnails/users/{userId}/{image_name}.png").public_url
    )


def send_html_to_storage(userId: str, html_name: str, html_link: str) -> str:
    """
    Send html to storage
    Parameters
    ----------
    html_link : str
        html link

    Returns
    -------
    str
        html link
    """
    storage.bucket().blob(
        f"/plots/users/{userId}/{html_name}.html"
    ).upload_from_filename(html_link)

    return storage.bucket().blob(f"/plots/users/{userId}/{html_name}.html").public_url


@storage_fn.on_object_finalized(timeout_sec=1000, memory=options.MemoryOption.GB_1)
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
    if os.path.exists("/tmp/data_pre.run"):
        os.remove("/tmp/data_pre.run")
    if os.path.exists("/tmp/data.run"):
        os.remove("/tmp/data.run")
    if os.path.exists("/tmp/movies"):
        shutil.rmtree("/tmp/movies")
        os.mkdir("/tmp/movies")
    if os.path.exists("/tmp/snaps"):
        shutil.rmtree("/tmp/snaps")
        os.mkdir("/tmp/snaps")
    blob.download_to_filename("/tmp/data_pre.run")

    filter_run_data.filter_run_data("/tmp/data_pre.run", "/tmp/data.run")

    # Create video from object
    print(f"Creating video from {full_file_path}...")
    # graphical.create_video_from_file(LS=ls, LT=lt, RS=rs, RT=rt)
    now: datetime = datetime.now()
    date: str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    video_link: str = f"/tmp/movies/{date}.mp4"
    os.system(f"python graphical.py {video_link}")

    public_link: Final[str] = send_video_to_storage(userId, f"{date}", video_link)
    # create thumbnail using first image added
    thumbnail_link: str = f"/tmp/snaps/000001.png"
    # upload thumbnail to storage
    thumbnail_public_link: Final[str] = send_image_to_storage(
        userId, f"{date}_thumb", thumbnail_link
    )

    # query for most recent post of user
    firestore_client: google.cloud.firestore.Client = firestore.client()

    print(f"userId: {userId}")
    ref = firestore_client.document(f"users/{userId}")
    data = ref.get().to_dict()
    # if data is None:
    #     print(f"User {userId} does not exist")
    # get most recent post
    queryAns = list(
        firestore_client.collection(f"users/{userId}/posts")
        .order_by("datePosted", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )
    if queryAns is None:
        print(f"User {userId} has no posts")
        return
    # get post with type hint
    post_id: str = queryAns[0].id
    # if /tmp/plots not directory, make it one
    if not os.path.exists("/tmp/plots"):
        os.makedirs("/tmp/plots")
    # generate plots for post as well
    stride_filename = "/tmp/plots/stride.png"
    generate_average_stride_plots("/tmp/data.run", stride_filename)
    cadence_filename = "/tmp/plots/cadence.png"
    generate_cadence_plot("/tmp/data.run", cadence_filename)

    # send files to storage

    stride_public_link: Final[str] = send_image_to_storage(
        userId, f"{date}_stride", stride_filename
    )
    cadence_public_link: Final[str] = send_image_to_storage(
        userId, f"{date}_cadence", cadence_filename
    )

    post: firestore.firestore.DocumentSnapshot = queryAns[0].to_dict()
    # update post
    post["videoLink"] = public_link
    post["thumbnailLink"] = thumbnail_public_link
    post["stridePlot"] = stride_public_link
    post["cadencePlot"] = cadence_public_link
    # update post in firebase database
    firestore_client.document(f"users/{userId}/posts/{post_id}").update(post)
    # increment numPosts on /users/{userId} by 1
    # check if numPosts has been initialized
    if data is None:
        ref.set({"numPosts": firestore.firestore.Increment(1)})
    else:
        ref.update({"numPosts": firestore.firestore.Increment(1)})
