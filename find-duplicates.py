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
ignoreExtensions = [
  ".xmp",
  ".dll",
]
reportFile = '__report.txt'
images = defaultdict(list)
files = defaultdict(list)

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
def collectDuplicatesRecursive(dirPath):
  print(f'Collecting information {dirPath}...')
  dirName: str = os.path.basename(os.path.dirname(dirPath))

  # Calcualte stats for each file
  filePaths = sorted(os.listdir(dirPath), key=lambda path: natural_keys(path, dirName))
  for filePath in filePaths:
    fullFilePath = os.path.join(dirPath, filePath)

    # Recurse into directory
    if os.path.isdir(fullFilePath):
      collectDuplicatesRecursive(fullFilePath)
      continue

    extension = os.path.splitext(filePath)[1].lower()
    size = os.stat(fullFilePath).st_size

    # Non-image
    if extension not in imageExtensions:
      if extension in ignoreExtensions:
        continue
      files[size].append((fullFilePath, size, filePath))
      continue

    # Image
    try:
      hash = imagehash.average_hash(Image.open(fullFilePath))
    except:
      print(f'Failed to parse image: {fullFilePath}')
      continue
    images[hash].append((fullFilePath, size, hash, filePath))

# Finds similarities and reports duplicates
def reportDuplicates(dirPath):
  # Document
  report = []
  report.append('Similar images:\n')
  for items in images.values():
    if len(items) <= 1:
      continue
    report.append('  Possible similarity:\n')
    for item in items:
      report.append(f'    {item[0]}\n')
  report.append('\n')

  report.append('Simlar files:\n')
  for items in files.values():
    if len(items) <= 1:
      continue
    report.append('  Possible similarity:\n')
    for item in items:
      report.append(f'    {item[0]}\n')
  report.append('\n')

  # Write report
  if len(report) > 0:
    reportPath = os.path.join(dirPath, reportFile)
    print(f'Writing report to: {reportPath}')
    with open(reportPath, 'w', encoding="utf-8") as f:
      f.write(''.join(report))

def findDuplicates():
  # Check args
  if len(sys.argv) < 2:
    print("Please provide path")
    return

  # Calc path
  path = sys.argv[1]

  # Can't work on non-existent path
  if not os.path.exists(path):
    print(f'Path: {path} does not exist')
    return

  print(f'Starting from {path}')
  collectDuplicatesRecursive(path)
  reportDuplicates(path)

if __name__ == "__main__":
  findDuplicates()
