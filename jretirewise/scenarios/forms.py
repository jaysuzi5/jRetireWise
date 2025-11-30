"""
Forms for scenarios app.
"""

from django import forms
import json
from .models import RetirementScenario


class ScenarioForm(forms.ModelForm):
    """Form for creating/editing retirement scenarios."""

    parameters_json = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm',
            'placeholder': '{"annual_return": 0.07, "inflation_rate": 0.03}',
        }),
        required=False,
        label='Parameters (JSON)',
        help_text='Optional. Provide JSON to override default parameters.'
    )

    class Meta:
        model = RetirementScenario
        fields = ['name', 'description', 'calculator_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'calculator_type': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate parameters_json from instance if available
        if self.instance and self.instance.pk:
            if isinstance(self.instance.parameters, dict):
                self.fields['parameters_json'].initial = json.dumps(self.instance.parameters, indent=2)
            elif isinstance(self.instance.parameters, str):
                self.fields['parameters_json'].initial = self.instance.parameters

    def clean_parameters_json(self):
        """Validate JSON parameters."""
        params_str = self.cleaned_data.get('parameters_json', '')
        if not params_str:
            return {}

        try:
            return json.loads(params_str)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON: {str(e)}')

    def save(self, commit=True):
        """Save scenario with parsed JSON parameters."""
        instance = super().save(commit=False)
        # Get the parsed parameters from clean_parameters_json
        instance.parameters = self.cleaned_data.get('parameters_json', {})
        if commit:
            instance.save()
        return instance
