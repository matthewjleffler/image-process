import sys
import os
import imagehash
import re
from functools import cmp_to_key
from PIL import Image

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
hashCutoff = 1

# Sort folder by natural numbers
def atoi(text):
  return int(text) if text.isdigit() else text

def natural_keys(text):
  '''
  alist.sort(key=natural_keys) sorts in human order
  http://nedbatchelder.com/blog/200712/human_sorting.html
  (See Toothy's implementation in the comments)
  '''
  return [ atoi(c) for c in re.split(r'(\d+)', text) ]

# Cleans a folder
def cleanFolderRecursive(dirPath, report):
  # Ignore already cleaned paths
  dirName = os.path.basename(dirPath)
  if dirName == badfolder:
    return

  # Cache vars
  badPath = f'{dirPath}/{badfolder}'
  calculatedImages = []
  calculatedFiles = []
  filePaths = sorted(os.listdir(dirPath), key=natural_keys)

  # Recurse first. Double iterates, but doesn't blow up memory (theoretically)
  for filePath in filePaths:
    fullFilePath = f'{dirPath}/{filePath}'
    if os.path.isdir(fullFilePath):
      cleanFolderRecursive(fullFilePath, report)

  print(f'Checking {dirPath}...')

  # Calcualte stats for each file
  for filePath in filePaths:
    fullFilePath = f'{dirPath}/{filePath}'
    if os.path.isdir(fullFilePath):
      continue
    if filePath == reportFile:
      continue
    duplicateExtension = os.path.splitext(filePath)[1].lower()
    stat = os.stat(fullFilePath)
    if duplicateExtension not in imageExtensions:
      calculatedFiles.append((fullFilePath, stat.st_size, filePath))
      continue
    try:
      hashValue = imagehash.average_hash(Image.open(fullFilePath))
    except:
      print(f'Failed to parse image: {fullFilePath}')
      continue
    calculatedImages.append((fullFilePath, stat.st_size, hashValue, filePath))

  # Loop through and identify similar images
  hasDuplicates = False
  similarImageLists = {}
  for calc in calculatedImages:
    calcHash = calc[2]
    foundSimilar = False
    for similarHash, items in similarImageLists.items():
      delta = calcHash - similarHash
      if delta < hashCutoff:
        foundSimilar = True
        hasDuplicates = True
        items.append(calc)
        break
    if not foundSimilar:
      similarImageLists[calcHash] = [calc]

  # Loop through and identify other similar files
  similarFileLists = {}
  for calc in calculatedFiles:
    calcSize = calc[1]
    foundSimilar = False
    for similarSize, items in similarFileLists.items():
      if similarSize == calcSize:
        foundSimilar = True
        hasDuplicates = True
        items.append(calc)
        break
    if not foundSimilar:
      similarFileLists[calcSize] = [calc]

  if hasDuplicates:
    # Create target folder if it doesn't exist
    if makeChanges and not os.path.exists(badPath):
      os.mkdir(badPath)
    report.append(f'Found duplicate files in {dirPath}:\n')
  else:
    report.append(f'Found no duplicates in {dirPath}:\n')

  baseFileIdx = 0
  # Move images
  for similarImageList in similarImageLists.values():
    # Find the largest image, others will be moved
    max = similarImageList[0]
    for item in similarImageList:
      if item[1] > max[1]:
        max = item

    maxExtension = os.path.splitext(max[3])[1].lower() # Max file extension
    maxNewName = f'{dirName.lower()}_{baseFileIdx}'.replace(' ', '_')
    maxNewPath = f'{dirPath}/{maxNewName}{maxExtension}'
    baseFileIdx += 1

    if makeChanges and max[0] != maxNewPath:
      report.append(f'  Keep:     \'{max[3]}\' -> \'{maxNewName}{maxExtension}\'  ({max[1]} bytes)\n')
      os.rename(max[0], maxNewPath)

    # Move non-max files to badPath
    duplicateIdx = 0
    for item in similarImageList:
      if item is max:
        continue
      duplicateExtension = os.path.splitext(item[3])[1].lower() # Moved file extension
      # Keep picking the next largest file name until one doesn't exist
      while True:
        duplicateTargetName = f'{maxNewName}_{duplicateIdx}'.replace(' ', '_')
        duplicateTargetPath = f'{badPath}/{duplicateTargetName}{duplicateExtension}'
        duplicateIdx += 1
        if not os.path.exists(duplicateTargetPath):
          break
      report += f'    Remove: \'{item[3]}\' -> \'{duplicateTargetName}{duplicateExtension}\' ({item[1]} bytes)\n'
      if makeChanges:
        os.rename(item[0], duplicateTargetPath)

  # Move other files
  for similarFileList in similarFileLists.values():
    first = similarFileList[0]
    firstExtension = os.path.splitext(first[2])[1].lower()
    firstNewName = f'{dirName.lower()}_{baseFileIdx}'.replace(' ', '_')
    firstNewPath = f'{dirPath}/{firstNewName}{firstExtension}'
    baseFileIdx += 1

    if makeChanges and first[0] != firstNewPath:
      report.append(f'  Keep:     \'{first[2]}\' -> \'{firstNewName}{firstExtension}\'  ({first[1]} bytes)\n')
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
        duplicateTargetPath = f'{badPath}/{duplicateTargetName}{duplicateExtension}'
        duplicateIdx += 1
        if not os.path.exists(duplicateTargetPath):
          break
      report += f'    Remove: \'{item[2]}\' -> \'{duplicateTargetName}{duplicateExtension}\' ({item[1]} bytes)\n'
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
  path = f'./{sys.argv[1]}'

  # Can't work on non-existent path
  if not os.path.exists(path):
    print(f'Path: {path} does not exist')
    return

  # Start recursing
  report = []
  cleanFolderRecursive(path, report)

  # Write report
  if len(report) > 0:
    reportPath = f'{path}/{reportFile}'
    print(f'Writing report to: {reportPath}')
    reportWrite = open(reportPath, 'w')
    reportWrite.write(''.join(report))
    reportWrite.close()

if __name__ == "__main__":
  compareImages()
