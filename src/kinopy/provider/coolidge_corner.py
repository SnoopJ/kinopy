from ..datamodel import Showing

class CoolidgeCornerProvider:
    @classmethod
    def from_html(cls, film_card: lxml.html.Element):
        link = film_card.xpath(".//film-card__link")
        url = link.attr["href"]
        title = link.text_content()

        return cls(
            date=date,
            title=title,
            url=url,
            showtimes=showtimes,
            excerpt=excerpt,
        )

    @classmethod
