from pathlib import Path
import zipfile


def unzip(file: Path, to: Path, delete: bool = True) -> Path:
  """
  Unzips a zip file to the specified path.
  """
  new_path = to / file.name[:-4]

  with zipfile.ZipFile(file, "r") as zip_ref:
    zip_ref.extractall(new_path)

  # move subfolders to the root
  while len(list(new_path.iterdir())) == 1:
    subfolder = list(new_path.iterdir())[0]
    if not subfolder.is_dir():
      break
    for f in subfolder.iterdir():
      f.rename(new_path / f.name)

    subfolder.rmdir()
    
  if delete:
    # Delete the zip file
    file.unlink()

  return new_path


def unzip_all(fp: str = "./", to: str = "./extracted/", delete: bool = True) -> list[Path]:
  """
  Unzips all zip files in the specified path.
  """
  path = Path(fp)
  to = Path(to)
  new_paths = []
  for file in path.glob("*.zip"):
    try:
      new_paths.append(unzip(file, to, delete=delete))
    except Exception as e:
      print(f"Error unzipping {file}: {e}")

  return new_paths