from django import forms, template

register = template.Library()


@register.filter
def campo_bootstrap(campo):
    widget = campo.field.widget
    if isinstance(widget, forms.CheckboxInput):
        clase = "form-check-input"
    elif isinstance(widget, forms.Select):
        clase = "custom-select"
    else:
        clase = "form-control"
    attrs = {"class": clase}
    if isinstance(widget, forms.Textarea):
        attrs["rows"] = 4
    return campo.as_widget(attrs=attrs)
