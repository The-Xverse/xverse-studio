"""Bounded admission of named metric dependencies in one frozen profile set."""
from .evaluator import EvaluationError, validate_definition


def metric_references(expression):
    result = []
    stack = [expression]
    while stack:
        node = stack.pop()
        kind = node['kind']
        if kind == 'metric': result.append(node['evaluationRef'])
        elif kind in {'aggregate','convert'}: stack.append(node['input'])
        elif kind == 'compare': stack.extend((node['left'],node['right']))
        elif kind == 'boolean': stack.extend(node['inputs'])
    return result


def definition_order(definitions, selected_ref=None):
    """Return metric-first order; refuse cycles, absent refs and changed pins.

    The entire admitted profile set is checked even if one assertion is selected.
    Each dependency names an actual version-pinned metric, never an assertion.
    """
    if not isinstance(definitions,list) or len(definitions)>32:
        raise EvaluationError('REFERENCE_LIMIT')
    by_id = {}
    for entry in definitions:
        definition = entry['definition']
        validate_definition(definition)
        identifier = definition['evaluationId']
        if identifier in by_id:
            raise EvaluationError('DEFINITION_ID_AMBIGUOUS')
        by_id[identifier] = entry
    graph = {}
    for identifier,entry in by_id.items():
        refs = metric_references(entry['definition']['expression'])
        graph[identifier] = refs
        for ref in refs:
            dependency = by_id.get(ref['evaluationId'])
            if dependency is None or dependency['definition']['kind']!='metric':
                raise EvaluationError('METRIC_REFERENCE_UNRESOLVED')
    visited, active, order = set(),set(),[]
    def visit(identifier):
        if identifier in active: raise EvaluationError('METRIC_DEPENDENCY_CYCLE')
        if identifier in visited: return
        active.add(identifier)
        for ref in graph[identifier]: visit(ref['evaluationId'])
        active.remove(identifier);visited.add(identifier);order.append(identifier)
    for identifier in by_id: visit(identifier)
    for refs in graph.values():
        for ref in refs:
            dependency=by_id[ref['evaluationId']]
            if ref['version']!=dependency['definition']['version'] or ref['definitionDigest']!=dependency['definitionDigest']:
                raise EvaluationError('METRIC_IDENTITY_MISMATCH')
    if selected_ref is None: return [by_id[key] for key in order]
    if selected_ref not in by_id: raise EvaluationError('DEFINITION_REFERENCE_UNRESOLVED')
    needed=set()
    def require(identifier):
        if identifier in needed:return
        needed.add(identifier)
        for ref in graph[identifier]:require(ref['evaluationId'])
    require(selected_ref)
    return [by_id[key] for key in order if key in needed]
