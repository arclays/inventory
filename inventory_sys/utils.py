import csv
from django.http import HttpResponse
from django.http import JsonResponse
from .forms import ExportCSVForm
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def export_csv(request, model, queryset, field_mappings, filename_prefix):
    form = ExportCSVForm(request.GET)
    if form.is_valid():
        try:
            selected_date = form.cleaned_data['order_date']

            # Filter the queryset based on the selected date if applicable
            if 'order_date' in field_mappings:
                queryset = queryset.filter(**{field_mappings['order_date']: selected_date})

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{selected_date.strftime("%Y-%m-%d")}.csv"'

            writer = csv.writer(response)
            headers = [header for header, _ in field_mappings.items()]
            writer.writerow(headers)

            for obj in queryset:
                row = []
                for _, field in field_mappings.items():
                    if callable(field):
                        row.append(field(obj))
                    else:
                        value = getattr(obj, field, 'N/A')
                        if isinstance(value, timezone.datetime):
                            value = value.strftime("%Y-%m-%d")
                        row.append(value)
                writer.writerow(row)

            return response

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return JsonResponse({'error': f'Error exporting CSV: {str(e)}'}, status=500)
    else:
        logger.error(f"Form validation errors: {form.errors}")
        return JsonResponse({'errors': form.errors}, status=400)