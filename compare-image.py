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
  ".tif",
  ".tiff",
]
badfolder = '__remove'
reportFile = '__report.txt'

# Sort folder by natural numbers
def atoi(text: str):
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

# Cleans a folder
def cleanFolderRecursive(dirPath: str, report: list):
  # Ignore already cleaned paths
  dirName: str = os.path.basename(os.path.dirname(dirPath))
  if dirName == badfolder:
    return

  # Cache vars
  badPath = os.path.join(dirPath, badfolder)
  images = defaultdict(list)
  files = defaultdict(list)
  filePaths = sorted(os.listdir(dirPath), key=lambda path: natural_keys(path, dirName))

  # Calcualte stats for each file
  print(f'Checking {dirPath}...')
  hasDuplicates = False
  for filePath in filePaths:
    fullFilePath = os.path.join(dirPath, filePath)

    if os.path.isdir(fullFilePath):
      cleanFolderRecursive(fullFilePath, report)
      continue
    if filePath == reportFile:
      continue

    duplicateExtension = os.path.splitext(filePath)[1].lower()
    try:
      size = os.stat(fullFilePath).st_size
    except:
      continue

    # Non-image
    if duplicateExtension not in imageExtensions:
      fileList = files[size]
      fileList.append((fullFilePath, size, filePath))
      hasDuplicates = hasDuplicates or len(fileList) > 1
      continue

    # Image
    try:
      hashValue = imagehash.average_hash(Image.open(fullFilePath))
    except:
      print(f'Failed to parse image: {fullFilePath}')
      continue
    imageList = images[hashValue]
    imageList.append((fullFilePath, size, hashValue, filePath))
    hasDuplicates = hasDuplicates or len(imageList) > 1

  if hasDuplicates:
    # Create target folder if it doesn't exist
    if makeChanges and not os.path.exists(badPath):
      os.mkdir(badPath)
    report.append(f'Found duplicate files in {dirPath}:\n')
  else:
    report.append(f'Found no duplicates in {dirPath}:\n')

  # Move images
  baseFileIdx = 0
  for similarList in images.values():
    # Find the largest image, others will be moved
    max = similarList[0]
    for item in similarList:
      if item[1] > max[1]:
        max = item

    # Find next available file path
    maxExtension = os.path.splitext(max[3])[1].lower() # Max file extension
    while True:
      maxNewName = f'{dirName.lower()}_{baseFileIdx}'.replace(' ', '_')
      maxNewFile =  f'{maxNewName}{maxExtension}'
      maxNewPath = os.path.join(dirPath, maxNewFile)
      baseFileIdx += 1
      if not os.path.exists(maxNewPath) or max[0] == maxNewPath:
        break

    # Rename if that's not already our name
    if makeChanges and max[0] != maxNewPath:
      report.append(f'  Keep:     \'{max[3]}\' -> \'{maxNewFile}\'  ({max[1]} bytes)\n')
      os.rename(max[0], maxNewPath)

    # Move non-max files to badPath
    duplicateIdx = 0
    for item in similarList:
      if item is max:
        continue
      duplicateExtension = os.path.splitext(item[3])[1].lower() # Moved file extension
      # Keep picking the next largest file name until one doesn't exist
      while True:
        duplicateTargetName = f'{maxNewName}_{duplicateIdx}'.replace(' ', '_')
        duplicateTargetFile = f'{duplicateTargetName}{duplicateExtension}'
        duplicateTargetPath = os.path.join(badPath, duplicateTargetFile)
        duplicateIdx += 1
        if not os.path.exists(duplicateTargetPath):
          break
      report += f'    Remove: \'{item[3]}\' -> \'{duplicateTargetFile}\' ({item[1]} bytes)\n'
      if makeChanges:
        os.rename(item[0], duplicateTargetPath)

  # Move other files
  for similarFileList in files.values():
    first = similarFileList[0]
    firstExtension = os.path.splitext(first[2])[1].lower()
    # Find the first available open file path
    while True:
      firstNewName = f'{dirName.lower()}_{baseFileIdx}'.replace(' ', '_')
      firstNewFile = f'{firstNewName}{firstExtension}'
      firstNewPath = os.path.join(dirPath, firstNewFile)
      baseFileIdx += 1
      if not os.path.exists(firstNewPath) or first[0] == firstNewPath:
        break

    # Rename to that file path if we aren't using that name already
    if makeChanges and first[0] != firstNewPath:
      report.append(f'  Keep:     \'{first[2]}\' -> \'{firstNewFile}\'  ({first[1]} bytes)\n')
      os.rename(first[0], firstNewPath)

    # Move other files to badPath
    duplicateIdx = 0
    for item in similarFileList:
      if item is first:
        continue
      duplicateExtension = os.path.splitext(item[2])[1].lower()
      # Keep picking the next largest file name until one doesn't exist
      while True:
        duplicateTargetName = f'{firstNewName}_{duplicateIdx}'.replace(' ', '_')
        duplicateTargetFile = f'{duplicateTargetName}{duplicateExtension}'
        duplicateTargetPath = os.path.join(badPath, duplicateTargetFile)
        duplicateIdx += 1
        if not os.path.exists(duplicateTargetPath):
          break
      report += f'    Remove: \'{item[2]}\' -> \'{duplicateTargetFile}\' ({item[1]} bytes)\n'
      if makeChanges:
        os.rename(item[0], duplicateTargetPath)

  report.append('\n')
  if hasDuplicates:
    print(f'Found and removed duplicates.')

def compareImages():
  # Check args
  if len(sys.argv) < 2:
    print("Please provide path")
    return

  # Calc path
  path = sys.argv[1]
  if path.endswith('\"'):
    path = path[:len(path)-1]

  # Can't work on non-existent path
  if not os.path.exists(path):
    print(f'Path: {path} does not exist')
    return

  # Start recursing
  report = []
  cleanFolderRecursive(path, report)

  # Write report
  if len(report) > 0:
    reportPath = os.path.join(path, reportFile)
    print(f'Writing report to: {reportPath}')
    reportWrite = open(reportPath, 'w')
    reportWrite.write(''.join(report))
    reportWrite.close()

if __name__ == "__main__":
  compareImages()
