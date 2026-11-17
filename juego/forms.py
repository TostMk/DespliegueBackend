from django import forms

from .models import Habilidad, Personaje


TIPOS_VALIDOS = [
    ("guerrero", "Guerrero"),
    ("maga", "Maga"),
    ("elfo", "Elfo"),
    ("asesino", "Asesino"),
    ("aventurero", "Aventurero"),
]


class PersonajeForm(forms.ModelForm):
    tipo = forms.ChoiceField(choices=TIPOS_VALIDOS, required=False)
    ataque = forms.IntegerField(min_value=0, max_value=100)
    defensa = forms.IntegerField(min_value=0, max_value=100)
    estamina = forms.IntegerField(min_value=0, max_value=100)
    perfil_id = forms.IntegerField(min_value=1, required=False)
    habilidades = forms.JSONField(required=False)

    class Meta:
        model = Personaje
        fields = ["nombre", "tipo", "descripcion", "ataque", "defensa", "estamina"]

    def clean_tipo(self):
        return self.cleaned_data.get("tipo") or "aventurero"

    def clean_habilidades(self):
        ids = self.cleaned_data.get("habilidades") or []
        if not isinstance(ids, list) or any(type(value) is not int or value < 1 for value in ids):
            raise forms.ValidationError("Debe ser una lista de identificadores enteros positivos.")
        if len(ids) != len(set(ids)):
            raise forms.ValidationError("No se permiten habilidades repetidas.")
        return ids


class HabilidadForm(forms.ModelForm):
    class Meta:
        model = Habilidad
        fields = [
            "nombre", "descripcion", "incremento_ataque",
            "incremento_defensa", "incremento_estamina",
        ]


class PersonajeHabilidadForm(forms.Form):
    habilidad_id = forms.IntegerField(min_value=1)
    nivel = forms.IntegerField(min_value=1, required=False, initial=1)

    def clean_nivel(self):
        return self.cleaned_data.get("nivel") or 1
