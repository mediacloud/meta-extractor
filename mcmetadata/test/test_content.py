import unittest
from typing import Optional
import requests
import lxml.html

from .. import content
from .. import webpages
from ..exceptions import UnableToExtractError


class TestContentParsers(unittest.TestCase):

    URL = "https://web.archive.org/web/https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"

    def setUp(self) -> None:
        self.html_content, self.response = webpages.fetch(self.URL)

    def test_readability(self):
        extractor = content.ReadabilityExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True
        # verify result has no tags as well, since we have to remove them by hand
        text_has_html = lxml.html.fromstring(extractor.content['text']).find('.//*') is not None
        assert text_has_html is False

    def test_trafilatura(self):
        extractor = content.TrafilaturaExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_boilerpipe3(self):
        extractor = content.BoilerPipe3Extractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_goose(self):
        extractor = content.GooseExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_newspaper3k(self):
        extractor = content.Newspaper3kExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True

    def test_rawhtml(self):
        extractor = content.RawHtmlExtractor()
        extractor.extract(self.URL, self.html_content)
        assert extractor.worked() is True


class TestContentFromUrl(unittest.TestCase):

    @staticmethod
    def _fetch_and_validate(url: str, expected_method: Optional[str]):
        html_text, _ = webpages.fetch(url)
        results = content.from_html(url, html_text)
        assert results['url'] == url
        assert len(results['text']) > content.MINIMUM_CONTENT_LENGTH
        assert results['extraction_method'] == expected_method
        return results

    def test_failure_javascript_alert(self):
        url = "https://web.archive.org/web/http://www.prigepp.org/aula-foro-answer.php?idcomentario=301c4&idforo=cc0&idcrso=467&CodigoUni=100190"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Dirigido a Operadores de Justicia de toda la regi??n" in results['text']

    def test_failure_all_javascript(self):
        # this is rendered all by JS, so we can't do anything
        url = "https://web.archive.org/web/https://nbcmontana.com/news/local/2-women-killed-children-hurt-in-western-nebraska-crash"
        try:
            self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
            assert False
        except UnableToExtractError as _:
            assert True

    def test_failing_url(self):
        url = "chrome://newtab/"
        try:
            self._fetch_and_validate(url, None)
            assert False
        except requests.exceptions.InvalidSchema as _:
            # this is an image, so it should return nothing
            assert True

    def test_not_html(self):
        url = "https://web.archive.org/web/https://s3.amazonaws.com/CFSV2/obituaries/photos/4736/635311/5fecf89b1a6fb.jpeg"
        try:
            self._fetch_and_validate(url, None)
        except RuntimeError:
            # this is an image, so it should return nothing
            assert True

    def test_lanacion(self):
        # this one has a "Javascript required" check, which readability-lxml doesn't support but Trifilatura does
        url = 'https://web.archive.org/web/https://www.lanacion.com.ar/seguridad/cordoba-en-marzo-asesinaron-a-tres-mujeres-nid1884942/'
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Por segunda vez esta semana la provincia se ve sacudida" in results['text']

    def test_cnn(self):
        url = "https://web.archive.org/web/https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "McConnell is calling on the education secretary to abandon the idea." in results['text']

    def test_from_url_informe_correintes(self):
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        results = self._fetch_and_validate(url, content.METHOD_READABILITY)
        assert "En este sentido se trabaja en la construcci??n de sendos canales a cielo abierto" in results['text']

    def test_from_url_p??gina_12(self):
        # this one has a "Javascript required" check, which readability-lxml doesn't support but Trifilatura does
        url = "https://web.archive.org/web/https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Por otro lado, fueron realizados en el d??a 84.085 tests" in results['text']

    def test_method_success_stats(self):
        url = "https://web.archive.org/web/https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        self._fetch_and_validate(url, content.METHOD_READABILITY)
        stats = content.method_success_stats
        assert stats[content.METHOD_TRIFILATURA] >= 1
        assert stats[content.METHOD_READABILITY] >= 1
        assert stats[content.METHOD_DRAGNET] == 0

    def test_encoding_fix(self):
        url = "https://web.archive.org/web/https://www.mk.co.kr/news/society/view/2020/07/693939/"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "??" not in results['text']  # this would be there if the encoding isn't being read right
        assert "????????????" in results['text']


if __name__ == "__main__":
    unittest.main()
