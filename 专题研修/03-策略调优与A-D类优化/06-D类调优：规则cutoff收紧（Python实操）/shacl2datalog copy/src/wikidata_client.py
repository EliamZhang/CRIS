import requests
import time
from typing import Dict, List, Optional, Any
import logging
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from pathlib import Path

logger = logging.getLogger(__name__)

class WikidataClient:
    """Wikidata SPARQL query client for fetching real data"""
    
    def __init__(self, endpoint_url: str = "https://query.wikidata.org/sparql"):
        self.endpoint_url = endpoint_url
        self.sparql = SPARQLWrapper(endpoint_url)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setRequestMethod("GET")
        self.sparql.setTimeout(60)
        
    def fetch_sample_data(self, entity_type: str, limit: int = 1000) -> Dict[str, Any]:
        """Fetch sample data from Wikidata"""
        logger.info(f"Fetching {limit} {entity_type} entities from Wikidata")
        
        queries = {
            'person': self._get_person_query,
            'university': self._get_university_query,
            'city': self._get_city_query,
            'company': self._get_company_query
        }
        
        if entity_type not in queries:
            logger.error(f"Unsupported entity type: {entity_type}")
            return {}
        
        query = queries[entity_type](limit)
        
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            # Process results
            entities = []
            for binding in results["results"]["bindings"]:
                entity = {}
                for var, value in binding.items():
                    entity[var] = value["value"]
                entities.append(entity)
            
            logger.info(f"Fetched {len(entities)} entities")
            return {
                'entity_type': entity_type,
                'count': len(entities),
                'entities': entities
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch Wikidata: {e}")
            return {}
    
    def _get_person_query(self, limit: int) -> str:
        """SPARQL query for persons"""
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?person ?name ?birthDate ?deathDate ?occupation ?nationality
        WHERE {{
          ?person wdt:P31 wd:Q5 .  # Instance of human
          ?person rdfs:label ?name .
          FILTER(LANG(?name) = "en")
          
          OPTIONAL {{ ?person wdt:P569 ?birthDate }}
          OPTIONAL {{ ?person wdt:P570 ?deathDate }}
          OPTIONAL {{ 
            ?person wdt:P106 ?occ .
            ?occ rdfs:label ?occupation .
            FILTER(LANG(?occupation) = "en")
          }}
          OPTIONAL {{
            ?person wdt:P27 ?nat .
            ?nat rdfs:label ?nationality .
            FILTER(LANG(?nationality) = "en")
          }}
        }}
        LIMIT {limit}
        """
    
    def _get_university_query(self, limit: int) -> str:
        """SPARQL query for universities"""
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?university ?name ?country ?founded ?website ?students
        WHERE {{
          ?university wdt:P31/wdt:P279* wd:Q3918 .  # University
          ?university rdfs:label ?name .
          FILTER(LANG(?name) = "en")
          
          OPTIONAL {{
            ?university wdt:P17 ?c .
            ?c rdfs:label ?country .
            FILTER(LANG(?country) = "en")
          }}
          OPTIONAL {{ ?university wdt:P571 ?founded }}
          OPTIONAL {{ ?university wdt:P856 ?website }}
          OPTIONAL {{ ?university wdt:P2196 ?students }}
        }}
        LIMIT {limit}
        """
    
    def _get_city_query(self, limit: int) -> str:
        """SPARQL query for cities"""
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?city ?name ?country ?population ?area ?founded
        WHERE {{
          ?city wdt:P31/wdt:P279* wd:Q515 .  # City
          ?city rdfs:label ?name .
          FILTER(LANG(?name) = "en")
          
          OPTIONAL {{
            ?city wdt:P17 ?c .
            ?c rdfs:label ?country .
            FILTER(LANG(?country) = "en")
          }}
          OPTIONAL {{ ?city wdt:P1082 ?population }}
          OPTIONAL {{ ?city wdt:P2046 ?area }}
          OPTIONAL {{ ?city wdt:P571 ?founded }}
        }}
        LIMIT {limit}
        """
    
    def _get_company_query(self, limit: int) -> str:
        """SPARQL query for companies"""
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?company ?name ?industry ?founded ?headquarters ?employees
        WHERE {{
          ?company wdt:P31/wdt:P279* wd:Q4830453 .  # Business enterprise
          ?company rdfs:label ?name .
          FILTER(LANG(?name) = "en")
          
          OPTIONAL {{
            ?company wdt:P452 ?ind .
            ?ind rdfs:label ?industry .
            FILTER(LANG(?industry) = "en")
          }}
          OPTIONAL {{ ?company wdt:P571 ?founded }}
          OPTIONAL {{
            ?company wdt:P159 ?hq .
            ?hq rdfs:label ?headquarters .
            FILTER(LANG(?headquarters) = "en")
          }}
          OPTIONAL {{ ?company wdt:P1128 ?employees }}
        }}
        LIMIT {limit}
        """
    
    def convert_to_rdf_turtle(self, data: Dict[str, Any], output_file: str):
        """Convert Wikidata results to RDF Turtle format"""
        from rdflib import Graph, Namespace, Literal, URIRef
        from rdflib.namespace import RDF, RDFS, XSD
        
        g = Graph()
        ex = Namespace("http://example.org/")
        g.bind("ex", ex)
        
        entity_type = data.get('entity_type', 'entity')
        
        for entity in data.get('entities', []):
            # Create entity URI
            entity_id = entity.get(entity_type, entity.get('entity', ''))
            if entity_id:
                entity_uri = URIRef(entity_id)
                
                # Add type
                g.add((entity_uri, RDF.type, ex[entity_type.capitalize()]))
                
                # Add properties
                for prop, value in entity.items():
                    if prop != entity_type and value:
                        # Clean property name
                        prop_name = prop.replace('Label', '')
                        
                        # Add triple
                        if 'Date' in prop or 'founded' in prop:
                            try:
                                date_str = str(value)
                                if 'T' in date_str:
                                    date_str = date_str.split('T')[0]
                                # if date_str.startswith('-'):
                                #     continue
                                g.add((entity_uri, ex[prop_name], Literal(date_str)))
                            except:
                                g.add((entity_uri, ex[prop_name], Literal(value)))
                        elif any(x in prop for x in ['population', 'students', 'employees', 'area']):
                            try:
                                g.add((entity_uri, ex[prop_name], 
                                      Literal(int(float(value)), datatype=XSD.integer)))
                            except:
                                g.add((entity_uri, ex[prop_name], Literal(value)))
                        else:
                            g.add((entity_uri, ex[prop_name], Literal(value)))
        
        # Save to file
        g.serialize(destination=output_file, format='turtle')
        logger.info(f"Saved RDF data to {output_file}")
    
    def convert_to_datalog_facts(self, data: Dict[str, Any], output_dir: str):
        """Convert Wikidata results to Datalog facts"""
        entity_type = data.get('entity_type', 'entity')
        entities = data.get('entities', [])
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Group facts by predicate
        facts_by_predicate = {}
        
        for entity in entities:
            entity_id = entity.get(entity_type, entity.get('entity', ''))
            if not entity_id:
                continue
            
            # Clean entity ID
            entity_id = entity_id.split('/')[-1]
            
            # Add type fact
            type_pred = entity_type.lower()
            if type_pred not in facts_by_predicate:
                facts_by_predicate[type_pred] = []
            facts_by_predicate[type_pred].append(f'"{entity_id}"')
            
            # Add property facts
            for prop, value in entity.items():
                if prop != entity_type and value:
                    # Clean property name
                    prop_name = prop.replace('Label', '').lower()
                    if prop_name == entity_type.lower():
                        prop_name = 'name'
                    
                    if prop_name not in facts_by_predicate:
                        facts_by_predicate[prop_name] = []
                    
                    # Clean value
                    value = str(value).replace('"', '\\"').replace('\n', ' ')
                    facts_by_predicate[prop_name].append(f'"{entity_id}"\t"{value}"')
        
        # Write facts to files
        for predicate, facts in facts_by_predicate.items():
            fact_file = Path(output_dir) / f"{predicate}.facts"
            with open(fact_file, 'w', encoding='utf-8') as f:
                for fact in facts:
                    f.write(fact + '\n')
            logger.info(f"Wrote {len(facts)} facts to {fact_file}")

