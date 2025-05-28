QRCodeSizeArray : list[int] = [(i * 4 + 21) for i in range(40)]

CenterPos = [
    [],
    [6, 18],
    [6, 22],
    [6, 26],
    [6, 30],
    [6, 34],
    [6, 22, 38],
    [6, 24, 42],
    [6, 26, 46],
    [6, 28, 50],
    [6, 30, 54],
    [6, 32, 58],
    [6, 34, 62],
    [6, 26, 46, 66],
    [6, 26, 48, 70],
    [6, 26, 50, 74],
    [6, 30, 54, 78],
    [6, 30, 56, 82],
    [6, 30, 58, 86],
    [6, 34, 62, 90],
    [6, 28, 50, 72, 94],
    [6, 26, 50, 74, 98],
    [6, 30, 54, 78, 102],
    [6, 28, 54, 80, 106],
    [6, 32, 58, 84, 110],
    [6, 30, 58, 86, 114],
    [6, 34, 62, 90, 118],
    [6, 26, 50, 74, 98, 122],
    [6, 30, 54, 78, 102, 126],
    [6, 26, 52, 78, 104, 130],
    [6, 30, 56, 82, 108, 134],
    [6, 34, 60, 86, 112, 138],
    [6, 30, 58, 86, 114, 142],
    [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150],
    [6, 24, 50, 76, 102, 128, 154],
    [6, 28, 54, 80, 106, 132, 158],
    [6, 32, 58, 84, 110, 136, 162],
    [6, 26, 54, 82, 110, 138, 166],
    [6, 30, 58, 86, 114, 142, 170]
]

topLeftPos = []

def checkForOverlap(x1 : int, y1 : int, width1 : int, height1 : int, x2 : int, y2 : int, width2 : int, height2 : int) -> bool:
    if x1 + width1 <= x2 or x2 + width2 <= x1:
        return False
    if y1 + height1 <= y2 or y2 + height2 <= y1:
        return False

    return True
    

for i, versionEntry in enumerate(CenterPos):
    tArray = []
    for x in versionEntry:
        for y in versionEntry:
            topLeftX : int = x - 2
            topLeftY : int = y - 2
            currentVersionSize : int = QRCodeSizeArray[i]

            #Check for overlap
            if not checkForOverlap(0, 0, 7, 7, topLeftX, topLeftY, 5, 5) and not checkForOverlap(currentVersionSize - 7, 0, 7, 7, topLeftX, topLeftY, 5, 5)  and not checkForOverlap(0, currentVersionSize - 7, 7, 7, topLeftX, topLeftY, 5, 5):
                #If no overlap, add to array
                tArray.append((topLeftX * currentVersionSize) + topLeftY)
    topLeftPos.append(tArray)

print(topLeftPos)
