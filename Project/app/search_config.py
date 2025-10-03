# -*- coding: utf-8 -*-
"""
Search config (no ENV).
Defines which external domains are allowed for web search results.
Edit ALLOWED_DOMAINS to add/remove sites.
"""

from typing import Set
from urllib.parse import urlparse

ALLOWED_DOMAINS: Set[str] = {
    # Kubernetes / Cloud-native
    "kubernetes.io", "kubernetes.dev", "helm.sh", "kustomize.io",

    # Docker & OCI
    "docker.com", "docs.docker.com",

    # HashiCorp / Terraform
    "hashicorp.com", "developer.hashicorp.com", "terraform.io",

    # Observability
    "prometheus.io", "grafana.com",

    # SRE / Google
    "sre.google", "google.dev", "cloud.google.com",

    # AWS (EKS וכו')
    "aws.amazon.com", "docs.aws.amazon.com",

    # GitHub
    "github.com", "docs.github.com",

    # DevOps books & security
    "itrevolution.com", "owasp.org", "cheatsheetseries.owasp.org",

    # איכותיים ללימוד
    "learnk8s.io", "iximiuz.com",
}

# bias קל לשאילתות (לא חובה)
QUERY_SUFFIX = " devops OR kubernetes OR docker OR terraform OR helm OR sre"


def is_allowed(url: str) -> bool:
    """Return True if URL host is in allow-list (by suffix)."""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    for d in ALLOWED_DOMAINS:
        d = d.lower()
        if host == d or host.endswith("." + d):
            return True
    return False
