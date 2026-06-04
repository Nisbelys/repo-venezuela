from odoo import fields, models


class ResCountryStateMunicipalityParish(models.Model):
    _name = "res.country.state.municipality.parish"
    _description = "Venezuelan Parish"
    _order = "name"

    name = fields.Char(string="Parroquia", required=True)
    code = fields.Char(string="Código", size=6, required=True)
    municipality_id = fields.Many2one(
        "res.country.state.municipality",
        string="Municipio",
        ondelete="restrict",
    )
