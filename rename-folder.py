import sys
import os
import imagehash
import re
from PIL import Image
from collections import defaultdict

makeChanges = True
imageExtensions = [
  ".jpg",
  ".jpeg",
  ".png",
  ".gif",
]
tempString = '__temp__'

# Sort folder by natural numbers
def atoi(text):
  return int(text) if text.isdigit() else text

def natural_keys(text: str, dirName: str):
  init = [1]
  if text.lower().startswith(dirName.lower()):
    init = [0]

  '''
  alist.sort(key=natural_keys) sorts in human order
  http://nedbatchelder.com/blog/200712/human_sorting.html
  (See Toothy's implementation in the comments)
  '''
  return init + [ atoi(c) for c in re.split(r'(\d+)', text) ]

# Collects images and files
def renameFilesInFolderRecursive(dirPath):
  dirName: str = os.path.basename(dirPath).lower()

  images = []
  files = []

  # Collect all files
  filePaths = sorted(os.listdir(dirPath), key=lambda path: natural_keys(path, dirName))
  for file in filePaths:
    filePath = os.path.join(dirPath, file)

    # Recurse into directory
    if os.path.isdir(filePath):
      renameFilesInFolderRecursive(filePath)
      continue

    fileName, fileExtension = os.path.splitext(file)
    fileName = fileName.lower()
    fileExtension = fileExtension.lower()

    # Non-image
    if fileExtension not in imageExtensions:
      files.append((filePath, file, fileExtension))
      continue

    # Image
    images.append((filePath, file, fileExtension))

  # Combine files at the end of images
  files = images + files

  if len(files) < 1:
    return

  # Prompt to see if the change should be made
  print('\nFiles:')
  for file in files:
    print(f'  {file[1]}')

  prompt = input(f'Rename files in: {dirPath}? Y/n: ')
  if len(prompt) > 0:
    if not prompt.lower().startswith('y'):
      print('  Skipped')
      return
  print('  Renaming...')

  # Rename files in order, first to temp name, then to real name
  for i in range(len(files)):
    filePath = files[i][0]
    tempFile = f'{tempString}{i}'
    tempPath = os.path.join(dirPath, tempFile)
    if makeChanges:
      os.rename(filePath, tempPath)

  for i in range(len(files)):
    _, fileName, fileExtension = files[i]
    newName = f'{dirName}_{(i + 1)}'.replace(' ', '_')
    newFile = f'{newName}{fileExtension}'
    newPath = os.path.join(dirPath, newFile)
    tempFile = f'{tempString}{i}'
    tempPath = os.path.join(dirPath, tempFile)
    if makeChanges:
      os.rename(tempPath, newPath)
    print(f'    Rename: {fileName} -> {newFile}')

def renameFiles():
  # Check args
  if len(sys.argv) < 2:
    print("Please provide path")
    return

  # Calc path
  path = sys.argv[1]

  # Can't work on non-existent path
  if not os.path.exists(path) or not os.path.isdir(path):
    print(f'Path: {path} does not exist')
    return

  if path.endswith('\\') or path.endswith('/'):
    path = path[:len(path) - 1]

  print(f'Starting from {path}')
  renameFilesInFolderRecursive(path)

if __name__ == "__main__":
  renameFiles()
