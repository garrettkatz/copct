"""
Helper functions for dealing with logic programming formulations
"""

def unify(facts, query):
    """
    Simplistic unification of a query with one of several facts.
    Query and each fact should be a tuple.
    "Variables" are indicated by None in the query
    Valid substitutions with literals from the facts are returned
    """
    matches = set()
    for fact in facts:
        if not len(fact) == len(query): continue
        if not all([query[i] in [None, fact[i]] for i in range(len(fact))]): continue
        matches.add(tuple(fact[i] for i in range(len(fact)) if query[i] is None))
    return matches

def single_unify(facts, *queries):
    """
    Return substitution for which one of the queries has precisely one match.
    Useful when required that there is a single unambiguous substitution.
    """
    for query in queries:
        matches = unify(facts, query)
        if len(matches)==1: return matches.pop()
    return tuple(None for q in query if q is None)
