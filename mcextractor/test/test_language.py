import unittest
import py3langid as langid

from .. import content as content


class TestLanguage(unittest.TestCase):

    @staticmethod
    def _fetch_and_validate(url: str, expected_language: str):
        article = content.from_html(url)
        language_info = langid.classify(article['text'])
        assert language_info[0] == expected_language

    def test_india_times(self):
        self._fetch_and_validate(
            "https://www.indiatimes.com/explainers/news/united-nations-climate-report-means-for-india-wet-bulb-temperature-563318.html",
            "en"
        )

    def test_corriere_della_sera(self):
        self._fetch_and_validate(
            "https://www.corriere.it/esteri/22_marzo_07/bombe-ucraine-donbass-soldati-russi-azioni-umanitarie-mondo-parallelo-mosca-176a20ea-9e41-11ec-aa45-e6507f140451.shtml",
            "it"
        )


if __name__ == "__main__":
    unittest.main()
