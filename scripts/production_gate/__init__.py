"""Production gate predicates.

Every module here answers ONE question about a mesh and returns check dicts
shaped {name, status, value, limit, note}. status is pass | fail | info | skip.
No module claims physical evidence; see specs/README.md.
"""
CHECKER_VERSION = "1.0.0"
