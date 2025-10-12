import os
import sys
from datetime import datetime

import dropbox
import dropbox.exceptions
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import WriteMode

from config import get_config_path


def _is_token_valid(dbx):
    try:
        dbx.users_get_current_account()
    except AuthError:
        sys.exit(
            "ERROR: Invalid access token; try re-generating an "
            "access token from the app console on the web."
        )


def _upload(dbx, file_path, remote_path):
    with open(file_path, "rb") as file:
        try:
            dbx.files_move(
                remote_path,
                f"/backups/{int(datetime.now().timestamp())}_{remote_path[1:]}",
            )

        except ApiError:
            # file not present. New to cloud
            ...

        try:
            dbx.files_upload(file.read(), remote_path, mode=WriteMode("overwrite"))
            print(f"{remote_path} correctly uplaoded")
        except ApiError as err:
            if (
                err.error.is_path()
                and err.error.get_path().reason.is_insufficient_space()
            ):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
                sys.exit()
            else:
                print(err)
                sys.exit()


def update():
    with dropbox.Dropbox(os.getenv("DBX_TOKEN")) as dbx:
        _is_token_valid(dbx)
        for file_name in ["questions.json", "config.json"]:
            _upload(dbx, get_config_path().parent.joinpath(file_name), f"/{file_name}")


def download():
    with dropbox.Dropbox(os.getenv("DBX_TOKEN")) as dbx:
        _is_token_valid(dbx)
        for file_name in ["questions.json", "config.json"]:
            try:
                dbx.files_download_to_file(
                    get_config_path().parent.joinpath(file_name), f"/{file_name}"
                )
                print(f"{file_name} correctly downloaded")
            except dropbox.exceptions.ApiError as e:
                print(e.error)
