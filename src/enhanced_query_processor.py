import re
from typing import Tuple, Dict, Any
from src.graph_rag_query_processor import GraphRAGQueryProcessor, safe_split_key

# EnhancedGraphRAGQueryProcessor without debug statements
class EnhancedGraphRAGQueryProcessor(GraphRAGQueryProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Comprehensive patterns for definitions
        self.intent_patterns['definition_inquiry'] = {
            'patterns': [
                r'(?i)what\s+(?:is|are)\s+([\w\s-]+?)(?:\?|$)',
                r'(?i)what\s+does\s+([\w\s-]+?)\s+mean(?:\?|$)',
                r'(?i)define\s+([\w\s-]+?)(?:\?|$)',
                r'(?i)meaning\s+of\s+([\w\s-]+?)(?:\?|$)',
                r'(?i)definition\s+of\s+([\w\s-]+?)(?:\?|$)'
            ],
        }
        self.intent_embeddings = self._compute_intent_embeddings()
        # Ensure knowledge_graph exists
        if not hasattr(self, 'knowledge_graph') or self.knowledge_graph is None:
            import networkx as nx
            self.knowledge_graph = nx.MultiDiGraph()

    def extract_parameters(self, query_text: str, intent: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        params = super().extract_parameters(query_text, intent, user_context)
        if intent == 'definition_inquiry':
            term = None
            for pattern in self.intent_patterns[intent]['patterns']:
                m = re.search(pattern, query_text)
                if m and m.groups():
                    term = m.group(1).strip().lower()
                    break
            if not term:
                cleaned_query = re.sub(r'(?i)what\s+(?:is|are|does)|mean[s]?|\?|definition|of|the', '', query_text)
                term = cleaned_query.strip().lower()
            params['term'] = term
            params['original_term'] = term
        return params

    def build_graph_query(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if intent == 'definition_inquiry':
            term = params.get('term', '')
            if not term:
                return {
                    'start_nodes': [{'label': 'Definition', 'alias': 'd'}],
                    'return_properties': [
                        {'node': 'd', 'property': 'term'},
                        {'node': 'd', 'property': 'meaning'}
                    ]
                }
            params['original_term'] = term
            return {
                'start_nodes': [{'label': 'Definition', 'alias': 'd'}],
                'return_properties': [
                    {'node': 'd', 'property': 'term'},
                    {'node': 'd', 'property': 'meaning'}
                ],
                'filters': [{
                    'operator': 'OR',
                    'conditions': [
                        {'node': 'd', 'property': 'term', 'operator': '=', 'value': term},
                        {'node': 'd', 'property': 'term', 'operator': '=', 'value': term.lower()},
                        {'node': 'd', 'property': 'term', 'operator': 'CONTAINS', 'value': term},
                        {'node': 'd', 'property': 'aliases', 'operator': 'CONTAINS', 'value': term}
                    ]
                }]
            }
        return super().build_graph_query(intent, params)

    def _prepare_template_data(self, intent: str, query_results: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        if intent == 'definition_inquiry':
            data: Dict[str, Any] = {}
            props = query_results.get('properties', {})
            requested_term = params.get('term', '').lower()
            if params.get('term'):
                data['term'] = params['term']
            definition_found = False
            for k, vals in props.items():
                if not vals:
                    continue
                alias, prop = safe_split_key(k)
                if prop == 'term':
                    found_term = vals[0]
                    found_term_lower = found_term.lower()
                    if found_term_lower == requested_term or requested_term in found_term_lower or found_term_lower in requested_term:
                        data['term'] = found_term
                        definition_found = True
                elif prop == 'meaning' and definition_found:
                    data['meaning'] = vals[0]
            if not definition_found or 'meaning' not in data:
                term = requested_term
                result_found = False
                if hasattr(self, 'knowledge_graph') and self.knowledge_graph is not None:
                    matched_nodes = []
                    try:
                        for node_id, node_data in self.knowledge_graph.nodes(data=True):
                            node_props = node_data.get('properties', {})
                            node_term = node_props.get('term', node_props.get('name', '')).lower()
                            similarity = self._calculate_term_similarity(term, node_term)
                            if similarity > 0.5:
                                matched_nodes.append((node_id, node_data, similarity))
                        if matched_nodes:
                            matched_nodes.sort(key=lambda x: x[2], reverse=True)
                            best_match = matched_nodes[0]
                            node_props = best_match[1].get('properties', {})
                            data['term'] = node_props.get('term', node_props.get('name', ''))
                            data['meaning'] = node_props.get('meaning', node_props.get('description', ''))
                            result_found = True
                    except Exception:
                        pass
                if not result_found:
                    data['term'] = requested_term
                    data['meaning'] = f"No definition found for '{requested_term}'"
            return data
        return super()._prepare_template_data(intent, query_results, params)

    def _calculate_term_similarity(self, term1: str, term2: str) -> float:
        if term1 in term2 or term2 in term1:
            return 0.8
        words1 = set(term1.split())
        words2 = set(term2.split())
        if words1 and words2:
            overlap = len(words1.intersection(words2))
            total = len(words1.union(words2))
            if total > 0:
                return overlap / total
        return 0.0
