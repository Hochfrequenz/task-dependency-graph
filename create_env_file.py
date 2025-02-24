"""
This python script copies the example.env to .env if .env does not already exists.
This is similar to the bash command `mv example.env .env`.
It is used in all tox environments except the linting environment.
"""

from pathlib import Path
from shutil import copyfile


def create_env_file(directory_path: Path):
    """
    Checks if a file with the file name `destination_file_name` exists.
    If yes, nothing will be done.
    If not, it will copy the `source_file_name` file to the `destination_file_name` in the same directory.
    """
    source_file_name: str = "env.example"
    destination_file_name: str = ".env"

    path_to_env_file: Path = directory_path / destination_file_name

    if path_to_env_file.exists():
        print("✅ Great, you have already an environment file.")
    else:
        print(
            f"🤔 Uh I see you have no {destination_file_name} file in {directory_path}\n"
            f"😊 But do not worry, I have you covered, I try to copy for you the {source_file_name} file to"
            f"{destination_file_name}"
        )
        try:
            copyfile(directory_path / source_file_name, path_to_env_file)
            print("🤗 And we are done.\nℹ Please update some credentials for your need, e.g. database credentials.")
        except FileNotFoundError:
            print(
                f"😞 I am so sorry, but the {source_file_name} file is gone. Please ask someone of you colleagues "
                f"to help you."
            )


if __name__ == "__main__":
    cwd_path = Path.cwd()
    root_directory_path = cwd_path
    if root_directory_path.parts[-1] == "tests":
        root_directory_path = root_directory_path.parent
    create_env_file(directory_path=root_directory_path)
