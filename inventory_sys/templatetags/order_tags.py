from django import template
from datetime import datetime

register = template.Library()

@register.filter
def timestamp_prefix(value):
    # Generate a 6-character prefix from the current timestamp
    timestamp = datetime.now().strftime('%H%M%S')  # e.g., 112735 for 11:27:35
    return f"{timestamp}"  # e.g., REC-112735 in the template