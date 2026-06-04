from odoo import fields, models


class ResCountryStateMunicipality(models.Model):
    _name = "res.country.state.municipality"
    _description = "Venezuelan Municipality"
    _order = "name"

    name = fields.Char(string="Municipio", required=True)
    code = fields.Char(string="Código", size=5, required=True)
    state_id = fields.Many2one(
        "res.country.state",
        string="Estado",
        ondelete="restrict",
    )
    parish_ids = fields.One2many(
        "res.country.state.municipality.parish",
        "municipality_id",
        string="Parroquias",
    )
