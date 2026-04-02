import ipaddress
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

DOMAIN_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
)


def validate_domain(value):
    if not DOMAIN_RE.match(value):
        raise ValidationError(_("%(value)s is not a valid domain name."), params={"value": value})


def validate_ip(value):
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError(_("%(value)s is not a valid IP address."), params={"value": value})


def validate_cidr(value):
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError:
        raise ValidationError(_("%(value)s is not a valid CIDR range."), params={"value": value})


def validate_scope_item(item_type, value):
    """Validate a scope item based on its type. Returns cleaned value."""
    validators = {
        "domain": validate_domain,
        "ip": validate_ip,
        "cidr": validate_cidr,
    }
    validator = validators.get(item_type)
    if validator:
        validator(value)
    return value.strip()
