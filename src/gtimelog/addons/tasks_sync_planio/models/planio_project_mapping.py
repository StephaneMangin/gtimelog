import json
import os


class PlanioProjectMapping:
    """Store and auto-register Planio project name mappings."""

    def __init__(self, filename: str):
        self.filename = filename
        self._mappings = self._load()

    def _load(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, encoding='utf-8') as file_obj:
            try:
                data = json.load(file_obj)
            except json.JSONDecodeError:
                return []
        if isinstance(data, list):
            return data
        return []

    def _save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
        with open(self.filename, 'w', encoding='utf-8') as file_obj:
            json.dump(self._mappings, file_obj, indent=4)

    def as_dict(self):
        """Return an in-memory dict representation of current mappings."""
        return {item['planio_name']: item['odoo_name'] for item in self._mappings}

    def ensure_mapping(self, planio_name: str):
        """Return mapped local project name and auto-register unknown names."""
        mappings = self.as_dict()
        if planio_name in mappings:
            return mappings[planio_name]

        odoo_name = f'{planio_name} - A CONVERTIR'
        self._mappings.append({'planio_name': planio_name, 'odoo_name': odoo_name})
        self._save()
        return odoo_name
