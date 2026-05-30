import os
import unittest

from src.dvsktt_parser.parser import parse_document, split_pages


class TestParserE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate the data file
        cls.data_path = "data/chinh-hoa-18.txt"
        if not os.path.exists(cls.data_path):
            cls.data_path = "../data/chinh-hoa-18.txt"

        with open(cls.data_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cls.pages = split_pages(raw_text)
        cls.doc = parse_document(cls.pages)

    def test_parts_count(self):
        """1. Parts Count: Document.parts must contain exactly 2 parts (Ngoại Kỷ and Bản Kỷ)."""
        self.assertEqual(
            len(self.doc.parts), 2, "Document must contain exactly 2 parts"
        )
        self.assertEqual(self.doc.parts[0].name, "Ngoại Kỷ")
        self.assertEqual(self.doc.parts[1].name, "Bản Kỷ")

    def test_volumes_per_part(self):
        """2. Volumes per Part: Ngoại Kỷ must have exactly 5 Volumes, Bản Kỷ must have exactly 22 Volumes."""
        ngoai_ky = self.doc.parts[0]
        ban_ky = self.doc.parts[1]

        self.assertEqual(
            len(ngoai_ky.volumes), 5, "Ngoại Kỷ must have exactly 5 Volumes"
        )
        self.assertEqual(len(ban_ky.volumes), 22, "Bản Kỷ must have exactly 22 Volumes")

    def test_era_verification(self):
        """3. Era Verification: Assert that the parsed Eras across the document align with the extracted list."""
        eras = []
        for p in self.doc.parts:
            for v in p.volumes:
                for e in v.eras:
                    if e.name not in ["Unknown/Placeholder", ""]:
                        eras.append(e.name)

        # De-duplicate consecutive duplicate names of Eras across volume transitions
        dedup_eras = []
        for name in eras:
            if not dedup_eras or dedup_eras[-1] != name:
                dedup_eras.append(name)

        expected_eras = [
            "Kỷ Hồng Bàng Thị",
            "Kỷ Nhà Thục",
            "Kỷ Nhà Triệu",
            "Kỷ Thuộc Tây Hán",
            "Kỷ Trưng Nữ Vương",
            "Kỷ Thuộc Đông Hán",
            "Kỷ Sĩ Vương",
            "Kỷ Thuộc Ngô, Tấn, Tống, Tề, Lương",
            "Kỷ Nhà Tiền Lý",
            "Kỷ Triệu Việt Vương",
            "Kỷ Hậu Lý",
            "Kỷ Thuộc Tùy Đường",
            "Kỷ Nam Bắc Phân Tranh",
            "Kỷ Nhà Ngô",
            "Kỷ nhà Đinh",
            "Kỷ NHÀ LÊ",
            "Kỷ Nhà Lý",
            "Kỷ Nhà Trần",
            "Kỷ Hậu Trần",
            "Kỷ Nhà Lê",
            "Kỷ Hoàng Triều Nhà Lê",
        ]

        self.assertEqual(
            dedup_eras,
            expected_eras,
            "De-duplicated list of parsed eras does not match the expected list.",
        )


if __name__ == "__main__":
    unittest.main()
