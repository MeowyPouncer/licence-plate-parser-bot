"""
python3 -m nomeroff_net.text_detectors.eu_ua_2004_2015 -f nomeroff_net/text_detectors/eu_ua_2004_2015.py
"""
import torch
from .base.ocr import OCR


class EuUaFrom2004(OCR):
    def __init__(self) -> None:
        OCR.__init__(self)
        self.letters = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "E", "H", "I", "K", "M",
                        "O", "P", "T", "X", "Z"]
        self.max_text_len = 8
        self.max_plate_length = 8
        self.letters_max = len(self.letters)+1
        self.init_label_converter()


eu_ua_2004_2015 = EuUaFrom2004


if __name__ == "__main__":
    ocr = EuUaFrom2004()
    ocr.load()
    y = ocr.predict(torch.rand((1, 3, 50, 200)))
    print(y)
