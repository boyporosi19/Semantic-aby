import json
from rdflib import Graph, Literal, Namespace, URIRef, BNode
from rdflib.namespace import RDF, XSD, RDFS


# Namespace definitions
SCHEMA = Namespace("https://schema.org/")
EX = Namespace("http://example.org/data/")


SCHEMA_TYPE_MAP = {
    "cnn": "NewsArticle",
    "detik": "NewsArticle",
    "kompas": "NewsArticle",
    "wikipedia": "Article",
    "tribun": "NewsArticle",
}


def get_schema_type(source: str) -> str:
    """Get Schema.org type for a source."""
    return SCHEMA_TYPE_MAP.get(source, "Thing")


def _safe_uri(text: str) -> str:
    """Create a URI-safe string from text."""
    return text.replace(" ", "_").replace("/", "-").replace("'", "").replace('"', "")[:80]


def build_rdf_graph(data: list[dict], source: str) -> Graph:
    """
    Convert scraped data to an RDF graph using Schema.org vocabulary.

    Args:
        data: List of scraped items
        source: Source name ('cnn', 'detik', 'kompas', 'wikipedia', 'tribun')

    Returns:
        rdflib.Graph populated with triples
    """
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)

    schema_type = get_schema_type(source)

    for i, item in enumerate(data):
        subject = EX[f"{source}/{i+1}"]
        g.add((subject, RDF.type, SCHEMA[schema_type]))

        if source in ("cnn", "detik", "kompas", "tribun"):
            # All news sources share the same structure
            g.add((subject, SCHEMA.headline, Literal(item.get("title", ""), datatype=XSD.string)))
            url = item.get("url", "")
            if url:
                g.add((subject, SCHEMA.url, URIRef(url)))
            g.add((subject, SCHEMA.articleSection, Literal(item.get("category", ""), datatype=XSD.string)))
            summary = item.get("summary", "")
            if summary:
                g.add((subject, SCHEMA.description, Literal(summary, datatype=XSD.string)))
            date = item.get("date", "")
            if date:
                g.add((subject, SCHEMA.datePublished, Literal(date, datatype=XSD.string)))
            source_url = item.get("source_url", "")
            if source_url:
                g.add((subject, SCHEMA.isPartOf, URIRef(source_url)))

        elif source == "wikipedia":
            g.add((subject, SCHEMA.name, Literal(item.get("title", ""), datatype=XSD.string)))
            g.add((subject, SCHEMA.description, Literal(item.get("summary", ""), datatype=XSD.string)))
            url = item.get("url", "")
            if url:
                g.add((subject, SCHEMA.url, URIRef(url)))
            g.add((subject, SCHEMA.inLanguage, Literal("en", datatype=XSD.string)))
            for cat in item.get("categories", []):
                g.add((subject, SCHEMA.about, Literal(cat, datatype=XSD.string)))

    return g


def to_turtle(graph: Graph) -> str:
    """Serialize an RDF graph to Turtle format."""
    return graph.serialize(format="turtle")


def to_jsonld(data: list[dict], source: str) -> list[dict]:
    """
    Generate JSON-LD representation of scraped data.

    Args:
        data: List of scraped items
        source: Source name

    Returns:
        List of JSON-LD dicts
    """
    schema_type = get_schema_type(source)
    jsonld_items = []

    for item in data:
        jsonld_item = {
            "@context": "https://schema.org",
            "@type": schema_type,
        }

        if source in ("cnn", "detik", "kompas", "tribun"):
            publisher_names = {
                "cnn": "CNN",
                "detik": "detik.com",
                "kompas": "Kompas.com",
                "tribun": "Tribunnews.com",
            }
            jsonld_item.update({
                "headline": item.get("title", ""),
                "url": item.get("url", ""),
                "articleSection": item.get("category", ""),
                "publisher": {
                    "@type": "Organization",
                    "name": publisher_names.get(source, source),
                },
            })
            if item.get("summary"):
                jsonld_item["description"] = item["summary"]
            if item.get("date"):
                jsonld_item["datePublished"] = item["date"]

        elif source == "wikipedia":
            jsonld_item.update({
                "name": item.get("title", ""),
                "description": item.get("summary", ""),
                "url": item.get("url", ""),
                "about": item.get("categories", []),
                "inLanguage": "en",
                "publisher": {
                    "@type": "Organization",
                    "name": "Wikipedia",
                },
            })

        jsonld_items.append(jsonld_item)

    return jsonld_items


def run_sparql(graph: Graph, query: str) -> list[dict]:
    """
    Execute a SPARQL query on the RDF graph.

    Args:
        graph: rdflib.Graph to query
        query: SPARQL query string

    Returns:
        List of result dicts
    """
    results = []
    try:
        qres = graph.query(query)
        for row in qres:
            result = {}
            for var in qres.vars:
                val = getattr(row, str(var), None)
                result[str(var)] = str(val) if val is not None else ""
            results.append(result)
    except Exception as e:
        results = [{"error": str(e)}]

    return results
