"""
Bahoy - Web Scrapers
Este paquete contiene los scrapers para obtener datos de eventos y actividades.

Scrapers disponibles:
- AgendaBaSpider: Scraper para la Agenda de Buenos Aires (turismo.buenosaires.gob.ar)
- AlternativaTeatralSpider: Scraper para Alternativa Teatral (alternativateatral.com)

Uso:
    python app/scrapers/run_scraper.py --spider all
    python app/scrapers/run_scraper.py --spider alternativa_teatral

Para más información ver README.md en este directorio.
"""

__all__ = ['AgendaBaSpider', 'AlternativaTeatralSpider', 'EventItem']
