import cv2
import numpy as np

def is_trading_chart(path: str) -> bool:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False

    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=100,
        minLineLength=100,
        maxLineGap=10
    )
    return lines is not None and len(lines) > 20
